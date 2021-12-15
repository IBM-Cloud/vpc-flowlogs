export DOCKER_IMAGE=powellquiring/flowlog:1.2

# Contstants that are not required to configure, see comments
CE_REGION=$LOGDNA_REGION
ce_project_name=$BASENAME-project; # will be created if it does not exist
ce_job_name=$BASENAME-job; # will be created if it does not exist
ce_subscription_name=$BASENAME-cos-to-job
ce_configmap_name=$BASENAME-configmap
service_id_name=$BASENAME-cos
service_api_key_name=$BASENAME-cos
secret_for_apikey_name=$BASENAME
key_first_logged="first_logged"