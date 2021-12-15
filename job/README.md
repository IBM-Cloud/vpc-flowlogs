# Job
FLowlogs are put into a bucket.  This is code that will read the objects from a bucket and push them to flowlogs.

The code can be packaged into a code engine job and the job envoked through a COS subscription.  The job will be invoked each time a new object is added to the bucket.

# Modes
- simple push one object to logdna
- all - push all objects to logdna
- one - push one object to logdna
- catchup - create and use an object in the COS bucket to push all of the objects over multiple iterations.  Keep in mind that more flowlogs are being delivered and this process could take a while.

By default when invoked via code engine it is in catchup mode.

## Simple


todo:
- [ ] Use direct endpoints in COS https://ibm-cloudplatform.slack.com/archives/CPH7ES7PT/p1635358860081500?thread_ts=1635358715.081400&cid=CPH7ES7PT

## Catchup mode
Assumed to be invoked every few minutes.  A STATE file is used to track progress.  Algorithm:
- If STATE does not exist
  - create STATE status=working
  - not_caught_up = True
  - while not_caught_up:
    - not_caught_up = False
    - for each object get_objects
      - if object not pushed:
        - push object to logdna
        - not_caught_up = True
  - create STATE status=finished
- else read STATE file.  status:
  - working - exit
  - finished - push object to logdna

If catchup fails start over with new logdna instance.

# Questions
- Can the timestamp in logdna be replaced by a time stamp on the flow log entry?

Commands:
- sendall - send all files in bucket to logdna
- sendone - send one file in bucket to logdna
- pull


# OLD Packaging
See https://cloud.ibm.com/docs/openwhisk?topic=openwhisk-prep#prep_python_local_virtenv

zipit.sh will create a log.zip file containing the cloud function action and dependencies.  It avoids installing virtualenv into your primary shell by using docker.  If you dont have docker perofrm the steps in these shell scripts
```
./zipit.sh
```

The test environment requires some additional setup and some additional python requirements:
```
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_full.txt
pip install -r requirements_main.txt
```

The cli tool is also handy for testing the __main__ script but also for downloading the flowlog files from cos and having a look at them.  The 020-create-functions.sh will create a actions/local.env.  Source this file to run the ./cli.py.

Run `./cli.py --help` to see all the stuff the command can do.  Examples:
- `./cli.py ` fetch all cos objects into /data and concatinate all of them into flow log lines in the file **all** (format of all is the same as LogDNA lines)
- `./cli.py --key 2` fetch only the latest 2 cos objects into /data and concatinate all of them into flow log lines in the file **all** (format of all is the same as LogDNA lines)
- `./cli.py --deleteallflowlogsincos` delete all the objects from the bucket, forever
- `./cli.py --simulate --key bucketkey` call the code that the cloud function calls to send a log to log dna, notice the extra environment variables required
- `./cli.py --simulate --key 1` just send the latest one (it might be empty) use 2 to send 2 etc  
- `./cli.py --simulate` call the code that the cloud function calls to send all logs to logdna (could take a while)


