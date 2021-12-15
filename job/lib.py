
""" Library used by both the cli and __main__ cloud function
It should only have the dependencies that are required for the __main__ action
since it will be zipped up for cloud execution
"""
import dataclasses
import ibm_boto3
import ibm_botocore
import logging
import functools
import gzip
import json
import logdna_synchronous

log = logging.getLogger("flowlog")

@functools.lru_cache()
def get_ibm_boto3_client(cos_api_key, cos_instance_id, endpoint) -> ibm_boto3.session.Session.client:
    log.debug(f"get_ibm_boto3_client for cos: instance_id: {cos_instance_id}, endpoint: {endpoint}")
    # log.debug(f"get_ibm_boto3_client for cos: apikey:{cos_api_key}, instance_id: {cos_instance_id}, endpoint: {endpoint}")
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
        all_json = {**extra_json, **fl, **{"_app": "FLCE"}}
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

def client_head_key(client, bucket, key):
    """return the head for the key or None if not found"""
    try:
        response = client.head_object(Bucket=bucket, Key=key)
    except ibm_botocore.exceptions.ClientError as ex:
        response_error_code = ex.response["Error"]["Code"]
        if response_error_code == '404':
            return None
        else:
            log.exception(f"Exception response for check of head_object({bucket}, {key})")
            return None
    return response

@dataclasses.dataclass
class CosObject:
    obj: str = None
    exception: Exception = None
    error_str: str = None
    def good(self) -> bool:
      return self.obj != None
    def non_fatal(self) -> bool:
      return (not self.good()) and isinstance(self.exception, ibm_botocore.exceptions.ClientError) and self.exception.response['Error']['Code'] == "NoSuchKey"
    def fatal(self) -> bool:
      return not self.non_fatal()


def client_get_object(client, bucket, key):
    """called when the object is known to exist"""
    log.debug(f"client_get_object, key:{key}")
    try:
      obj = client.get_object(Bucket=bucket, Key=key)
    except ibm_botocore.exceptions.ClientError as ex:
        log.error(f"client_get_object({bucket}, {key}) client error")
        return CosObject(None, ex, "client error")
    except ibm_botocore.exceptions.CredentialRetrievalError as ex:
        return CosObject(None, ex, "bad credentials, this is fatal")
    except Exception as ex:
        log.error(f"unexpected exceptionsclient_get_object({bucket}, {key}) raised exception")
        log.exception(ex)
        return CosObject(None, ex, error_str="unexpected exception")
    return CosObject(obj)

def log_cos_object_keys(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, bucket, keys):
    """Send list of cos flowlog objects to logdna"""
    log.info(f"sending the content of cos objects from bucket to logdna, number of objects:{len(keys)} bucket {bucket}")
    client = get_ibm_boto3_client(apikey, cos_crn, cos_endpoint)
    logdna_writer = logdna_synchronous.LogdnaSynchronous(logdna_endpoint, logdna_ingestion_key, "flowlogjob")
    for key in keys:
      cos_obj = client_get_object(client, bucket, key)
      if cos_obj.good():
          obj = cos_obj.obj
          for row_json in rows_from_gz_flowlog_stream(obj["Body"], key):
              out_str = json.dumps(row_json)
              logdna_writer.emit(out_str)
      elif cos_obj.fatal():
        log.error(f"fatal cos error, quiting: {cos_obj.error_str}")
        break
      else:
        log.error(f"non fatal cos error, continuing: {cos_obj.error_str}")

    logdna_writer.close()

def log_cos_object(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, bucket, key):
    log_cos_object_keys(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, bucket, [key])

@dataclasses.dataclass
class KeyHeadOlder:
    """when a key is found to be older then the KeyFirstLogged (see below) return one of these"""
    key: str  # key that is older then key first logged
    head: dict # head of the older key (only valid if older == True)
    older: bool # indication that it is older.

class KeyFirstLogged:
    """The key_first_logged is the key to an object.  The object contains a key - the key first logged.
    Return the KeyHeadOlder of the key that is in the object.  If key_first_logged is None then all subsequent
    objects will be processed and considered older"""
    def __init__(self, client, bucket, key_first_logged):
        self.client = client
        self.bucket = bucket
        self.key_first_logged = key_first_logged
        self.head_first_logged_object = None
        # if no key_first_logged provided then all objects are considered older
        if self.key_first_logged:
          head = client_head_key(client, bucket, key_first_logged)
          if head != None:
              # The key exists.  The contents of the object is a key of the first logged object
              log.info(f"key first logged exists, key:{key_first_logged}")
              obj = client_get_object(self.client, self.bucket, self.key_first_logged)
              if obj != None:
                  try:
                      self.key_of_first_logged_object = obj["Body"].read().decode("utf-8")
                  except Exception as ex:
                      log.error(f"exception raised reading utf-8 string from bucket object {key_first_logged}")
                      log.exception(ex)
                      return
                  log.info(f"key in {self.key_first_logged} is {self.key_of_first_logged_object}")
                  self.head_first_logged_object = client_head_key(client, bucket, self.key_of_first_logged_object)
                  self.key_name_params = self.split_key_name_params(self.key_of_first_logged_object)

    def split_key_name_params(self, key):
        parameters = key.split("/")
        return dict([n.split("=") for n in key.split("/")[1:-1]])

    def older(self, key: str):
      """Is this key older then me, .i.e older then the first logged object, if no key_first_logged provided always provide the head"""
      # if false is being returned there is no reason to head the object, so short circuit return
      if self.head_first_logged_object != None:
          key_name_params = self.split_key_name_params(key)
          for date_part in ("year", "month", "day", "hour"):
              if not(date_part in key_name_params) or self.key_name_params[date_part] > key_name_params[date_part]:
                  log.debug(f"short circuit newer object {key}")
                  return KeyHeadOlder(key, None, False)
      # It is pretty old look more deeply:
      head = client_head_key(self.client, self.bucket, key) 
      if head == None:
          log.error(f"get_head failed.  bucket: {bucket}, key {key}")
          return KeyHeadOlder(key, None, False) # it is not going to do any good to log this object it can no be read
      
      if self.head_first_logged_object == None:
          return KeyHeadOlder(key, head, True)
      else:
          return KeyHeadOlder(key, head, head['Metadata']['capture_start_time'] < self.head_first_logged_object['Metadata']['capture_start_time'])

def keys_in_bucket(apikey, cos_crn, cos_endpoint, bucket):
    client = get_ibm_boto3_client(apikey, cos_crn, cos_endpoint)
    os = client.list_objects(Bucket=bucket)
    keys = []
    while True:
      for content in os["Contents"]:
        key = content["Key"]
        keys.append(key)
      if os["IsTruncated"]:
        os = client.list_objects(Bucket=bucket, Marker=os["NextMarker"])
      else:
        break
    return keys  

def log_all_cos_objects(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, bucket, key_first_logged):
    client = get_ibm_boto3_client(apikey, cos_crn, cos_endpoint)
    key_first_logged = KeyFirstLogged(client, bucket, key_first_logged)
    os = client.list_objects(Bucket=bucket)
    key_heads = []
    while True:
      log.info(f'sorting a set of cos flowlog objects len:{len(os["Contents"])}, bucket:{bucket}')
      for content in os["Contents"]:
        key = content["Key"]
        key_head = key_first_logged.older(key)
        if key_head.older:
            key_heads.append(key_head)
        else:
            log.debug(f"key ignored because it is too new, key {key}")
      if os["IsTruncated"]:
        os = client.list_objects(Bucket=bucket, Marker=os["NextMarker"])
      else:
        break
    
    key_heads = sorted(key_heads, key=lambda key_head: key_head.head['Metadata']['capture_start_time'])
    all_keys = [key_head.key for key_head in key_heads]
    log_cos_object_keys(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, bucket, all_keys)
    
def log_cos_object_and_remember(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, bucket, key, key_first_logged):
    log_cos_object(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, bucket, key)
    # record the key of the first object logged
    remember_first_logged(get_ibm_boto3_client(apikey, cos_crn, cos_endpoint), bucket, key, key_first_logged)

def log_all_cos_objects_simple(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, bucket, key_first_logged):
    keys = keys_in_bucket(apikey, cos_crn, cos_endpoint, bucket)
    log.info(f'sorting a set of cos flowlog objects, a head will now be executed for each key, len:{len(keys)}')
    client = get_ibm_boto3_client(apikey, cos_crn, cos_endpoint)
    key_first_logged = KeyFirstLogged(client, bucket, None)
    # to a head for all keys
    key_heads = [key_first_logged.older(key) for key in keys]
    key_heads = sorted(key_heads, key=lambda key_head: key_head.head['Metadata']['capture_start_time'])
    all_keys = [key_head.key for key_head in key_heads]
    log_cos_object_keys(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, bucket, all_keys)
    
def log_cos_object_simple(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, bucket, key, key_first_logged):
    log_cos_object(logdna_endpoint, logdna_ingestion_key, apikey, cos_crn, cos_endpoint, bucket, key)
