#!/usr/bin/env python

import pathlib
import os
import json
import ibm_boto3
import logging
import configparser
import flowlog
import lib

log = logging.getLogger("flowlog")

def cos_public_endpoint(cos_endpoint):
  #return f's3.{region}.cloud-object-storage.appdomain.cloud'
  return cos_endpoint.replace(".direct.", ".", 1)

def setup_environ(key=None):
  config = configparser.ConfigParser()
  logging.basicConfig()
  logging.getLogger("flowlog").setLevel("DEBUG")

def test_all():
  flowlog.ce_job()

known_key = None
# look up a key to avoid reading all of the keys in the bucket
#known_key = 'ibm_vpc_flowlogs_v1/account=713c783d9a507a53135fe6793c37cc74/region=us-south/vpc-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Avpc%3Ar006-0f9c0744-3a8e-4381-96bc-8cea1a0cb9cd/subnet-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south-2%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Asubnet%3A0727-c3a6ab5c-a68e-4682-934b-8b7b322b95af/endpoint-type=vnics/instance-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south-2%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Ainstance%3A0727_35d351c2-b74a-434c-946a-177420e476f4/vnic-id=0727-53951b15-ba23-4495-80b8-0b2f4617c506/record-type=egress/year=2021/month=12/day=14/hour=13/stream-id=20211210T183830Z/00000010.gz'
def test_one():
  ce_environ = flowlog.CeEnviron()
  bucket = ce_environ.COS_BUCKET
  if known_key:
    key = known_key
  else:
    ce_environ = flowlog.CeEnviron()
    keys = lib.keys_in_bucket(ce_environ.APIKEY, ce_environ.COS_CRN, ce_environ.COS_ENDPOINT, bucket)
    key = keys[0]

  # most of this stuff is ignored.  Just the bucket is useful
  os.environ["CE_DATA"] = json.dumps({
    "bucket": bucket,
    "endpoint":"",
    "key": key,
    "notification":{"bucket_name":bucket,
      "event_type":"Object:Write",
      "format":"2.0",
      "meta_headers":[{"header":"x-amz-meta-collector_crn","value":"crn:v1:bluemix:public:is:us-south:a/713c783d9a507a53135fe6793c37cc74::flow-log-collector:r006-789fce8c-28f4-4908-8197-c18de50387b0"},{"header":"x-amz-meta-number_of_flow_logs","value":"1"},{"header":"x-amz-meta-vpc_crn","value":"crn:v1:bluemix:public:is:us-south:a/713c783d9a507a53135fe6793c37cc74::vpc:r006-f6045065-8a82-44fc-ae1e-4817f499c9c6"},{"header":"x-amz-meta-capture_start_time","value":"2021-11-23T20:29:59Z"},{"header":"x-amz-meta-instance_crn","value":"crn:v1:bluemix:public:is:us-south-2:a/713c783d9a507a53135fe6793c37cc74::instance:0727_8a0f4f09-7b4a-4399-b7af-e96225f6ad4a"},{"header":"x-amz-meta-attached_endpoint_type","value":"vnic"},{"header":"x-amz-meta-state","value":"ok"},{"header":"x-amz-meta-version","value":"0.0.1"},{"header":"x-amz-meta-capture_end_time","value":"2021-11-23T20:34:59Z"},{"header":"x-amz-meta-network_interface_id","value":"0727-c9ce1904-48ef-4c94-b41f-51c48ccfbee4"}],
      "object_etag":"e985738a2ef36a9ef8c79bc875355980",
      "object_length":"587",
      "object_name":"ibm_vpc_flowlogs_v1/account=713c783d9a507a53135fe6793c37cc74/region=us-south/vpc-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Avpc%3Ar006-f6045065-8a82-44fc-ae1e-4817f499c9c6/subnet-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south-2%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Asubnet%3A0727-b3eda4c5-63a5-430e-a2e0-26f22e0d1fdb/endpoint-type=vnics/instance-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south-2%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Ainstance%3A0727_8a0f4f09-7b4a-4399-b7af-e96225f6ad4a/vnic-id=0727-c9ce1904-48ef-4c94-b41f-51c48ccfbee4/record-type=egress/year=2021/month=11/day=23/hour=20/stream-id=20211119T222459Z/00000006.gz","request_id":"9fd89c26-63c1-415c-8176-10b4574fa741","request_time":"2021-11-23T20:34:59.612Z"},
      "operation":"Object:Write"})
  flowlog.ce_job()

if __name__ == "__main__":
  # read the python.ini file and put the contents into the environment
  setup_environ()
  log.info("starting test")
  python_ini=str(pathlib.Path(__file__).parent.parent / "python.ini")
  config = configparser.ConfigParser()
  config.read(python_ini)
  for k,v in config['env'].items():
    if k == "cos_endpoint":
      # If configured with the direct endpoint for COS bucket debugging from desktop is not going to work
      v = cos_public_endpoint(v)
    os.environ[k.upper()] = v
  test_one()
  #test_all()