#!/bin/bash
set -e
( cd tf; terraform init; terraform apply -auto-approve )
vpc_id=$(terraform output -state=tf/terraform.tfstate vpc_id)
ibmcloud is flow-log-create --bucket $COS_BUCKET_NAME --target $vpc_id
