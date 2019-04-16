#!/usr/bin/env bash

ROOT=/opt/licode
SCRIPTS="$ROOT"/scripts
NVM_CHECK="$ROOT"/scripts/checkNvm.sh

run_nvm() {
  echo "Running NVM"
  . $ROOT/build/libdeps/nvm/nvm.sh
}

run_erizoAgent() {
  echo "Starting erizoAgent"
  cd $ROOT/erizo_controller/erizoAgent
  node erizoAgent.js &
}

echo "Running as `id -u -n`"

cd $ROOT/scripts

run_nvm
nvm use

run_erizoAgent
wait
