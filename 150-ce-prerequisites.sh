#!/bin/bash
success=false
trap check_finish EXIT
check_finish() {
  if [ $success = true ]; then
    echo '>>>' success
  else
    echo "FAILED"
  fi
}

set -e

source code_engine_config.sh
source code_engine_more_config.sh
source shared.sh

echo ">>> ibmcloud cli"
ibmcloud version

echo ">>> ibmcloud target"
ibmcloud target -r $LOGDNA_REGION -g $RESOURCE_GROUP_NAME

echo ">>> ibmcloud ce plugin"
if ! output=$(ibmcloud ce); then
  echo $output
  exit 1
fi

echo ">>> ibmcloud logging plugin"
if ! output=$(ibmcloud logging); then
  echo $output
  exit 1
fi

echo ">>> Is jq (https://stedolan.github.io/jq/) installed?"
jq -V

echo ">>> Ensuring flowlogs are installed and working"
if flow_logs_json=$(ibmcloud is flow-logs --output json); then
  echo "flow logs are available"
else
  echo "Make sure flow logs are available in your account."
  exit 1
fi

cos_global_variables

echo ">>> Ensuring that there is a flowlog for the configured bucket"
if ! flow_log_json=$(jq -e -r '.[]|select(.storage_bucket.name=="'$COS_BUCKET'")' <<< "$flow_logs_json"); then
  echo flow log for bucket $COS_BUCKET not found
  exit 1
fi

echo ">>> Looking for plugin updates"""
plugins_that_need_update=$(ibmcloud plugin list --output json | jq '[.[]|select(.Status=="Update Available")]|length')
if [ $plugins_that_need_update -gt 0 ]; then
  ibmcloud plugin list
  echo
  echo "WARNING $plugins_that_need_update plugins need updating.  Update them by executing:"
  echo ibmcloud plugin update --all
fi

success=true
