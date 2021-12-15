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

source code_engine_config.sh
source code_engine_more_config.sh

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
  instances=$(ibmcloud logging service-instances --output json)
  if name=$(jq -er '.[]|select(.service_name=="logdna") | select(.doc.parameters.default_receiver==true) | .name'  <<< "$instances"); then
    echo platform logging instance in $CE_REGION is $name
  else
    echo "*** there is no platform logging instance in region $CE_REGION.  It will not be possible to debug the code engine job using logs"
    echo ">>> see https://cloud.ibm.com/docs/log-analysis?topic=log-analysis-config_svc_logs"
  fi

}

################
ibmcloud target -r $CE_REGION -g $RESOURCE_GROUP_NAME
#ce_job
check_platform_logging_instance
success=true