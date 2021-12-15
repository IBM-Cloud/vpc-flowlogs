# If you are creating the demo vpc environment ignore this.  Part of the
# 100-demo-vpc-and-flowlog-bucket-create.sh will be to create code_engine_config.sh.

# Unique prefix for all resources to be created.
# Use only 'a' to 'z', '0' to '9' and '-' characters.
# Do not start with a digit.
BASENAME="flowlogdna01"

# resource group name for all resources
RESOURCE_GROUP_NAME="default"

# These come from you existing COS bucket that is full of flow logs, yours will look something like these:
COS_CRN="crn:v1:bluemix:public:cloud-object-storage:global:a/713c783d11111111135fe6793c37cc74:aaaaaea1-b9d8-4082-aee4-12345678a80e::"
COS_GUID="12345678-b9d8-4082-aee4-12345678a80e"
COS_BUCKET="flowlogdna01-flowlog-001"
COS_ENDPOINT="s3.direct.us-south.cloud-object-storage.appdomain.cloud"
COS_BUCKET_REGION="us-south"