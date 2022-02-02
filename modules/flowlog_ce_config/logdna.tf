resource "ibm_resource_instance" "logdna" {
  name              = "${local.name}-logdna"
  service           = "logdna"
  plan              = "7-day"
  location          = var.region
  resource_group_id = var.resource_group
  tags              = var.tags
}

resource "ibm_resource_key" "logdna" {
  name                 = local.name
  role                 = "Manager"
  resource_instance_id = ibm_resource_instance.logdna.id
}
