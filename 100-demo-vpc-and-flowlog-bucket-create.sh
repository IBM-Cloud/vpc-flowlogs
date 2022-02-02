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
terraform output -raw -state demo_tf/terraform.tfstate code_engine_config > code_engine_config.sh
success=true