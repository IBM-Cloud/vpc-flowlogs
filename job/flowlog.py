#!/usr/bin/env python3
"""
Code engine job code.  When executed from a COS bucket notifier the environment variable CE_DATA will be
set and the key passed as a parameter will be processed.
When no CE_DATA is set then process all of the keys in the bucket up to but not including the KEY_FIRST_LOGGED
"""
import os
import lib
# import requests
import json
import sys
import logging
log = logging.getLogger(__name__)


def cos_regional_endpoint(region):
  #r = requests.get("https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints")
  # return f'https://{json.loads(r.text)["service-endpoints"]["regional"][region]["public"][region]}'
  #regionals = json.loads(r.text)["service-endpoints"]["regional"]
  #for r, d in regionals.items():
  #  assert d["public"][r] == f"s3.{r}.cloud-object-storage.appdomain.cloud"
  return f's3.{region}.cloud-object-storage.appdomain.cloud'

def logdna_regional_endpoint(region):
  return f"https://logs.{region}.logging.cloud.ibm.com"

def ce_jobrun(CE_DATA, logdna_ingestion_key, apikey, cos_crn, cos_bucket, region, key_first_logged):
    """read/log the one key passed to the job or all of the keys"""
    version = 5
    log.info(f"version={version}")
    cos_region = region
    cos_endpoint = cos_regional_endpoint(cos_region)
    logdna_region = region
    logdna_endpoint = logdna_regional_endpoint(logdna_region)
    if CE_DATA:
      ce_data = json.loads(CE_DATA)
      if cos_bucket != ce_data["bucket"]:
        log.error(f"misconfigured bucket in config map {cos_bucket} is not the same as the ce_data[bucket] {ce_data['bucket']}")
        cos_bucket = ce_data["bucket"]
      key = ce_data["key"]
      lib.log_cos_object_and_remember(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, bucket, key, key_first_logged)
    else:
      lib.log_all_cos_objects(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, cos_bucket, key_first_logged)

def ce_job():
  """code engine job run from a job run or from a subscription"""
  log.info("ce_job")
  LOGDNA_INGESTION_KEY = os.getenv("LOGDNA_INGESTION_KEY")
  APIKEY = os.getenv("APIKEY")
  COS_CRN = os.getenv("COS_CRN")
  COS_BUCKET = os.getenv("COS_BUCKET")
  REGION = os.getenv("REGION")
  KEY_FIRST_LOGGED = os.getenv("KEY_FIRST_LOGGED")
  CE_DATA = os.getenv("CE_DATA", None)
  log.info(f"COS_CRN:{COS_CRN} COS_BUCKET:{COS_BUCKET} REGION:{REGION} KEY_FIRST_LOGGED:{KEY_FIRST_LOGGED} CE_DATA:{CE_DATA}")
  ce_jobrun(CE_DATA, LOGDNA_INGESTION_KEY, APIKEY, COS_CRN, COS_BUCKET, REGION, KEY_FIRST_LOGGED)

if __name__ == "__main__":
  logging.basicConfig(level=os.getenv("LOG"))
  ce_job()