#!/bin/bash
set -e
python3 -m venv venv
source venv/bin/activate
pip install virtualenv
virtualenv virtualenv
source virtualenv/bin/activate
pip install -r requirements_main.txt
