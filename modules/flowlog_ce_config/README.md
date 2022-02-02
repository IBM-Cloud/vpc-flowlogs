# Module for flowlog config
If you have a terraform configuration for your existing vpc you can use this module.  It will:
- Create a COS instance
- Create a COS bucket
- Create a flowlog for the vpc configured to send flowlogs to the bucket
- Create a logdna intance for use by the code engine job

Add the following to your existing terraform specification.  See demo_tf/flowlog_ce_config.tf for an example

```
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
```

Use the output to generate a configuration file:

```
terraform output code_engine_config > code_engine_config.sh
```