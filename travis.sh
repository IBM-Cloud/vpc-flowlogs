#!/bin/bash
set -ex
set -o pipefail
source demo.env

./000-demo-prerequisites.sh
./100-demo-vpc-and-flowlog-bucket-create.sh
./150-ce-prerequisites.sh
./200-create-ce-project-logging-and-keys.sh
#./800-cleanup-code-engine.sh
#./900-cleanup-demo.sh

