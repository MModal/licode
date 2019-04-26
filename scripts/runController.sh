#!/usr/bin/env bash

ROOT=/opt/licode
SCRIPTS="$ROOT"/scripts
NVM_CHECK="$ROOT"/scripts/checkNvm.sh

run_nvm() {
  echo "Running NVM"
  . $ROOT/build/libdeps/nvm/nvm.sh
}

run_erizoController() {
  echo "Starting erizoController"
  cd $ROOT/erizoController
  node erizoController.js &
}

echo "Running as `id -u -n`"

cd $ROOT/scripts

run_nvm
nvm use

run_erizoController
wait
