#!/bin/bash
set -e

success=false
trap check_finish EXIT
check_finish() {
  if [ $success = true ]; then
    echo '>>>' success
  else
    echo "FAILED"
  fi
}

echo ">>> Verify terraform installed"
terraform version

echo ">>> demo_tf is the terraform configuration"
(
  cd demo_tf
  terraform init
  terraform apply -auto-approve
)

echo ">>> create code_engine_config.sh"
rm -f code_engine_config.sh
for variable in BASENAME RESOURCE_GROUP_NAME COS_CRN COS_GUID COS_BUCKET COS_ENDPOINT COS_BUCKET_REGION LOGDNA_REGION LOGDNA_NAME LOGDNA_INGESTION_KEY; do 
  echo $variable=$(terraform output -state demo_tf/terraform.tfstate $variable) >> code_engine_config.sh
done
cat code_engine_config.sh

success=true