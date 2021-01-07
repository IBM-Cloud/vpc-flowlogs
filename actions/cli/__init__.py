import click
from pathlib import Path
import os
import subprocess
import json
import time
import lib
import datetime
import logging
import asyncio

class MissingEnvironmentVariable(Exception):
    def __init__(self, variable):
        self.variable = variable

def os_environ(env_var):
    if env_var in os.environ:
        return os.environ[env_var]
    click.echo(f"Set the environment variable {env_var}")
    click.echo(f"export {env_var}=VALUE")
    raise MissingEnvironmentVariable(env_var)

def cos_bucket_name():
    return os_environ("COS_BUCKET_NAME")

def cos_api_key():
    return os_environ("COS_API_KEY")

def cos_instance_id():
    return os_environ("COS_INSTANCE_ID")

def logdna_key():
    return os_environ("LOGDNAKEY")

def logdna_ingestion_endpoint():
    return os_environ("LOGDNA_INGESTION_ENDPOINT")

def cos_endpoint():
    return os_environ("COSENDPOINT")

def log_command(command, **kwargs):
    print(' '.join(command) + '    ' + kwargs.get('delimiter', ''))
    stdout = ''
    try:
        out = subprocess.check_output(command)
        stdout = out.decode()
    except subprocess.CalledProcessError:
        print('*** Command execution failed')
    if kwargs.get('print_output', True):
        print(stdout)
    return stdout

def get_keys(bucket):
    stdout = log_command(['ibmcloud', 'cos', 'list-objects', '--bucket', bucket, '--json'], print_output=False)
    record = json.loads(stdout)
    ret = []
    for o in record["Contents"]:
        ret.append(o['Key'])
    return ret

def bucket_key_to_file_name(key):
    end_of_bucket = key.find('/')
    # key is like: ibm_vpc_flowlogs_v1/account=713c783d9a507a532834766793c37cc74/region=a/hour=20/stream-id=20210106T202552Z/00000000.gz
    part_str = key[end_of_bucket + 1:-3] # after the first / and not including the .gz
    parts = part_str.split('/')
    part_map = {}
    id = None
    for part in parts:
        left_right = part.split("=")
        if len(left_right) == 2:
            part_map[left_right[0]] = left_right[1]
        elif len(left_right) == 1:
            assert id == None
            id = part
        else:
            raise Exception("bad key")
    #return part_map["stream-id"]
    return id

def fetch_file(bucket, key, dir_path):
    all = set()
    if not dir_path.exists():
        dir_path.mkdir()
    f = bucket_key_to_file_name(key)
    if f in all:
        click.echo(f'duplicate file {f}')
    all = all | set(f)
    f_path = dir_path/f
    if f_path.exists():
        with f_path.open() as infile:
            contents = json.load(infile)
            if contents["key"] != key:
                click.echo("file content error, key provided not equal to key in previously fetched file")
                click.echo(f"key in file: {contents['key']}")
                click.echo(f"key:       : {key}")
            else:
                click.echo(f"skipping:{f}")

    else:
        json_path = str(f_path)
        raw_path = json_path + ".raw"
        try:
            log_command(['ibmcloud', 'cos', 'get-object', '--bucket', bucket, '--key', key, raw_path])
            with open(raw_path) as infile:
                contents = json.load(infile)
                contents["key"] = key
                with open(json_path, "w") as outfile:
                    json.dump(contents, outfile, indent=2)
        finally:
            Path(raw_path).unlink()
    
def fetch_cos_bucket_objects(bucket, dir_path, keys):
    for key in keys:
        fetch_file(bucket, key, dir_path)


def concat_downloaded(dir_path):
    all_file = dir_path/Path("all")
    with all_file.open(mode="w") as outfile:
        for f in dir_path.glob('[0-9]*'):
            with f.open() as infile:
                jf = json.load(infile)
                log_rows = lib.encode_log_rows(jf)
                for log_row in log_rows:
                    row_json = {**log_row, **{"file": str(f)}}
                    outfile.write(json.dumps(row_json) + "\n")

def get_start_millisec_timestamp(row):
    if start_time_str in row:
        start_time = row[start_time_str]
        if not start_time:
            start_time = row['connection_start_time']
        return int(utc_timestamp(datetime.datetime.fromisoformat(start_time[0:-1])) * 1000)
    else:
        click.echo(f"row does not have a {start_time_str}, row: {row}")
        return int(time.time() * 1000)

def sec_after_epoch_in_millisec(epoch):
    dt = datetime.datetime.fromtimestamp(epoch)
    sec_after_dt = datetime.datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, 1)
    return int(sec_after_dt.timestamp()) * 1000

def sec_after_current_minute_in_millisec():
    """Return the current millisec associated with the current time , but exactly 01 seconds after current minute"""
    return sec_after_epoch_in_millisec(time.time())

logdna_choice_1sec = '1sec'
def call_logdna(logdna_choice):
    if logdna_choice == logdna_choice_1sec:
        log = lib.get_logger(logdna_key(), logdna_ingestion_endpoint())
        timestamp = sec_after_current_minute_in_millisec()
        message = f"expected time: {datetime.datetime.fromtimestamp(timestamp/1000)}"
        opts = {"app": "simlogdna", "timestamp": timestamp}
        log.info(message, opts)
        return

def delete_key(bucket, key):
    log_command(['ibmcloud', 'cos', 'delete-object', '--bucket', bucket, '--key', key, "--force"])

async def delete_cos_bucket_contents(bucket):
    keys = get_keys(bucket)
    for key in keys:
        delete_key(bucket, key)

def keys_from_key_parameter(key_option):
    def is_int(s):
        try: 
            int(s)
            return True
        except ValueError:
            return False
    def key_key(cos_key):
        """convert a cos key name to a sort key string, a key looks a little like this:
        ibm_vpc_flowlogs_v0/99/us-south-2/crn:v1:bluemix:public:is:us-south:a/99::vpc:r006-9/crn:v1:bluemix:public:is:us-south-2:a/99::subnet:99/vnics/crn:v1:bluemix:public:is:us-south-2:a/99::instance:99/99/ingress/20200608T132243Z/00002630.gz
        """
        logdna_date_str = cos_key.split('/')[-2]
        return logdna_date_str

    if is_int(key_option):
        count = int(key_option)
        sorted_keys = sorted(get_keys(cos_bucket_name()), key=key_key)
        if count == -1:
            return sorted_keys
        return sorted_keys[-count:]

    if not "ibm_vpc_flowlogs" in key_option:
        # file name
        f_path = Path(key_option)
        with f_path.open() as infile:
            contents = json.load(infile)
            return [ contents["key"] ]
    return [ key_option ]

def call_main(keys):
    for key in keys:
        return lib.main({
            'bucket': cos_bucket_name(),
            'cosApiKey': cos_api_key(),
            'cosInstanceId': cos_instance_id(),
            'logdnaKey': logdna_key(),
            'logdnaIngestionEndpoint': logdna_ingestion_endpoint(),
            'endpoint': cos_endpoint(),
            'key': key,
        })


@click.command(help="Fetch and concatinate flow logs.  Set environment variables COS_BUCKET_NAME, COS_API_KEY, COS_INSTANCE_ID before using.")
@click.option("--keys", default=False, is_flag=True, help="list all of the keys in the bucket and exit")
@click.option("--fetch/--no-fetch", default=True, is_flag=True, help="fetch all of the flow logs from the bucket")
@click.option("--deleteallflowlogsincos", default=False, is_flag=True, help="Delete all of the flow logs in the COS bucket FOREVER")
@click.option("-d", "--directory", default="data", help="dir to store files")
@click.option("-b", "--bucket", help="bucket name will use environment variable COS_BUCKET_NAME if not supplied")
@click.option("--concat/--no-concat", default=True, help="concat all the downloaded files after fetching")
@click.option("-s", "--simulate", default=False, is_flag=True, help="simulate function call to main that is used for testing LogDNA integegration: set environment variables LOGDNAKEY, LOGDNA_INGESTION_ENDPOINT, COSENDPOINT")
@click.option("--key", default="", help="A number to specify how many keys from the sored list of all keys (default -1 means all), or a COS key, or a file that contains a json string with a 'key' key (.i.e path name to a previously fetched file like data/00001209)")
@click.option('--logdna', type=click.Choice([logdna_choice_1sec], case_sensitive=False), help="log to logdna, 1sec log hello to exactly 1 sec after the current time")
def cli(keys, fetch, deleteallflowlogsincos, directory, bucket, concat, simulate, key, logdna):
    dir_path = Path(directory)
    if simulate:
        if key == "":
            key = "-1"
        call_main(keys_from_key_parameter(key))
        return
    if logdna:
        call_logdna(logdna)
        return
    if not bucket:
        bucket = cos_bucket_name()
    if keys:
        click.echo("\n".join(get_keys(bucket)))
        return
    if deleteallflowlogsincos:
        delete_cos_bucket_contents(bucket)
    if fetch:
        if key == "":
            key = "-1"
        fetch_cos_bucket_objects(bucket, dir_path, keys_from_key_parameter(key))
    if concat:
        concat_downloaded(dir_path)
        return

