#!/bin/bash
set -e

echo ">>> Verify the VPC ssh key exists..."
ibmcloud is keys --json | jq -e '.[] | select(.name=="'$TF_VAR_ssh_key_name'")' > /dev/null

echo ">>> Verify terraform installed"
terraform version
