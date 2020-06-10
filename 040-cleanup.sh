#!/bin/bash
set -e

# vpc and flow logs
flow_log_id=$(ibmcloud is flow-logs --json | jq -r '.[] | select(.name=="'$PREFIX-flowlog'")|.id')
ibmcloud is flow-log-delete $flow_log_id -f
( cd tf; terraform destroy -auto-approve )

# Cloud Functions
ibmcloud fn rule delete create-rule
ibmcloud fn trigger delete create-trigger
ibmcloud fn action delete log

NAMESPACE=$PREFIX-actions
ibmcloud fn namespace delete $NAMESPACE

# Services
COS_INSTANCE_ID=$(ibmcloud resource service-instance --output JSON $COS_SERVICE_NAME | jq -r .[0].id)
ibmcloud resource service-instance-delete $COS_INSTANCE_ID --force --recursive

LOGDNA_INSTANCE_ID=$(ibmcloud resource service-instance --output JSON $LOGDNA_SERVICE_NAME | jq -r .[0].id)
ibmcloud resource service-instance-delete $LOGDNA_INSTANCE_ID --force --recursive
