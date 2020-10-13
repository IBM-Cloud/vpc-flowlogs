#!/bin/bash
set -e
pip3 install virtualenv
virtualenv virtualenv
source virtualenv/bin/activate
pip install -r requirements_main.txt
