#!/bin/bash
source ./shared.sh

# vpc and flow logs
if flow_log_id=$(ibmcloud is flow-logs --json | jq -e -r '.[] | select(.name=="'$PREFIX-flowlog'")|.id'); then
  ibmcloud is flow-log-delete $flow_log_id -f
fi

if workspace_id=$(get_workspace_id); then
  ibmcloud schematics destroy --id $workspace_id -f
  poll_for_latest_action_to_finish $workspace_id
  ibmcloud schematics workspace delete --id $workspace_id -f
fi


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
