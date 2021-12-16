# Analyze VPC Flow Logs

[Flow logs for VPC](https://cloud.ibm.com/vpc-ext/network/flowLogs/vpc) persists a digest of network traffic in a Virtual Private Clouds (VPC) in a Cloud Object Storage (COS) bucket.

[Code Engine](https://cloud.ibm.com/codeengine/overview) can be extended by [integrating with Cloud Object Storage (COS)](https://cloud.ibm.com/docs/codeengine?topic=codeengine-subscribe-cos-tutorial). The COS trigger type lets you run custom code logic when a new object is stored, updated, or deleted from a designated bucket in COS. 

This project shows how use a Code Engine notification to start the excecution of a Code Engine job which will read a flow log COS object and write it to [IBM log analysis](https://cloud.ibm.com/observe/logging).

![create flow](./drawio/flowlog-to-logdna.png)

1. The Flow logs for VPC are written to a COS bucket.
1. Cloud Object Storage works with Code Engine to execute the job.
1. Job reads the COS bucket object using an apikey for authorization
1. Job writes the log entries

## Create demo VPC, COS bucket and logdna
If you do not have a vpc use the scripts below to create a vpc, COS bucket, logging service instance.  The script also creates a **code_engine_config.sh** file.

```
# create a demo.env file with some terraform variables tht suite your taste
cp template.demo.env demo.env
edit demo.env
source demo.env

# verify prerequisites
000-demo-prerequisites.sh;

# execute terraform and create a code_engine_config.sh file
100-demo-vpc-and-flowlog-bucket-create.sh;

# take a look at the code_engine_config.sh file and note that it contains a logdna ingestion key secret - keep the file safe
cat code_engine_config.sh
```

## Configure your existing VPC, COS bucket and Logging
If you already have a vpc make make sure that it has been configured with flowlogs and you know the details of the bucket containing the flowlogs, and a Logging service instance and ingestion key.

To find the bucket navigate to the [Resources view](https://cloud.ibm.com/resources) and in the **Storage** section open your Cloud Object Storage instance.  Open the **Bucket** and then open the **Configuration** and find the **Direct** endpoint and the **Bucket instance CRN**

To find the LOGDNA constants visit [Observability Logging](https://cloud.ibm.com/observe/logging) and click on your logging instance.  The region is a string like "us-south". Click **Actions**, click **view Ingestion key**

Create the **code_engine_config.sh** file with your fingers:
```
# read the comments in the file and configure variables to match your COS bucket and logdna configuration
cp template.code_engine_config.sh code_engine_config.sh
edit code_engine_config.sh
```

The file **code_engine_more_config.sh** has a few more configuration variables that you likely not need to change.  Open the file in an editor and verify.

## Create code engine related resources
The script 200-create-ce-project-logging-and-keys.sh will create resources as shown in the diagram above:
- IAM service ID allowing access to COS and associated apikey
- code engine project
- code engine config map passed as environment variables to the job
- code engine secrets for apikey and logdna ingestion key passed as environment variables to the job
- service authorization allowing flow logs to write to a COS bucket. 
- code engine job
- code engine subscription from the COS bucket to the job

All this was configured based on the contents of the two files:
- code_engine_config.sh
- code_engine_more_config.sh

If you want to walk more slowly through the source code or make your own Docker image go to **Development** below.  Otherwise continue:
```
ibmcloud login
./150-ce-prerequsites
./200-create-ce-project-logging-and-keys.sh
```

## Observe the logs
In the ibm cloud console visit [Observability Logging](https://cloud.ibm.com/observe/logging) and click on your logging instance. Then click on **Open Dashboard** to open the actual logs.  You should start to see VPC flow logs in about 10 minutes.

If you do not see the logs check out **Troubleshooting** below

## Clean up
To destroy the code engine project, the logging instance, service id and authorization:
```
./800-cleanup-code-engine.sh
```

If you created the demo VPC, COS instance and bucket:
```
./900-cleanup-demo.sh
```

# Development
This section is for those that want to dig deeper into the source code or debug
## Debug the python program on your desktop
The python scripts in the job/ directory require some configuration variables.  The scripts below will create the code engine project but not the code engine job.  The code engine configmap and secrets will also be created and are needed to test the python code.

```
./150-ce-prerequsites
./200-create-ce-project-logging-and-keys.sh basics; # project, configmap and secrets
./300-python-debug-config.sh; # make python.ini with configuration including secrets for running locally
```

Set up your python 3.9 environment.  I use a virtual python environment on my laptop.

```
$ python --version
Python 3.9.6
```

Python source code is in the job/ directory
```
cd job
pip install --no-cache-dir -r requirements.txt
```

The python script **./test_flowlog_to_logdna.py** can be executed to find a key in the cos bucket and send it to logdna.  You can make some changes to this file to test different scenarios.

## Create a docker image
The docker image on your desktop and push it to docker hub.

Work in the **job/** directory:
```
cd job
```

Code engine scripts use the configuration file
```
$ grep DOCKER  ../code_engine_more_config.sh
export DOCKER_IMAGE=powellquiring/flowlog:1.1
todo sample-flowlog-logdna
```

You must use your own docker repository in docker hub. Change the environment variable in the file and export it into your environment:
```
# change DOCKER_IMAGE=YourRepository/flowlog:1.0
edit ../code_engine_more_config.sh;

# actually export it into your current shell environment to allow the Makefile to work
export DOCKER_IMAGE=YourRepository/flowlog:1.0
```

A makefile will build it for you, if you do not have make available type the commands in the Makefile with your fingers.
```
make docker-build
make docker-push
```

Deploy using your own docker image.  The script is smart enough to use the resources that were created earlier if they exist:
```
./150-ce-prerequsites
./200-create-ce-project-logging-and-keys.sh
```

## Log existing flow logs
This section explains how to send the objects previously created to logdna.  The steps above log the new flow logs as they are written, but you may have a bucket full of old flow logs that you want to analize.

Create the basic code engine project and environment then create a job:
```
./150-ce-prerequsites
./200-create-ce-project-logging-and-keys.sh basic
./200-create-ce-project-logging-and-keys.sh job
```

Check out the **job** in the IBM cloud console in the [Code Engine Projects](https://cloud.ibm.com/codeengine/projects)
- Click on your project to open it up.  Notice the **Secrets and Configmaps** tab and the **Jobs** tab
- Click on the **Jobs** tab
- Click on your job
if you submit the job all of the VPC flow log objects in the bucket will be written to the Logging instance.  This has been tested with a few thousand, but you could have more if you have been accumulating them for a few days.  

Before creating the job it can be helpful to deploy a platform logging instance in the same region as the code engine job.

## Subscribe to COS bucket

After completing the previous step to capture the existing flow logs turn on subscriptions to get the new ones.

The subscription will call the job each time flowlog puts an object into the bucket:
```
./200-create-ce-project-logging-and-keys.sh job subscription
```


# Troubleshooting

To troubleshoot problems start in the IBM cloud console in the [Code Engine Projects](https://cloud.ibm.com/codeengine/projects)
- Click on your project to open it up.  Notice the **Secrets and Configmaps** tab and the **Jobs** tab
- Click on the **Jobs** tab
- Click on your job
- You should see some jobs in the **Job runs** tab.  The subscription is starting a job each time an object file is put into the bucket
- In the logs check out the table:
  - Configmap reference - click on the **Configmap** link and look at the environment variables that will be set in the job run
  - Secret reference - click on the **Secret** link and verify
    - LOGDNA_INGESTION_KEY - Open the Logging instance, click **Actions**, click **view Ingestion key**, verify the Ingestion Keys match.
    - Verify the LOGDNA_REGION matches the region of the logging instance
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

