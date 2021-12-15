resource "ibm_resource_instance" "logdna" {
  name              = "${local.name}-logdna"
  service   = "logdna"
  plan              = "7-day"
  location = var.region
  resource_group_id = local.resource_group
  tags              = local.tags
}

resource "ibm_resource_key" "logdna" {
  name = local.name
  role = "Manager"
  resource_instance_id = ibm_resource_instance.logdna.id
}

output LOGDNA_REGION {
  value = var.region
}

output LOGDNA_NAME {
  value = ibm_resource_instance.logdna.name
}

output LOGDNA_INGESTION_KEY {
  sensitive = true
  value = ibm_resource_key.logdna.credentials.ingestion_key
}