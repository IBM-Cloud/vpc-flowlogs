locals {
  tags = [
    "basename:${var.basename}",
    lower(replace("dir:${abspath(path.root)}", "/", "_")),
  ]
  resource_group = data.ibm_resource_group.group.id
}

# VPC with one subnet, one VSI and a floating IP
provider "ibm" {
  region           = var.region
  ibmcloud_api_key = var.ibmcloud_api_key
}

data "ibm_resource_group" "group" {
  name = var.resource_group_name
}

data "ibm_is_ssh_key" "ssh_key" {
  name = var.ssh_key_name
}

data "ibm_is_image" "ubuntu" {
  name = var.ubuntu1804
}

## Resources
resource "ibm_is_vpc" "vpc" {
  name = var.basename
  resource_group            = local.resource_group
  tags = local.tags
}

# vsi1 access 
resource "ibm_is_security_group" "sg1" {
  name = "${var.basename}-sg1"
  vpc  = ibm_is_vpc.vpc.id
}

# Add the ability to access the ibm app endpoint from any ip address, like from a desktop try: curl IP:3000
resource "ibm_is_security_group_rule" "sg1_ingress_app_all" {
  group     = ibm_is_security_group.sg1.id
  direction = "inbound"
  remote    = "0.0.0.0/0"

  tcp {
    port_min = 3000
    port_max = 3000
  }
}
locals {
  ibm_vsi1_user_data = "${replace(local.shared_app_user_data, "REMOTE_IP", ibm_is_instance.vsi2.primary_network_interface.0.primary_ipv4_address)}"
  ibm_vsi1_security_groups = [ibm_is_security_group.sg1.id, ibm_is_security_group.install_software.id]
}

resource "ibm_is_subnet" "subnet1" {
  name                     = "${var.basename}-subnet1"
  resource_group            = local.resource_group
  vpc                      = ibm_is_vpc.vpc.id
  zone                     = var.ibm_zones[0]
  total_ipv4_address_count = 256
  tags = local.tags
}

resource "ibm_is_instance" "vsi1" {
  name    = "${var.basename}-vsi1"
  resource_group            = local.resource_group
  vpc     = ibm_is_vpc.vpc.id
  zone    = var.ibm_zones[0]
  keys    = [data.ibm_is_ssh_key.ssh_key.id]
  image   = data.ibm_is_image.ubuntu.id
  profile = var.profile

  primary_network_interface {
    subnet = ibm_is_subnet.subnet1.id
    security_groups = local.ibm_vsi1_security_groups
  }

  user_data = local.ibm_vsi1_user_data
  tags = local.tags
}

resource "ibm_is_floating_ip" "vsi1" {
  name   = "${var.basename}-vsi1"
  resource_group            = local.resource_group
  target = ibm_is_instance.vsi1.primary_network_interface[0].id
  tags = local.tags
}

output "vpc_id" {
  value = ibm_is_vpc.vpc.id
}

output "ibm1_public_ip" {
  value = ibm_is_floating_ip.vsi1.address
}

output "ibm1_private_ip" {
  value = ibm_is_instance.vsi1.primary_network_interface[0].primary_ipv4_address
}

output ibm1_curl {
  value = <<EOS
curl ${ibm_is_floating_ip.vsi1.address}:3000; # get hello world string
curl ${ibm_is_floating_ip.vsi1.address}:3000/info; # get the private IP address
curl ${ibm_is_floating_ip.vsi1.address}:3000/remote; # get the remote private IP address
EOS
}