locals {
  output_logdna_region        = var.region
  output_logdna_ingestion_key = nonsensitive(ibm_resource_key.logdna.credentials.ingestion_key)
  output_cos_bucket_crn       = ibm_cos_bucket.flowlog.crn
  output_cos_endpoint         = replace(ibm_cos_bucket.flowlog.s3_endpoint_private, ".private.", ".direct.")
}

output "LOGDNA_REGION" {
  value = local.output_logdna_region
}

output "LOGDNA_INGESTION_KEY" {
  value = local.output_logdna_ingestion_key
}
output "COS_BUCKET_CRN" {
  value = local.output_cos_bucket_crn
}
output "COS_ENDPOINT" {
  value = local.output_cos_endpoint
}

output "code_engine_config" {
  value = <<-EOF
    BASENAME=${var.basename}
    RESOURCE_GROUP_NAME=${var.resource_group_name}
    COS_BUCKET_CRN=${local.output_cos_bucket_crn}
    COS_ENDPOINT=${local.output_cos_endpoint}
    LOGDNA_REGION=${local.output_logdna_region}
    LOGDNA_INGESTION_KEY=${local.output_logdna_ingestion_key}
  EOF
}
