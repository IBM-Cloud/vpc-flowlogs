#!/bin/bash

# Shared functions

cos_global_variables(){
  COS_CRN=$(echo $COS_BUCKET_CRN | sed 's/\(.*\):[^:]*:[^:]*:[^:]*/\1/')::
  COS_GUID=$(echo $COS_BUCKET_CRN | sed 's/.*:\([^:]*\):[^:]*:[^:]*/\1/')
  bucket=$(echo $COS_BUCKET_CRN | sed 's/.*:[^:]*:\([^:]*\):[^:]*/\1/')
  COS_BUCKET=$(echo $COS_BUCKET_CRN | sed 's/.*:[^:]*:[^:]*:\([^:]*\)/\1/')
  if [ x$bucket != xbucket ]; then
    echo "*** error parsing the COS_BUCKET_CRN:$COS_BUCKET_CRN"
    exit 1
  fi
}