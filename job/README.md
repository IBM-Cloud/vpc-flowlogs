# Questions
- Send log lines to logdna as a dictionary?
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


