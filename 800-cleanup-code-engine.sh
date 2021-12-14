#!/bin/bash

source code_engine_config.sh
source code_engine_more_config.sh

ce_subscription() {
  echo ibmcloud ce subscription cos delete --name $ce_subscription_name --force
}

ce_job() {
  echo ibmcloud ce job delete --name $ce_job_name --force
}

ce_configmap() {
  echo ibmcloud ce configmap delete --name $ce_configmap_name --force
}

ce_secret() {
  ibmcloud ce secret delete -n $secret_for_apikey_name --force
}

logdna_service_key_and_ingestion_key() {
  ibmcloud resource service-key-delete $logdna_service_name-for-code-engine --force
}

logdna_service_instance() {
  ibmcloud resource service-instance-delete $logdna_service_name  --force
}

apikey_for_cos_access() {
  echo deleting the service id is enough
}

service_id_for_cos_access() {
  ibmcloud iam service-id-delete $service_id_name --force
}

authorization_policy_for_cos_ce_notifications() {
  existing_policies=$(ibmcloud iam authorization-policies --output JSON)
  #  select(.subjects[].attributes[].value=="'$project_guid'") |
  if policy_id=$(jq -er '.[] |
    select(.subjects[].attributes[].value=="codeengine") |
    select(.roles[].display_name=="Notifications Manager") |
    select(.resources[].attributes[].value=="cloud-object-storage") |
    select(.resources[].attributes[].value=="'$COS_GUID'")|.id' <<< "$existing_policies"); then
      ibmcloud iam authorization-policy-delete $policy_id --force
  fi
}

ce_project() {
  ibmcloud ce project delete --name $ce_project_name --hard --force
}


################
# liberal use of global variables throughout
echo ">>> Targeting region for code engine $CE_REGION and resource group $RESOURCE_GROUP_NAME"
ibmcloud target -r $CE_REGION -g $RESOURCE_GROUP_NAME

ce_subscription
ce_job
ce_configmap
ce_secret
logdna_service_key_and_ingestion_key
logdna_service_instance
apikey_for_cos_access
service_id_for_cos_access
authorization_policy_for_cos_ce_notifications
ce_project
################
