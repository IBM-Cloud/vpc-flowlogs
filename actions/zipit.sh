#/bin/bash
set -ex
if [ ! -d virtualenv ]; then
  docker run -it --rm --name my-running-script -v "$PWD":/usr/src/myapp -w /usr/src/myapp python:3.7 bash virtualenv-createusingdocker.sh
fi
zip -r log.zip virtualenv __main__.py lib
