#!/bin/bash
set -e

echo ">>> Targeting region $TF_VAR_region..."
ibmcloud target -r $TF_VAR_region

echo ">>> Targeting resource group $RESOURCE_GROUP_NAME..."
ibmcloud target -g $RESOURCE_GROUP_NAME

echo ">>> Targeting vpc generation 2..."
ibmcloud is target --gen 2

echo ">>> Verify the VPC ssh key exists..."
ibmcloud is keys --json | jq -e '.[] | select(.name=="'$TF_VAR_ssh_key_name'")' > /dev/null

echo ">>> Ensuring Cloud Object Storage plugin is installed"
if ibmcloud cos config list >/dev/null; then
  echo "cloud-object-storage plugin is OK"
  # clear any default crn as it could prevent COS calls to work
  ibmcloud cos config crn --crn "" --force
else
  echo "Make sure cloud-object-storage plugin is properly installed with ibmcloud plugin install cloud-object-storage."
  exit 1
fi

echo ">>> Ensuring Code Engine plugin is installed"
if ibmcloud ce project list >/dev/null; then
  echo "code-engine plugin is OK"
else
  echo "Make sure code-engine plugin is properly installed with ibmcloud plugin install cloud-functions."
  exit 1
fi

echo TODO
echo ">>> Ensuring Schematics plugin is installed"
if ibmcloud schematics workspace list >/dev/null; then
  echo "schematics plugin is OK"
else
  echo "Make sure schematics plugin is properly installed with ibmcloud plugin install schematics."
  exit 1
fi

echo ">>> Ensuring flowlogs are installed and working"
if ibmcloud is flow-logs > /dev/null; then
  echo "flow logs are available"
else
  echo "Make sure flow logs are available in your account."
  exit 1
fi

echo ">>> Is jq (https://stedolan.github.io/jq/) installed?"
jq -V

echo ">>> Looking for plugin updates"""
plugins_that_need_update=$(ibmcloud plugin list --output json | jq '[.[]|select(.Status=="Update Available")]|length')
if [ $plugins_that_need_update -gt 0 ]; then
  ibmcloud plugin list
  echo
  echo "WARNING $plugins_that_need_update plugins need updating.  Update them by executing:"
  echo ibmcloud plugin update --all
fi
