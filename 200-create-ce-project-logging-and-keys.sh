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
source code_engine_more_config.sh

### 
cos_global_variables(){
  COS_CRN=$(echo $COS_BUCKET_CRN | sed 's/\(.*\):[^:]*:[^:]*:[^:]*/\1/')::
  COS_GUID=$(echo $COS_BUCKET_CRN | sed 's/.*:\([^:]*\):[^:]*:[^:]*/\1/')
  bucket=$(echo $COS_BUCKET_CRN | sed 's/.*:[^:]*:\([^:]*\):[^:]*/\1/')
  COS_BUCKET=$(echo $COS_BUCKET_CRN | sed 's/.*:[^:]*:[^:]*:\([^:]*\)/\1/')
  if [ x$bucket != xbucket ]; then
    echo "*** error parsing the COS_BUCKET_CRN:$COS_BUCKET_CRN"
    exit 1
  fi
}

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
      --target-service-instance-id $COS_GUID
    existing_policies=$(ibmcloud iam authorization-policies --output JSON)
  fi
  if ! authorization_policy_exists; then
    echo '***' authorization policy does not exist
    exit 1
  fi

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

  existing_service_id_policies=$(ibmcloud iam service-policies $service_id --output json)
  if writer_service_policy_exists; then
    echo '>>> writer policy for bucket exists'
  else
    echo '>>> create writer policy for bucket'
    ibmcloud iam service-policy-create $service_id --roles Writer --service-name cloud-object-storage  --service-instance $COS_GUID --resource-type bucket --resource $COS_BUCKET
  fi
}

### create the apikey for the service id 
apikey_for_cos_access() {
  echo ">>> Check for existing service api key"
  if result=$(ibmcloud iam service-api-key $service_api_key_name $service_id); then
    echo ">>> existing service api key exists"
    echo "$result"
    echo ">>> delete existing service api key"
    ibmcloud iam service-api-key-delete $service_api_key_name $service_id --force
  fi
  echo ">>> Create new service api key"
  service_api_key_json=$(ibmcloud iam service-api-key-create $service_api_key_name $service_id --description "$ce_project_name COS READ WRITE" --output json)
  apikey=$(jq -r .apikey <<< "$service_api_key_json")
}

### ce_secret - create the code engine secret
ibmcloud_ce_secret() {
  local command=$1
  ibmcloud ce secret $command -n $secret_for_apikey_name --from-literal APIKEY="$apikey" --from-literal LOGDNA_INGESTION_KEY="$LOGDNA_INGESTION_KEY"
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
}

## ce_configmap
ibmcloud_ce_configmap() {
  local command=$1
  ibmcloud ce configmap $command \
    --from-literal COS_ENDPOINT=$COS_ENDPOINT \
    --from-literal LOGDNA_REGION=$LOGDNA_REGION \
    --from-literal COS_CRN="$COS_CRN" \
    --from-literal COS_BUCKET="$COS_BUCKET" \
    --from-literal KEY_FIRST_LOGGED="$key_first_logged" \
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

## 
check_platform_logging_instance() {
  echo '>>> checking for logging instance in region'
  instances=$(ibmcloud logging service-instances --all-resource-groups --output json)
  if name=$(jq -er '.[]|select(.service_name=="logdna") | select(.doc.parameters.default_receiver==true) | .name'  <<< "$instances"); then
    echo platform logging instance in $CE_REGION is $name
  else
    echo "*** there is no platform logging instance in region $CE_REGION.  It will not be possible to debug the code engine job using logs"
    echo ">>> see https://cloud.ibm.com/docs/log-analysis?topic=log-analysis-config_svc_logs"
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

usage() {
  echo 
  echo USAGE:
  echo "$0 [basic|job|subscription]"
  echo "basic - code engine project, ConfigMap, secret, authorizations, iam apikey, ..."
  echo "job - code engine job create or update"
  echo "subscription - subscription from bucket to job"
  echo "no options means do them all"
  exit 1
}

################
basics=false
job=false
subscription=false
case $# in
0)
  basics=true
  job=true
  subscription=true
  ;;
1)
  case $1 in
  basics)
    basics=true
    ;;
  job)
    job=true
    ;;
  subscription)
    subscription=true
    ;;
  *)
    usage
    ;;
  esac
  ;;
*)
  usage
  ;;
esac

# liberal use of global variables throughout
echo ">>> Targeting region for code engine $CE_REGION and resource group $RESOURCE_GROUP_NAME"
ibmcloud target -r $CE_REGION -g $RESOURCE_GROUP_NAME

if [ $basics = true ]; then
  cos_global_variables
  ce_project
  authorization_policy_for_cos_ce_notifications
  echo ">>> create a apikey used by the code engine job that can read/write the COS bucket"
  service_id_for_cos_access
  apikey_for_cos_access
  ce_secret
  ce_configmap
fi
if [ $job = true ]; then
   ce_job
fi
if [ $subscription = true ]; then
  ce_subscription
fi
if [ $job = true ]; then
  check_platform_logging_instance
fi

################

success=true
