""" Library used by both the cli and __main__ cloud function
It should only have the dependencies that are required for the __main__ action
since it will be zipped up for cloud execution
"""
import datetime
import ibm_boto3
import ibm_botocore
import logging
import functools
import gzip
import json
import sys
from logdna import LogDNAHandler

def logdna_millisec_timestamp(date_str: str) -> int:
    """date_str is the format provided by flow logs, like: "capture_start_time": "2020-06-05T19:12:43Z"
    return a timestamp that is appropriate for a date in logdna"""
    dt = datetime.datetime.fromisoformat(date_str[0:-1])
    ret = dt.replace(tzinfo=datetime.timezone.utc).timestamp() * 1000
    return int(ret)

start_time_str = "start_time"
def get_start_millisec_timestamp(row):
    """Get the timestamp from the row, use start_time if available or fall back to capture_start_time"""
    if start_time_str in row:
        start_time = row[start_time_str]
        if not start_time:
            start_time = row['capture_start_time']
        return logdna_millisec_timestamp(start_time)
    else:
        click.echo(f"row does not have a {start_time_str}, row: {row}")
        return int(time.time() * 1000)

class FormatterArgs(logging.Formatter):
    """Add the args parameter, in this case for the logdna opts"""
    def format(self, record):
        return super().format(record) + f" args: {record.args}" if record.args else ""
    
@functools.lru_cache()
def get_logger(key, ingestion_endpoint):
    """add the logdna handler and a stream handler that prints stuff to stderr"""
    print(f"ingestion_endpoint: {ingestion_endpoint}")
    # print(f"key: {key}")
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(FormatterArgs())
    log.addHandler(sh)
    options = {
      'hostname': 'flowfunc',
      'ip': '10.0.1.1',
      'mac': 'C0:FF:EE:C0:FF:EE',
      'index_meta': True, # Defaults to False; when True meta objects are searchable
      'url': f'{ingestion_endpoint}/logs/ingest',
    }
    test = LogDNAHandler(key, options)
    log.addHandler(test)
    return log

@functools.lru_cache()
def get_ibm_boto3_client(cos_api_key, cos_instance_id, endpoint) -> ibm_boto3.session.Session.client:
    print("get_ibm_boto3_client called")
    return ibm_boto3.client('s3',
        ibm_api_key_id=cos_api_key,
        ibm_service_instance_id=cos_instance_id,
        config=ibm_botocore.config.Config(signature_version="oauth"),
        endpoint_url="https://" + endpoint,
        verify=True)

def encode_log_rows(jf):
    "return a list of flow logs with the top level fields repeated in each row"
    ret = []
    extra_keys = set(jf.keys()) - set(["flow_logs", "number_of_flow_logs"]) # remove these
    extra_json = {key: jf[key] for key in extra_keys}
    for fl in jf["flow_logs"]:
        all_json = {**extra_json, **fl}
        ret.append(all_json)
    return ret

def rows_from_flowlog_stream(bstream, key_value):
    """Return the rows of a binary stream"""
    ret = []
    b = bstream.read()
    s = b.decode("utf-8") 
    jf = json.loads(s)
    for log_row in encode_log_rows(jf):
        row_json = {**log_row, **{"key": key_value}}
        ret.append(row_json)
    return ret

def rows_from_gz_flowlog_stream(gz, key):
    """Return the rows of a compressed stream (.i.e COS object)"""
    with gzip.open(gz) as bstream:
        return rows_from_flowlog_stream(bstream, key)

def main(args):
    version = 22
    print(f"version {version}")
    # print(f"version {version} {args}")
    log_args = {"app": "flowlogfuncapp"}
    client = get_ibm_boto3_client(
        args["cosApiKey"],
        args['cosInstanceId'],
        args['endpoint'])
    # print(f"version {version}")
    object_key = args["key"]
    obj = client.get_object(Bucket=args["bucket"], Key=object_key)
    for row_json in rows_from_gz_flowlog_stream(obj["Body"], object_key):
        # print(f"row_json {row_json}")
        timestamp = get_start_millisec_timestamp(row_json)
        out_str = json.dumps(row_json)
        row_log_args = {**log_args, **{"timestamp": timestamp}}
        get_logger(args["logdnaKey"], args["logdnaIngestionEndpoint"]).info(out_str, row_log_args)
    return args
