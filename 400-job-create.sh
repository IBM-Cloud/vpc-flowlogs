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

################
ce_job
success=true