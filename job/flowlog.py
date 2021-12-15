#!/usr/bin/env python3
"""
Code engine job code.  When executed from a COS bucket notifier the environment variable CE_DATA will be
set and the key passed as a parameter will be processed.
When no CE_DATA is set then process all of the keys in the bucket up to but not including the KEY_FIRST_LOGGED
"""
import os
import lib
import json
import sys
import logging
log = logging.getLogger("flowlog")


def logdna_regional_endpoint(region):
  return f"https://logs.{region}.logging.cloud.ibm.com"

def ce_jobrun(CE_DATA, logdna_ingestion_key, logdna_region, apikey, cos_crn, cos_bucket, cos_endpoint, key_first_logged):
    """read/log the one key passed to the job or all of the keys"""
    version = 7
    log.info(f"version={version}")
    logdna_endpoint = logdna_regional_endpoint(logdna_region)
    if CE_DATA:
      ce_data = json.loads(CE_DATA)
      if cos_bucket != ce_data["bucket"]:
        log.error(f"misconfigured bucket in config map in the environment does not match the bucket supplied by the COS subscription, COS_BUCKET:{cos_bucket},  CE_DATA[bucket]:{ce_data['bucket']}")
        cos_bucket = ce_data["bucket"]
      key = ce_data["key"]
      log.info(f"COS bucket:{cos_bucket}, key:{key}")
      lib.log_cos_object_simple(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, cos_bucket, key, key_first_logged)
    else:
      lib.log_all_cos_objects_simple(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, cos_bucket, key_first_logged)

class CeEnviron():
  def __init__(self):
    self.missing = []
    for key in [
      "LOGDNA_INGESTION_KEY",
      "APIKEY",
      "COS_CRN",
      "COS_BUCKET",
      "COS_ENDPOINT",
      "LOGDNA_REGION",
      "KEY_FIRST_LOGGED",
    ]:
      if key in os.environ:
        setattr(self, key, os.getenv(key))
      else:
        self.missing.append(key)
  def summary_fail(self):
    for key in self.missing:
      log.error(f"Key must be in environment, key:{key}")
    return len(self.missing) > 0

def ce_job():
  """code engine job run from a job run or from a subscription"""
  log.info("ce_job")
  ce_environ = CeEnviron()
  if ce_environ.summary_fail():
    log.error("Exiting, required environment variables not supplied")
    return
  # log.debug(f"LOGDNA_INGESTION_KEY:{ce_environ.LOGDNA_INGESTION_KEY} APIKEY:{ce_environ.APIKEY}")
  log.info(f"COS_CRN:{ce_environ.COS_CRN} COS_BUCKET:{ce_environ.COS_BUCKET} COS_ENDPOINT:{ce_environ.COS_ENDPOINT} LOGDNA_REGION:{ce_environ.LOGDNA_REGION} KEY_FIRST_LOGGED:{ce_environ.KEY_FIRST_LOGGED}")
  CE_DATA = os.getenv("CE_DATA", None)
  log.info(f"CE_DATA:{CE_DATA}")
  ce_jobrun(CE_DATA, ce_environ.LOGDNA_INGESTION_KEY, ce_environ.LOGDNA_REGION, ce_environ.APIKEY, ce_environ.COS_CRN, ce_environ.COS_BUCKET, ce_environ.COS_ENDPOINT, ce_environ.KEY_FIRST_LOGGED)

if __name__ == "__main__":
  logging.basicConfig()
  log.setLevel(os.getenv("LOG", default="INFO"))
  ce_job()