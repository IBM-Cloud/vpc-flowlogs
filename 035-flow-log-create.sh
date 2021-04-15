#!/bin/bash
set -e
source ./shared.sh

echo ">>> create flow log collector for vpc $vpc_id"
ibmcloud is target --gen 2
ibmcloud is flow-log-create --bucket $COS_BUCKET_NAME --target $(cat vpcid.txt) --name $PREFIX-flowlog
