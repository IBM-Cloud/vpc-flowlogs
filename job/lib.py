
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
import logging
from logdna import LogDNAHandler

log = logging.getLogger(__name__)

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
    
# TODO practicing
class Mylogdnahandler(logging.Handler):
  def __init__(self, logdna_handler):
    logging.Handler.__init__(self)
    self.logdna_handler = logdna_handler
    self.logdna_handler.buffer_log = self.buffer_log
  def buffer_log(self, message):
    msglen = len(message['line'])
    self.logdna_handler.buf.append(message)
    self.logdna_handler.buf_size += msglen
    self.logdna_handler.try_request()

  def emit(self, record):
    self.logdna_handler.emit(record)


# TODO practicing
@functools.lru_cache()
def get_logger(key, ingestion_endpoint):
    """add the logdna handler and a stream handler that prints stuff to stderr"""
    log.debug(f"ingestion_endpoint: {ingestion_endpoint}, ingestion key: {key}")
    # root logger will send program logs to the same logdna.  To avoid this create a "logdna" Logger
    # logger = logging.getLogger("logdna")
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(FormatterArgs())
    logger.addHandler(sh)
    options = {
      'hostname': 'flowfunc',
      'ip': '10.0.1.1',
      'mac': 'C0:FF:EE:C0:FF:EE',
      'index_meta': True, # Defaults to False; when True meta objects are searchable
      'url': f'{ingestion_endpoint}/logs/ingest',
    }
    logdna_handler = LogDNAHandler(key, options)
    logger.addHandler(Mylogdnahandler(logdna_handler))
    return logger

@functools.lru_cache()
def get_logger_good(key, ingestion_endpoint):
    """add the logdna handler and a stream handler that prints stuff to stderr"""
    log.debug(f"ingestion_endpoint: {ingestion_endpoint}, ingestion key: {key}")
    # root logger will send program logs to the same logdna.  To avoid this create a "logdna" Logger
    # logger = logging.getLogger("logdna")
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(FormatterArgs())
    logger.addHandler(sh)
    options = {
      'hostname': 'flowfunc',
      'ip': '10.0.1.1',
      'mac': 'C0:FF:EE:C0:FF:EE',
      'index_meta': True, # Defaults to False; when True meta objects are searchable
      'url': f'{ingestion_endpoint}/logs/ingest',
    }
    logdna_handler = LogDNAHandler(key, options)
    logger.addHandler(logdna_handler)
    return logger

@functools.lru_cache()
def get_ibm_boto3_client(cos_api_key, cos_instance_id, endpoint) -> ibm_boto3.session.Session.client:
    log.debug(f"get_ibm_boto3_client for cos: apikey:{cos_api_key}, instance_id: {cos_instance_id}, endpoint: {endpoint}")
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

def remember_first_logged(client, bucket, key, key_first_logged):
    """record the key of the first object logged"""
    try:
        client.get_object(Bucket=bucket, Key=key_first_logged)
    except ibm_botocore.exceptions.ClientError as ex:
        response_error_code = ex.response["Error"]["Code"]
        if response_error_code == "NoSuchKey":
            client.put_object(Bucket=bucket, Key=key_first_logged, Body=bytes(f"{key}", 'utf-8'))
        else:
            log.exception(f"Exception response for check of get_object({bucket}, {key_first_logged})")

def log_cos_object(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, bucket, key):
    # log_args = {"app": "flowlogfuncapp"}
    client = get_ibm_boto3_client(apikey, cos_crn, cos_endpoint)
    obj = client.get_object(Bucket=bucket, Key=key)
    items = 0
    for row_json in rows_from_gz_flowlog_stream(obj["Body"], key):
        items += 1
        # print(f"row_json {row_json}")
        timestamp = get_start_millisec_timestamp(row_json)
        out_str = json.dumps(row_json)
        # row_log_args = {**log_args, **{"timestamp": timestamp}}
        # get_logger(args["logdnaKey"], args["logdnaIngestionEndpoint"]).info(out_str, row_log_args)
        get_logger(logdna_ingestion_key, logdna_endpoint).info(out_str)
        # TODO line above is good, below is testing
        #get_logger(logdna_ingestion_key, logdna_endpoint)

def log_all_cos_objects(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, bucket, key_first_logged):
    def extract_hours(key):
        #id = key.split("/")[-1]
        #return id
        parameters = key.split("/")
        key_name_params = dict([n.split("=") for n in key.split("/")[1:-1]])
        # return key_name_params["year"] + key_name_params["month"] + key_name_params["day"] + key_name_params["hour"]
        return parameters[-1]

    client = get_ibm_boto3_client(apikey, cos_crn, cos_endpoint)
    os = client.list_objects(Bucket=bucket)
    hour = ""
    hours = list()
    count = 0
    current_key = ""
    while True:
      for content in os["Contents"]:
        key = content["Key"]
        next_hour = extract_hours(key)
        if hour != next_hour:
          hours.append(next_hour)
        if next_hour < hour:
          print("out of order")
        hour = next_hour
        current_key = key
        count = count + 1
        log_cos_object(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, bucket, key)
      if os["IsTruncated"]:
        os = client.list_objects(Bucket=bucket, Marker=os["NextMarker"])
      else:
        break
    log.info(f"count = {count}")

def log_cos_object_and_remember(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, bucket, key, key_first_logged):
    log_cos_object(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, bucket, key)
    # record the key of the first object logged
    remember_first_logged(client, bucket, key, key_first_logged)


def main(args):
    version = 23
    log.info(f"version {version}")
    log_args = {"app": "flowlogjob"}
    client = get_ibm_boto3_client(
        args["cosApiKey"],
        args['cosInstanceId'],
        args['endpoint'])
    object_key = args["key"]
    obj = client.get_object(Bucket=args["bucket"], Key=object_key)
    for row_json in rows_from_gz_flowlog_stream(obj["Body"], object_key):
        # print(f"row_json {row_json}")
        timestamp = get_start_millisec_timestamp(row_json)
        out_str = json.dumps(row_json)
        row_log_args = {**log_args, **{"timestamp": timestamp}}
        # get_logger(args["logdnaKey"], args["logdnaIngestionEndpoint"]).info(out_str, row_log_args)
        get_logger(args["logdnaKey"], args["logdnaIngestionEndpoint"]).info(out_str)
    return args
