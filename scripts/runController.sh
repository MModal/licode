#!/usr/bin/env bash

ROOT=/opt/licode
SCRIPTS=$ROOT/scripts

run_nvm() {
  echo "Running NVM"
  . $ROOT/build/libdeps/nvm/nvm.sh
}

run_erizoController() {
  echo "Starting erizoController"
  cd $ROOT/erizo_controller/erizoController
  node erizoController.js &
}

echo "Running as `id -u -n`"

cd $SCRIPTS

run_nvm
nvm use

run_erizoController
wait
