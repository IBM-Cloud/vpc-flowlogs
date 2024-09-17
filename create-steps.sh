#!/bin/sh
set -ex

./000-demo-prerequisites.sh
./010-create-services.sh
./020-create-functions.sh
./030-create-vpc.sh
./035-flow-log-create.sh
