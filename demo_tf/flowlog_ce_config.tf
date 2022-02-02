module "flowlog_ce_config" {
  source              = "./../modules/flowlog_ce_config"
  basename            = var.basename
  vpc_id              = ibm_is_vpc.vpc.id
  region              = var.region
  resource_group_name = var.resource_group_name
  resource_group      = local.resource_group
  tags                = local.tags
}

output "code_engine_config" {
  value = module.flowlog_ce_config.code_engine_config
}