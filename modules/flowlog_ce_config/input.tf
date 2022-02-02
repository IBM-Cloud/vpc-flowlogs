variable "basename" {}
variable "vpc_id" {}
variable "region" {
  description = "region for bucket, like us-south"
}
variable "resource_group" {
  description = "resource group id"
}
variable "resource_group_name" {
  description = "resource group name to be uesd for code engine"
}
variable "tags" {}
