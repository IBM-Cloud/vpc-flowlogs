import os
import json
import ibm_boto3
from ibm_botocore.client import Config, ClientError
import gzip
import flowlog
import logging

region = "us-south"

def setup_environ(key=None):
  logging.basicConfig()
  logging.getLogger("flowlog").setLevel("INFO")
  os.environ["APIKEY"] = "wPSoNchl2OzaRDyAoVa7080AShni_22_GYLIFek4DLRF"
  # os.environ["CE_DATA"] = '{"bucket":"flowlogdna-pfq00-flowlog-001","endpoint":"","key":"ibm_vpc_flowlogs_v1/account=713c783d9a507a53135fe6793c37cc74/region=us-south/vpc-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Avpc%3Ar006-f6045065-8a82-44fc-ae1e-4817f499c9c6/subnet-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south-2%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Asubnet%3A0727-b3eda4c5-63a5-430e-a2e0-26f22e0d1fdb/endpoint-type=vnics/instance-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south-2%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Ainstance%3A0727_8a0f4f09-7b4a-4399-b7af-e96225f6ad4a/vnic-id=0727-c9ce1904-48ef-4c94-b41f-51c48ccfbee4/record-type=egress/year=2021/month=11/day=23/hour=20/stream-id=20211119T222459Z/00000006.gz","notification":{"bucket_name":"flowlogdna-pfq00-flowlog-001","event_type":"Object:Write","format":"2.0","meta_headers":[{"header":"x-amz-meta-collector_crn","value":"crn:v1:bluemix:public:is:us-south:a/713c783d9a507a53135fe6793c37cc74::flow-log-collector:r006-789fce8c-28f4-4908-8197-c18de50387b0"},{"header":"x-amz-meta-number_of_flow_logs","value":"1"},{"header":"x-amz-meta-vpc_crn","value":"crn:v1:bluemix:public:is:us-south:a/713c783d9a507a53135fe6793c37cc74::vpc:r006-f6045065-8a82-44fc-ae1e-4817f499c9c6"},{"header":"x-amz-meta-capture_start_time","value":"2021-11-23T20:29:59Z"},{"header":"x-amz-meta-instance_crn","value":"crn:v1:bluemix:public:is:us-south-2:a/713c783d9a507a53135fe6793c37cc74::instance:0727_8a0f4f09-7b4a-4399-b7af-e96225f6ad4a"},{"header":"x-amz-meta-attached_endpoint_type","value":"vnic"},{"header":"x-amz-meta-state","value":"ok"},{"header":"x-amz-meta-version","value":"0.0.1"},{"header":"x-amz-meta-capture_end_time","value":"2021-11-23T20:34:59Z"},{"header":"x-amz-meta-network_interface_id","value":"0727-c9ce1904-48ef-4c94-b41f-51c48ccfbee4"}],"object_etag":"e985738a2ef36a9ef8c79bc875355980","object_length":"587","object_name":"ibm_vpc_flowlogs_v1/account=713c783d9a507a53135fe6793c37cc74/region=us-south/vpc-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Avpc%3Ar006-f6045065-8a82-44fc-ae1e-4817f499c9c6/subnet-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south-2%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Asubnet%3A0727-b3eda4c5-63a5-430e-a2e0-26f22e0d1fdb/endpoint-type=vnics/instance-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south-2%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Ainstance%3A0727_8a0f4f09-7b4a-4399-b7af-e96225f6ad4a/vnic-id=0727-c9ce1904-48ef-4c94-b41f-51c48ccfbee4/record-type=egress/year=2021/month=11/day=23/hour=20/stream-id=20211119T222459Z/00000006.gz","request_id":"9fd89c26-63c1-415c-8176-10b4574fa741","request_time":"2021-11-23T20:34:59.612Z"},"operation":"Object:Write"}'
  os.environ["REGION"] = "us-south"
  os.environ["COS_CRN"] = "crn:v1:bluemix:public:cloud-object-storage:global:a/713c783d9a507a53135fe6793c37cc74:04e42b77-0fef-4882-8321-8f19f518c544::"
  bucket = "flowlogdna-pfq00-flowlog-001"
  os.environ["COS_BUCKET"] = bucket
  os.environ["LOGDNA_INGESTION_KEY"] = "546f63b1deff6e857b3f8c44d781ed60"
  os.environ["KEY_FIRST_LOGGED"] = "key_first_logged"
  if key:
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

def test_all():
  setup_environ()
  flowlog.ce_job()

def test_one():
  setup_environ('ibm_vpc_flowlogs_v1/account=713c783d9a507a53135fe6793c37cc74/region=us-south/vpc-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Avpc%3Ar006-f6045065-8a82-44fc-ae1e-4817f499c9c6/subnet-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south-1%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Asubnet%3A0717-92648d20-23a7-440f-a3bf-ceb75a3aab3b/endpoint-type=vnics/instance-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south-1%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Ainstance%3A0717_de4510d7-20d3-460e-9907-e24ddcfce463/vnic-id=0717-07e4fad5-b0a2-4958-b4fb-0cfa140f02c8/record-type=egress/year=2021/month=11/day=19/hour=22/stream-id=20211119T222506Z/00000004.gz')
  flowlog.ce_job()

if __name__ == "__main__":
  test_one()