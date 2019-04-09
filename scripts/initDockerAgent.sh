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

setup_config() {
  echo "Setting up config"
  cd $SCRIPTS/config_update
  source env/bin/activate
  python3 configs.py stable/scribe/licode/agent
  deactivate
  cd $ROOT/scripts
}

cd $ROOT/scripts

setup_config

run_nvm
nvm use

run_erizoAgent
wait
