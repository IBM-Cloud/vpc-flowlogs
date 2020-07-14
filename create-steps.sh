#!/bin/sh
set -ex

./000-prereqs.sh
./010-create-services.sh
./020-create-functions.sh
./030-create-vpc.sh
