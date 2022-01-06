export DOCKER_IMAGE=ibmcom/sample-flowlog-logdna:latest

# Contstants that are not required to configure, see comments
CE_REGION=$LOGDNA_REGION
ce_project_name=$BASENAME-project; # will be created/updated
ce_job_name=$BASENAME-job; # will be created/updated
ce_subscription_name=$BASENAME-cos-to-job; # will be created/updated
ce_configmap_name=$BASENAME-configmap; # will be created/updated
service_id_name=$BASENAME-cos; # will be created/updated
service_api_key_name=$BASENAME-cos; # will be created/updated
secret_for_apikey_name=$BASENAME; # will be deleted if it exists and a new one created
key_first_logged="first_logged"
