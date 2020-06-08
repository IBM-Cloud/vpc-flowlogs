#!/bin/bash
set -ex
pip install virtualenv
virtualenv virtualenv
source virtualenv/bin/activate
pip install -r requirements_main.txt
