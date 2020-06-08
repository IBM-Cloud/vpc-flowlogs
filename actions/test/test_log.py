import pytest
import lib
import cli
import click
import logging
import time
import datetime
from pathlib import Path
import gzip
import json

date_str = "2020-06-05T19:12:43Z"
date_millisec = 1591384363000
date_str_sec_after = "2020-06-05T19:12:01Z"

def test_logdna_millisec_timestamp():
    global date_str
    assert lib.logdna_millisec_timestamp(date_str) == date_millisec

def test_sec_after_epoch_in_millisec():
    milli0 = cli.sec_after_epoch_in_millisec(int(date_millisec/1000))
    milli1 = lib.logdna_millisec_timestamp(date_str_sec_after)
    assert milli0 == milli1

def path_to_example_flow_log_file(file_name_in_cwd):
    return Path(__file__).parent / Path(file_name_in_cwd)

def test_log_from_gz_and_timestamp_from_row():
    with path_to_example_flow_log_file('00000911.gz').open('rb') as gz:
        rows = lib.rows_from_gz_flowlog_stream(gz, "00000911")
        assert rows[0]["start_time"] == "2020-06-04T13:43:10Z"
        assert lib.get_start_millisec_timestamp(rows[0]) == lib.logdna_millisec_timestamp('2020-06-04T13:43:10Z')
        assert rows[1]["start_time"] == ""
        assert rows[1]["capture_start_time"] != ""
        assert lib.get_start_millisec_timestamp(rows[1]) == lib.logdna_millisec_timestamp(rows[1]["capture_start_time"])

example_cos_key = "ibm_vpc_flowlogs_v0/713c783d9a507a53135fe6793c37cc74/us-south-2/crn:v1:bluemix:public:is:us-south:a/713c783d9a507a53135fe6793c37cc74::vpc:r006-fc3e66f3-2a98-4bd2-800a-1b4a971f3b78/crn:v1:bluemix:public:is:us-south-2:a/713c783d9a507a53135fe6793c37cc74::subnet:0727-dd02b849-a804-4b5b-8456-7df33e311686/vnics/crn:v1:bluemix:public:is:us-south-2:a/713c783d9a507a53135fe6793c37cc74::instance:0727_7ccdd393-23a1-40f9-89bf-0a5b0a50ac0e/0727-c88727bc-345d-4ef0-b7a7-a3ae23ffdaeb/egress/20200608T144744Z/00002665.gz"
def test_latest_key():
    assert cli.keys_from_key_parameter(example_cos_key) == [ example_cos_key ]
    assert cli.keys_from_key_parameter(str(path_to_example_flow_log_file('00002630'))) == [ 'ibm_vpc_flowlogs_v0/713c783d9a507a53135fe6793c37cc74/us-south-2/crn:v1:bluemix:public:is:us-south:a/713c783d9a507a53135fe6793c37cc74::vpc:r006-fc3e66f3-2a98-4bd2-800a-1b4a971f3b78/crn:v1:bluemix:public:is:us-south-2:a/713c783d9a507a53135fe6793c37cc74::subnet:0727-dd02b849-a804-4b5b-8456-7df33e311686/vnics/crn:v1:bluemix:public:is:us-south-2:a/713c783d9a507a53135fe6793c37cc74::instance:0727_7ccdd393-23a1-40f9-89bf-0a5b0a50ac0e/0727-c88727bc-345d-4ef0-b7a7-a3ae23ffdaeb/ingress/20200608T132243Z/00002630.gz' ]
    keys = cli.keys_from_key_parameter(2)
    assert len(keys) == 2
    print(keys)

