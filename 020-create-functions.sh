#!/bin/bash
set -e

skip=false
if [ $# == 1 ] && [ $1 == skip ]; then
  skip=true
fi

echo '>>> cloud function namespace'
NAMESPACE=$PREFIX-actions
if ibmcloud fn property set --namespace $NAMESPACE > /dev/null 2>&1; then
  echo "Namespace $NAMESPACE already exists."
else
  ibmcloud fn namespace create $NAMESPACE
  ibmcloud fn property set --namespace $NAMESPACE
fi

NAMESPACE_INSTANCE_ID=$(ibmcloud fn namespace get $NAMESPACE --properties | grep ID | awk '{print $2}')
echo "Namespace Instance ID is $NAMESPACE_INSTANCE_ID"

COS_GUID=$(ibmcloud resource service-instance --output JSON $COS_SERVICE_NAME | jq -r .[0].guid)
echo "COS GUID is $COS_GUID"

echo '>>> iam authorization policy from function namspace to COS'
EXISTING_POLICIES=$(ibmcloud iam authorization-policies --output JSON)
if echo "$EXISTING_POLICIES" | \
  jq -e '.[] |
  select(.subjects[].attributes[].value=="functions") |
  select(.subjects[].attributes[].value=="'$NAMESPACE_INSTANCE_ID'") |
  select(.roles[].display_name=="Notifications Manager") |
  select(.resources[].attributes[].value=="cloud-object-storage") |
  select(.resources[].attributes[].value=="'$COS_GUID'")' > /dev/null; then
  echo "Reader policy between Functions and COS already exists"
else
  ibmcloud iam authorization-policy-create functions \
    cloud-object-storage "Notifications Manager" \
    --source-service-instance-name $NAMESPACE \
    --target-service-instance-id $COS_GUID
fi

# get the key to access COS service
COS_SERVICE_KEY=$(ibmcloud resource service-key $COS_SERVICE_NAME-for-functions --output json)
COS_API_KEY=$(echo $COS_SERVICE_KEY | jq -r '.[0].credentials.apikey')
COS_INSTANCE_ID=$(echo $COS_SERVICE_KEY | jq -r '.[0].credentials.resource_instance_id')

# get the key to access to LogDNA service
LOGDNA_SERVICE_KEY=$(ibmcloud resource service-key $LOGDNA_SERVICE_NAME-for-functions --output json)
LOGDNA_API_KEY=$(echo $LOGDNA_SERVICE_KEY | jq -r '.[0].credentials.apikey')
LOGDNA_INGESTION_KEY=$(echo $LOGDNA_SERVICE_KEY | jq -r '.[0].credentials.ingestion_key')

# one trigger, create-trigger, to handle new flowlog objects in COS
echo '>>> function trigger from COS'
if ibmcloud fn trigger get create-trigger > /dev/null 2>&1; then
  echo "Trigger on create already exists"
else
  ibmcloud fn trigger create create-trigger --feed /whisk.system/cos/changes \
    --param bucket $COS_BUCKET_NAME \
    --param event_types create
fi

if [ $skip == false ]; then
  # create a zip of the virtualenv/ and of __main__.py
  echo '>>> create zip of python action'
  ( cd actions; ./zipit.sh )

  # the fn update comand will create the action if it does not exist or update if it does exist
  echo '>>> update action with python zip'
  ibmcloud fn action update log --param cosApiKey $COS_API_KEY --param cosInstanceId $COS_INSTANCE_ID --param logdnaKey $LOGDNA_INGESTION_KEY --param logdnaIngestionEndpoint $LOGDNA_INGESTION_ENDPOINT actions/log.zip --kind python:3.7

  # connect the trigger to the action via a rule
  echo '>>> rule from trigger to action'
  if ibmcloud fn rule get create-rule > /dev/null 2>&1; then
    echo "Rule already exists"
  else
    ibmcloud fn rule create create-rule create-trigger log
  fi
fi
(
  cd actions
  cat > local.env <<EOF
export COS_BUCKET_NAME=$COS_BUCKET_NAME
export COS_API_KEY=$COS_API_KEY
export COS_INSTANCE_ID=$COS_INSTANCE_ID
export LOGDNAKEY=$LOGDNA_API_KEY
export LOGDNA_INGESTION_ENDPOINT=$LOGDNA_INGESTION_ENDPOINT
export COSENDPOINT=s3.$REGION.cloud-object-storage.appdomain.cloud
EOF
)
