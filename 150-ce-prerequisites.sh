#!/bin/bash
set -e

echo ">>> ibmcloud"
ibmcloud version

echo ">>> ibmcloud ce plugin"
ibmcloud ce

echo ">>> ibmcloud logging plugin"
ibmcloud logging

echo ">>> Looking for plugin updates"""
plugins_that_need_update=$(ibmcloud plugin list --output json | jq '[.[]|select(.Status=="Update Available")]|length')
if [ $plugins_that_need_update -gt 0 ]; then
  ibmcloud plugin list
  echo
  echo "WARNING $plugins_that_need_update plugins need updating.  Update them by executing:"
  echo ibmcloud plugin update --all
fi

echo ">>> Is jq (https://stedolan.github.io/jq/) installed?"
jq -V
