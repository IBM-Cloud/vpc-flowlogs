
#!/bin/bash
set -e

## Create the resources for a code engine, ce, processor of the COS bucket:
# ce project and job
# 

success=false
trap check_finish EXIT
check_finish() {
  if [ $success = true ]; then
    echo '>>>' success
  else
    echo "FAILED"
  fi
}

source code_engine_config.sh
source code_engine_more_config.sh

python_ini="python.ini"

secrets=$(ibmcloud ce secret get  -n $secret_for_apikey_name --decode)
apikey=$(grep 'APIKEY:' <<< "$secrets" | cut -d ' ' -f 2 -)
logdna_ingestion_key=$(grep 'LOGDNA_INGESTION_KEY:' <<< "$secrets" | cut -d ' ' -f 2 -)

rm -f $python_ini
echo '[env]' > $python_ini
echo "apikey=$apikey" >> $python_ini
echo "logdna_ingestion_key=$logdna_ingestion_key" >> $python_ini
ibmcloud ce configmap get --name $ce_configmap_name --output json | jq -r '.data | to_entries[] | "\(.key)=\(.value)"' >> $python_ini

echo '>>> NOTE python.ini has secrets!!! ready to debug using python.ini'

success=true