export DOCKER_IMAGE=powellquiring/flowlog:1.2

# Contstants that are not required to configure, see comments
region=$COS_BUCKET_REGION; # if this is not a regional bucket then hard code this to the desired region, like us-south
LOGDNA_REGION=$COS_BUCKET_REGION; # choose a region in which to create the logdna instance
logdna_service_name=$BASENAME-logdna; # will be created if it does not exist
CE_REGION=$COS_BUCKET_REGION
ce_project_name=$BASENAME-project; # will be created if it does not exist
ce_job_name=$BASENAME-job; # will be created if it does not exist
ce_subscription_name=$BASENAME-cos-to-job
ce_configmap_name=$BASENAME-configmap
service_id_name=$BASENAME
service_api_key_name=$BASENAME
secret_for_apikey_name=$BASENAME
key_first_logged="first_logged"