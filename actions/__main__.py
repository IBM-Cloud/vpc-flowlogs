#!/usr/bin/env python
import lib

def main(params):
    lib.main(params)
    return lib.main(params)

if __name__ == "__main__":
    # Use this for manual testing as a last resort.  See the README.md file for a better way to use the cli.py command
    main({
            'bucket': "bucket name",
            'cosApiKey': "cos api key",
            'cosInstanceId': "cos instance id",
            'logdnaKey': "logdna ingestion key",
            'logdnaIngestionEndpoint': "logdna ingestion endpoint like https://logs.us-south.logging.cloud.ibm.com",
            'endpoint': "cos regional endpoint like s3.us-south.cloud-object-storage.appdomain.cloud",
            'key': "cos key for a flow log object",
        })
