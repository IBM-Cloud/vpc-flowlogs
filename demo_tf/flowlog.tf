locals {
  name = var.basename
}

resource "ibm_resource_instance" "cos" {
  name              = local.name
  resource_group_id = local.resource_group
  service           = "cloud-object-storage"
  plan              = "standard"
  location          = "global"
  tags              = local.tags
}

resource "ibm_iam_authorization_policy" "is_flowlog_write_to_cos" {
  source_service_name  = "is"
  source_resource_type = "flow-log-collector"
  target_service_name  = "cloud-object-storage"
  target_resource_instance_id = ibm_resource_instance.cos.guid
  roles                = ["Writer"]
}

resource "ibm_cos_bucket" "flowlog" {
  bucket_name          = "${local.name}-flowlog-001"
  resource_instance_id = ibm_resource_instance.cos.id
  region_location      = var.region
  #storage_class        = "flex"
  storage_class        = "standard"
  force_delete         = true
}

resource ibm_is_flow_log all_vpc {
  depends_on = [ibm_iam_authorization_policy.is_flowlog_write_to_cos]
  name = local.name
  target = ibm_is_vpc.vpc.id
  active = true
  storage_bucket = ibm_cos_bucket.flowlog.bucket_name
} 

output COS_CRN {
  value = ibm_resource_instance.cos.id
}
output COS_GUID {
  value = ibm_resource_instance.cos.guid
}
output COS_BUCKET {
  value = ibm_cos_bucket.flowlog.bucket_name
}
output COS_ENDPOINT {
  value = replace(ibm_cos_bucket.flowlog.s3_endpoint_private, ".private.", ".direct.")
}
output COS_BUCKET_REGION {
  value = var.region
}