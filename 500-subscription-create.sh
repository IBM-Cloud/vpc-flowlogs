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
ce_subscription
success=true