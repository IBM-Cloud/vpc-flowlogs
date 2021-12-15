#!/bin/bash
set -e

if [ x = x$TF_VAR_ibmcloud_api_key ]; then
  echo ">>> environment variable TF_VAR_ibmcloud_api_key not initialized"
  exit 1
fi

rm -f python.ini code_engine_config.sh
cd demo_tf
terraform init
terraform destroy -auto-approve

