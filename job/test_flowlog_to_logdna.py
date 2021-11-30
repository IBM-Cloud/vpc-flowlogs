import os
import json
import ibm_boto3
from ibm_botocore.client import Config, ClientError
import gzip
import flowlog

region = "us-south"


def test_environ():
  os.environ["APIKEY"] = ""
  os.environ["APIKEY"] = ""
  # os.environ["CE_DATA"] = '{"bucket":"flowlogdna-pfq00-flowlog-001","endpoint":"","key":"ibm_vpc_flowlogs_v1/account=713c783d9a507a53135fe6793c37cc74/region=us-south/vpc-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Avpc%3Ar006-f6045065-8a82-44fc-ae1e-4817f499c9c6/subnet-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south-2%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Asubnet%3A0727-b3eda4c5-63a5-430e-a2e0-26f22e0d1fdb/endpoint-type=vnics/instance-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south-2%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Ainstance%3A0727_8a0f4f09-7b4a-4399-b7af-e96225f6ad4a/vnic-id=0727-c9ce1904-48ef-4c94-b41f-51c48ccfbee4/record-type=egress/year=2021/month=11/day=23/hour=20/stream-id=20211119T222459Z/00000006.gz","notification":{"bucket_name":"flowlogdna-pfq00-flowlog-001","event_type":"Object:Write","format":"2.0","meta_headers":[{"header":"x-amz-meta-collector_crn","value":"crn:v1:bluemix:public:is:us-south:a/713c783d9a507a53135fe6793c37cc74::flow-log-collector:r006-789fce8c-28f4-4908-8197-c18de50387b0"},{"header":"x-amz-meta-number_of_flow_logs","value":"1"},{"header":"x-amz-meta-vpc_crn","value":"crn:v1:bluemix:public:is:us-south:a/713c783d9a507a53135fe6793c37cc74::vpc:r006-f6045065-8a82-44fc-ae1e-4817f499c9c6"},{"header":"x-amz-meta-capture_start_time","value":"2021-11-23T20:29:59Z"},{"header":"x-amz-meta-instance_crn","value":"crn:v1:bluemix:public:is:us-south-2:a/713c783d9a507a53135fe6793c37cc74::instance:0727_8a0f4f09-7b4a-4399-b7af-e96225f6ad4a"},{"header":"x-amz-meta-attached_endpoint_type","value":"vnic"},{"header":"x-amz-meta-state","value":"ok"},{"header":"x-amz-meta-version","value":"0.0.1"},{"header":"x-amz-meta-capture_end_time","value":"2021-11-23T20:34:59Z"},{"header":"x-amz-meta-network_interface_id","value":"0727-c9ce1904-48ef-4c94-b41f-51c48ccfbee4"}],"object_etag":"e985738a2ef36a9ef8c79bc875355980","object_length":"587","object_name":"ibm_vpc_flowlogs_v1/account=713c783d9a507a53135fe6793c37cc74/region=us-south/vpc-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Avpc%3Ar006-f6045065-8a82-44fc-ae1e-4817f499c9c6/subnet-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south-2%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Asubnet%3A0727-b3eda4c5-63a5-430e-a2e0-26f22e0d1fdb/endpoint-type=vnics/instance-id=crn%3Av1%3Abluemix%3Apublic%3Ais%3Aus-south-2%3Aa%2F713c783d9a507a53135fe6793c37cc74%3A%3Ainstance%3A0727_8a0f4f09-7b4a-4399-b7af-e96225f6ad4a/vnic-id=0727-c9ce1904-48ef-4c94-b41f-51c48ccfbee4/record-type=egress/year=2021/month=11/day=23/hour=20/stream-id=20211119T222459Z/00000006.gz","request_id":"9fd89c26-63c1-415c-8176-10b4574fa741","request_time":"2021-11-23T20:34:59.612Z"},"operation":"Object:Write"}'
  os.environ["REGION"] = "us-south"
  os.environ["COS_CRN"] = "crn:v1:bluemix:public:cloud-object-storage:global:a/713c783d9a507a53135fe6793c37cc74:04e42b77-0fef-4882-8321-8f19f518c544::"
  os.environ["COS_BUCKET"] = "flowlogdna-pfq00-flowlog-001"
  os.environ["LOGDNA_INGESTION_KEY"] = ""
  os.environ["KEY_FIRST_LOGGED"] = "key_first_logged"
  # todo add to 030 
  flowlog.ce_job()

  
def notyet():
  # Constants for IBM COS values
  COS_ENDPOINT = "<endpoint>" # Current list avaiable at https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints
  COS_API_KEY_ID = "<api-key>" # eg "W00YixxxxxxxxxxMB-odB-2ySfTrFBIQQWanc--P3byk"
  COS_INSTANCE_CRN = "<service-instance-id>" # eg "crn:v1:bluemix:public:cloud-object-storage:global:a/3bf0d9003xxxxxxxxxx1c3e97696b71c:d6f04d83-6c4f-4a62-a165-696756d63903::"

  # Create resource

  ce_data = json.loads(CE_DATA)
  bucket = ce_data["bucket"]
  key = ce_data["key"]
  assert ce_data["bucket"] == "flowlogdna-pfq00-flowlog-001"
  APIKEY=''

  cos = ibm_boto3.resource("s3",
      ibm_api_key_id=APIKEY,
      ibm_service_instance_id=COS_CRN,
      config=Config(signature_version="oauth"),
      endpoint_url=endpoint)
  
  bucket = cos.Bucket(bucket)
  o = bucket.Object(key)
  fo = o.get()
  gz = fo["Body"].read()
  ss = gzip.decompress(gz)
  file_record = json.loads(ss)
  flow_logs = file_record["flow_logs"]
  for flow_log in flow_logs:
    print(flow_log)

if __name__ == "__main__":
  test_environ()