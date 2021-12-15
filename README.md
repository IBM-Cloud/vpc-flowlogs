# Analyze VPC Flow Logs

[Flow logs for VPC](https://cloud.ibm.com/vpc-ext/network/flowLogs/vpc) persists a digest of network traffic in a Virtual Private Clouds, VPC in a Cloud Object Storage (COS) bucket.

[Code Engine](https://cloud.ibm.com/codeengine/overview) can be extended by [integrating with Cloud Object Storage (COS)](https://cloud.ibm.com/docs/codeengine?topic=codeengine-subscribe-cos-tutorial). The COS trigger type lets you run custom code logic when a new object is stored, updated, or deleted from a designated bucket in COS. 

This project shows how use a trigger function to read a flow log COS object and write it to [IBM log analysis](https://cloud.ibm.com/observe/logging).

![create flow](./xdocs/vpc-flow-log.png)

1. The Flow logs for VPC are written to a COS bucket.
1. Cloud Object Storage sends an event to Cloud Engine.
1. This event triggers a code engine execution to read the bucket and write log entries.

## Create a vpc with flow logs enabled
If you do not have a vpc then use the following mechansim to create a demo vpc and **code_engine_config.sh** file
```
# create a demo.env file with some terraform variables
cp template.demo.env demo.env
# read the comments in the file and configure variables to suit your taste
edit demo.env
# execute terraform and create a code_engine_config.sh file
ibmcloud login
100-demo-vpc-and-flowlog-bucket-create.sh;
# take a look at the code_engine_config.sh file
cat code_engine_config.sh
```

If you already have a vpc make make sure that it has been configured with flowlogs and you know the details of the bucket containing the flowlogs.  Create the **code_engine_config.sh** file with your fingers:
```
cp template.code_engine_config.sh code_engine_config.sh
# read the comments in the file and configure variables to match your COS configuration
edit code_engine_config.sh
```

The file **code_engine_more_config.sh** has a few more configuration variables that you will probably not need to change.  Open the file in an editor and verify.

## Create code engine project, job, ...
The script 200-create-ce-project-logging-and-keys.sh will create the code engine project, job, environment variables for the job and secrets for the job based on the contents of the two files created in the previous step:
- code_engine_config.sh
- code_engine_more_config.sh

```
ibmcloud login
./200-create-ce-project-logging-and-keys.sh
```

## Debug the python program on your desktop
Optionally debug the python program on your desktop.

The python scripts in the job/ directory require some configuration variables.  The script below will create the python.ini file:

```
./300-python-debug-config.sh
```

Set up your python 3.9 environment.  I use a virtual python environment on my laptop.

```
$ python --version
Python 3.9.6
```

```
cd job
pip install --no-cache-dir -r requirements.txt
pip install --no-cache-dir -r requirements-dev.txt
```

The python script **./test_flowlog_to_logdna.py** can be executed to find a key in the cos bucket and send it to logdna.


## Create a docker image
Optionally create a docker image on your desktop and push it to docker hub.  Feel free to use the one configured in **code_engine_more_config.sh** :

Work in the **job/** directory:

```
cd job
```

Code engine scripts use the configuration file
```
$ grep DOCKER  ../code_engine_more_config.sh
export DOCKER_IMAGE=powellquiring/flowlog:1.1
```

You must use your own docker repository in docker hub. Change the environment variable in the file and export it into your environment:
```
edit ../code_engine_more_config.sh; # change DOCKER_IMAGE=YourRepository/flowlog:1.0
export DOCKER_IMAGE=YourRepository/flowlog:1.0
```

A makefile will build it for you, if you do not have make available type the commands in the Makefile with your fingers.
```
make docker-build
make docker-push
```

## Create job

The code engine project was created earlier and now the job can be created.
```
./400-job-create.sh
```

Optionally check out the **job** in the IBM cloud console in the [Code Engine Projects](https://cloud.ibm.com/codeengine/projects)
- Click on your project to open it up.  Notice the **Secrets and Configmaps** tab and the **Jobs** tab
- Click on the **Jobs** tab
- Click on your job

You can skip this step, but if you submit the job all of the VPC flow log objects in the bucket will be written to the Logging instance.  This has been tested with a few thousand, but you could have more if you have been accumulating them for a few days.  

## Subscribe to COS bucket

To capture all flowlogs as they are written to the bucket, subscribe the job to COS bucket events.  The subscription will call the job each time flowlog puts an object into the bucket
```
./500-subscription-create.sh
```

In the ibm cloud console visit [Observability Logging](https://cloud.ibm.com/observe/logging) and click on your loggin instance. Then click on **Open Dashboard** to open the actual logs.  You should start to see VPC flow logs in about 10 minutes.

## Troubleshoot

If your Logging instance does not have flow log entries verify that you have opened the logging instance in the region configured with the name matching the one in **code_engine_more_config.sh**: LOGDNA_REGION, logdna_service_name.

To troubleshoot problems start in the IBM cloud console in the [Code Engine Projects](https://cloud.ibm.com/codeengine/projects)
- Click on your project to open it up.  Notice the **Secrets and Configmaps** tab and the **Jobs** tab
- Click on the **Jobs** tab
- Click on your job
- You should see some jobs in the **Job runs** tab.  The subscription is starting a job each time an object file is put into the bucket
- In the logs check out the table:
  - Configmap reference - click on the **Configmap** link and look at the environment variables that will be set in the job run
  - Secret reference - click on the **Secret** link and verify
    - LOGDNA_INGESTION_KEY - Open the Logging instance, click **Actions**, click **view Ingestion key**, verify the Ingestion Keys match.
    - APIKEY - In a terminal window using the APIKEY secret and variables from the Configmap verify that the APIKEY has access to the bucket and objects:
      - ibmcloud login --apikey APIKEY
      - ibmcloud cos config crn --crn COS_CRN
      - ibmcloud cos objects --bucket COS_BUCKET
      - ibmcloud cos get-object --bucket COS_BUCKET --key key_from_previous_command
      - do not forget to restore your normal login!
  - CE_DATA.  Verify the keys "bucket" and "key" are visible.
- click on the **Launch logging** button and the IBM logging environment will be opened and at the bottom you will notice it is filtered specifically for the log entries printed by the python program.  This may be enough to pin point the problem.
- You can get more logs by enabling LOG/DEBUG.  Back in your Code Engine Project click the **Secrets and Configmaps** tab, click on your configmap, click **Add key-value pair** and add LOG/DEBUG for the Key/Value and click **Save**.
- The next job will have more logging info
- You should be able to track back to the python program in the **job/** folder for problems.   You can run the python program on your laptop using the instructions above.
- You can add more logging to the python files test it locally and then follow the instructions above to make a docker image.  After pushing the docker image execute ./400-job-create.sh
- 


## Clean up
To destroy the code engine project, the logging instance, service id and authorization:
```
./800-cleanup-code-engine.sh
```

If you created the demo VPC, COS instance and bucket:
```
./900-cleanup-demo.sh
```