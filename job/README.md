# Job
FLowlogs are put into a bucket.  This is code that will read the objects from a bucket and push them to flowlogs.

The code can be packaged into a code engine job and the job envoked through a COS subscription.  The job will be invoked each time a new object is added to the bucket.

- flowlog.py - parses the environment and then calls lib.py to do the work.
- lib.py - COS object reading and log line creation
- logdna_synchronous.py - write to logdna with retry.
- test_flowlog_to_logdna.py - tester.  Takes an ini file as input.


# Modes
- simple push one object or push all objects
- remember - push one object and remember the first one pushed.  Push all objects older then the first object pushed.  Remember has not been well tested
- catch up - not implemented

Currently using the simple mode.  When invoked with no CE_DATA (Code Engine data) environment variable, all objects will be pushed.  CE_DATA will be initialized with the bucket and object and envoked as a code engine job if the job is subscribed to a COS bucket in a code engine project.

# Remember
Not well tested:

Assumed to be invokd by Subscription every few minutes.  A STATE object is used to hold the key of the first processed key.

Subscription:
- If STATE does not exist
  - create STATE containing key of the object being processed

All:
- for each key in bucket_list
  - if newer then the STATE key remove from bucket_list
- for each key in sorted(bucket_list):
  - log key

## Alternative catch up
Not implemented

Assumed to be invoked every few minutes.  A STATE object is used to hold the key of the first processed key.
Subscription:
- If STATE does not exist
  - create STATE 
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
