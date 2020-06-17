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

# Resource authorizations:
echo '>>> iam authorization policy from flow-log-collector to COS bucket'
COS_INSTANCE_ID=$(ibmcloud resource service-instance --output JSON $COS_SERVICE_NAME | jq -r '.[0].guid')
EXISTING_POLICIES=$(ibmcloud iam authorization-policies --output JSON)
EXISTING_POLICY_ID=$(echo "$EXISTING_POLICIES" | \
  jq -r '.[] |
  select(.subjects[].attributes[].value=="flow-log-collector") |
  select(.subjects[].attributes[].value=="is") |
  select(.roles[].display_name=="Writer") |
  select(.resources[].attributes[].value=="cloud-object-storage") |
  select(.resources[].attributes[].value=="'$COS_INSTANCE_ID'")|.id')
ibmcloud iam authorization-policy-delete $EXISTING_POLICY_ID -f

# Services
COS_INSTANCE_ID=$(ibmcloud resource service-instance --output JSON $COS_SERVICE_NAME | jq -r .[0].id)
ibmcloud resource service-instance-delete $COS_INSTANCE_ID --force --recursive

LOGDNA_INSTANCE_ID=$(ibmcloud resource service-instance --output JSON $LOGDNA_SERVICE_NAME | jq -r .[0].id)
ibmcloud resource service-instance-delete $LOGDNA_INSTANCE_ID --force --recursive
