# Packaging python code with a local virtual environment
See https://cloud.ibm.com/docs/openwhisk?topic=openwhisk-prep#prep_python_local_virtenv

zipit.sh will create a log.zip file containing the cloud function action and dependencies.  It avoids installing virtualenv into your primary shell by using docker.  If you dont have docker perofrm the steps in these shell scripts
```
./zipit.sh
```

The test environment requires some additional requirements:
```
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_full.txt
pip install -r requirements_main.txt
```

The cli tool is also handy for testing the __main__ script but also for downloading the flowlog files from cos and having a look at them.  You must fir


