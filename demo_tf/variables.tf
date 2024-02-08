variable "ibmcloud_api_key" {}
variable "resource_group_name" {}
variable "basename" {}
variable "ssh_key_name" {}
variable "region" {}

variable "ibm_zones" {
  default = [
    "us-south-1",
    "us-south-2",
    "us-south-3",
  ]
}
variable "image_os" {
  default = "ubuntu-22-04-amd64"
}

variable "profile" {
  default = "cx2-2x4"
}
