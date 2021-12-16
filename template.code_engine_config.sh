# If you are creating the demo vpc environment ignore this.  Part of the
# 100-demo-vpc-and-flowlog-bucket-create.sh will be to create code_engine_config.sh.

# Unique prefix for all resources to be created.
# Use only 'a' to 'z', '0' to '9' and '-' characters.
# Do not start with a digit.
BASENAME="flowlogdna01"

# resource group name for all resources
RESOURCE_GROUP_NAME="default"

# These come from you existing COS bucket that is full of flow logs, yours will look something like these, note the bucket crn
# is the COS CRN with the string "bucket:YourBucketName" replaces the final :
COS_BUCKET_CRN="crn:v1:bluemix:public:cloud-object-storage:global:a/713c783d9a507a53135fe6793c37cc74:14fb3378-0f87-4bb8-9eae-0e7ee71bf3ce:bucket:flowlogdna03-cefl-001"
COS_ENDPOINT="s3.direct.us-south.cloud-object-storage.appdomain.cloud"

# These come from the LOGDNA service instance that was created
LOGDNA_REGION="us-south"
LOGDNA_INGESTION_KEY="e4bb78b17fc46651e2998c4afc9e461d"