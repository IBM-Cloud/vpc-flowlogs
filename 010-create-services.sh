#!/bin/bash
set -e

if ibmcloud resource service-instance $COS_SERVICE_NAME > /dev/null 2>&1; then
  echo "Cloud Object Storage service $COS_SERVICE_NAME already exists"
else
  echo "Creating Cloud Object Storage Service..."
  ibmcloud resource service-instance-create $COS_SERVICE_NAME \
    cloud-object-storage "$COS_SERVICE_PLAN" global || exit 1
fi

COS_INSTANCE_CRN=$(ibmcloud resource service-instance --output JSON $COS_SERVICE_NAME | jq -r '.[0].id')
echo "Cloud Object Storage CRN is $COS_INSTANCE_CRN"

if ibmcloud resource service-key $COS_SERVICE_NAME-for-functions > /dev/null 2>&1; then
  echo "Service key already exists"
else
  ibmcloud resource service-key-create $COS_SERVICE_NAME-for-functions Writer --instance-id $COS_INSTANCE_CRN
fi

ibmcloud cos config crn --crn $COS_INSTANCE_CRN --force

# Create the bucket
if ibmcloud cos head-bucket --bucket $COS_BUCKET_NAME --region $COS_REGION > /dev/null 2>&1; then
  echo "Bucket already exists"
else
  echo "Creating storage bucket $COS_BUCKET_NAME"
  ibmcloud cos create-bucket \
    --bucket $COS_BUCKET_NAME \
    --ibm-service-instance-id $COS_INSTANCE_CRN \
    --region $COS_REGION
fi


if ibmcloud resource service-instance $LOGDNA_SERVICE_NAME > /dev/null 2>&1; then
  echo "LogDNA service $LOGDNA_SERVICE_NAME already exists"
else
  echo "Creating LogDNA Service..."
  ibmcloud resource service-instance-create $LOGDNA_SERVICE_NAME \
    logdna "$LOGDNA_SERVICE_PLAN" $LOGDNA_REGION || exit 1
fi
LOGDNA_INSTANCE_CRN=$(ibmcloud resource service-instance --output JSON $LOGDNA_SERVICE_NAME | jq -r .[0].id)
echo "LogDNA ID is $LOGDNA_INSTANCE_CRN"

if ibmcloud resource service-key $LOGDNA_SERVICE_NAME-for-functions > /dev/null 2>&1; then
  echo "Service key already exists"
else
  ibmcloud resource service-key-create $LOGDNA_SERVICE_NAME-for-functions Manager --instance-id $LOGDNA_INSTANCE_CRN
fi
#TODO Valid roles are Manager, Reader, Standard Member. 


