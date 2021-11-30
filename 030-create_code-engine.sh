#!/bin/bash
set -e

## Create the resources for a code engine, ce, processor of the COS bucket:
# ce project and job
# 

success=false
trap check_finish EXIT
check_finish() {
  if [ $success = true ]; then
    echo '>>>' success
  else
    echo "FAILED"
  fi
}

if ! [ -e code_engine_config.sh ]; then
  echo '***' initialize code_engine_config.sh - template_code_engine_config.sh has documentation
  exit 1
fi
source code_engine_config.sh
source code_engine_constants.sh

### ce project
ce_project() {
  if ! ibmcloud ce project select --name $ce_project_name > /dev/null 2>&1; then
    echo ">>> create project $ce_project_name"
    ibmcloud ce project create --name $ce_project_name
    ibmcloud ce project select --name $ce_project_name
  else
    echo ">>> project $ce_project_name exists and is selected"
  fi
  project_guid=$(ibmcloud ce project current --output json | jq  -r .guid)
}

### authorization_policy_for_cos_ce_notifications policies allowing code engine project to ask COS
# to notify it when objects are written to a bucket
authorization_policy_exists() {
  jq -e '.[] |
    select(.subjects[].attributes[].value=="codeengine") |
    select(.subjects[].attributes[].value=="'$project_guid'") |
    select(.roles[].display_name=="Notifications Manager") |
    select(.resources[].attributes[].value=="cloud-object-storage") |
    select(.resources[].attributes[].value=="'$COS_GUID'")' <<< "$existing_policies" > /dev/null
}
authorization_policy_for_cos_ce_notifications() {
  existing_policies=$(ibmcloud iam authorization-policies --output JSON)
  if authorization_policy_exists; then
    echo ">>> Notification role between code engine and COS already exists"
  else
    echo ">>> create notification role between code engine and COS already exists"
    ibmcloud iam authorization-policy-create codeengine cloud-object-storage "Notifications Manager" \
      --source-service-instance-name $ce_project_name \
      --target-service-instance-id $COS_CRN
    sleep 5
  fi
  if ! authorization_policy_exists; then
    echo '***' authorization policy does not exist
    exit 1
  fi

  # create service id and read/writer policy for the cos bucket
  if result=$(ibmcloud iam service-id $service_id_name --output json 2>&1); then
    echo ">>> iam service-id exists $service_id_name"
    echo "$result"
  else
    echo ">>> iam service-id-create $service_id_name"
    service_id_json_one=$(ibmcloud iam service-id-create $service_id_name --output json)
  fi
  service_id_json=$(ibmcloud iam service-id $service_id_name --output json)
  service_id=$(jq -r '.[0].id' <<< "$service_id_json")
}

### service_id_for_cos_access
writer_service_policy_exists() {
  jq -e '.[] |
    select(.roles[].role_id=="crn:v1:bluemix:public:iam::::serviceRole:Writer") |
    select(.resources[].attributes[].value=="cloud-object-storage") |
    select(.resources[].attributes[].value=="'$COS_GUID'") |
    select(.resources[].attributes[].value=="'$COS_BUCKET'")' <<< "$existing_service_id_policies" > /dev/null
}
service_id_for_cos_access() {
  existing_service_id_policies=$(ibmcloud iam service-policies $service_id --output json)
  if writer_service_policy_exists; then
    echo '>>> writer policy for bucket exists'
  else
    echo '>>> create writer policy for bucket'
    ibmcloud iam service-policy-create $service_id --roles Writer --service-name cloud-object-storage  --service-instance $COS_GUID --resource-type bucket --resource $COS_BUCKET
  fi
}

### create the apikey for the service id and store it in a file
apikey_for_cos_access() {
  if [ -e $apikey_file_for_service_id ]; then
    echo ">>> using the previously fetched service api key file"
  else
    echo ">>> get the apikey store in file $apikey_file_for_service_id"
    ibmcloud iam service-api-key-create $service_api_key_name $service_id --description "$ce_project_name COS READ WRITE" --file $apikey_file_for_service_id --output json
  fi
  echo ">>> using the fetched API key.  It is in the file $apikey_file_for_service_id"
  apikey=$(jq -r .apikey $apikey_file_for_service_id)
}

### logdna service instance
logdna_service_instance() {
  if result=$(ibmcloud resource service-instance $logdna_service_name 2>&1); then
    echo ">>> LogDNA service $logdna_service_name already exists"
    echo "$result"
  else
    echo ">>> Creating LogDNA Service..."
    ibmcloud resource service-instance-create $logdna_service_name \
      logdna "$LOGDNA_SERVICE_PLAN" $LOGDNA_REGION || exit 1
  fi
  LOGDNA_INSTANCE_CRN=$(ibmcloud resource service-instance --output JSON $logdna_service_name | jq -r .[0].id)
  echo ">>> LogDNA ID is $LOGDNA_INSTANCE_CRN"
}

## create service key for logdna and extract the ingestion key
logdna_service_key_and_ingestion_key() {
  if logdna_service_key_json=$(ibmcloud resource service-key $logdna_service_name-for-code-engine --output json 2>/dev/null) ; then
    echo "Service key already exists"
  else
    logdna_service_key_json_one=$(ibmcloud resource service-key-create $logdna_service_name-for-code-engine Manager --instance-id $LOGDNA_INSTANCE_CRN --output json)
    logdna_service_key_json=$(ibmcloud resource service-key $logdna_service_name-for-code-engine --output json)
  fi
  # get the ingestion key to access to LogDNA service
  logdna_api_key=$(jq -r '.[0].credentials.apikey' <<< "$logdna_service_key_json")
  logdna_ingestion_key=$(jq -r '.[0].credentials.ingestion_key' <<< "$logdna_service_key_json")
  #TODO Valid roles are Manager, Reader, Standard Member. 
}

### ce_secret - create the code engine secret
ibmcloud_ce_secret() {
  local command=$1
  ibmcloud ce secret $command -n $secret_for_apikey_name --from-literal APIKEY="$apikey" --from-literal LOGDNA_INGESTION_KEY="$logdna_ingestion_key"
}
ce_secret() {
  if result=$(ibmcloud_ce_secret update 2>&1); then
    echo ">>> code engine secret updated"
    echo "$result"
  else
    echo ">>> create code engine secret"
    ibmcloud_ce_secret create
  fi
  echo ">>> verify code engine secret"
  ibmcloud ce secret get  -n $secret_for_apikey_name
}

## ce_configmap
ibmcloud_ce_configmap() {
  local command=$1
  ibmcloud ce configmap $command \
    --from-literal REGION=$REGION \
    --from-literal COS_CRN="$COS_CRN" \
    --from-literal COS_BUCKET="$COS_BUCKET" \
    --from-literal KEY_FIRST_LOGGED="$COS_CRN" \
    --name $ce_configmap_name
}
ce_configmap() {
  if result=$(ibmcloud_ce_configmap update 2>&1); then
    echo ">>> updated config map for code engine job"
    echo "$result"
  else
    echo ">>> create config map for code engine job"
    ibmcloud_ce_configmap create
  fi
  ibmcloud ce configmap get --name $ce_configmap_name; # test
}

## ce_job
ibmcloud_ce_job() {
  local command=$1
  ibmcloud ce job $command --name $ce_job_name --image $DOCKER_IMAGE --env-from-secret $secret_for_apikey_name --env-from-configmap $ce_configmap_name > /dev/null
}
ce_job() {
  if result=$(ibmcloud_ce_job update 2>&1); then
    echo '>>> updated code engine job'
    echo "$result"
  else
    ibmcloud_ce_job create
  fi
}

### ce_subscription
ibmcloud_ce_subscription(){
  command=$1
  bucket_cos_bucket="$2"
  ibmcloud ce subscription cos $command --name $ce_subscription_name --destination-type job --destination $ce_job_name $bucket_cos_bucket --event-type all
}
ce_subscription() {
  if result=$(ibmcloud_ce_subscription update 2>&1); then
    echo '>>> updated code engine subscription'
    echo "$result"
  else  
    echo '>>> create code engine subscription'
    ibmcloud_ce_subscription create "--bucket $COS_BUCKET"
  fi
}

################
# liberal use of global variables throughout
echo ">>> Targeting region $REGION and resource group $RESOURCE_GROUP_NAME"
ibmcloud target -r $REGION -g $RESOURCE_GROUP_NAME

ce_project
authorization_policy_for_cos_ce_notifications
echo ">>> create a apikey used by the code engine job that can read/write the COS bucket"
service_id_for_cos_access
apikey_for_cos_access
logdna_service_instance
echo '>>> create a logdna service key and from it get the ingestion key for code engine job to write to logdna'
logdna_service_key_and_ingestion_key
ce_secret
ce_configmap
ce_job
ce_subscription
################

success=true