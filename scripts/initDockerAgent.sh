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
  #use the Secrets manager key name to get secrets
  python3 configs.py "$@"
  deactivate
  cd $ROOT/scripts
}

cd $ROOT/scripts

setup_config

run_nvm
nvm use

run_erizoAgent
wait


while [ : ]
do
    echo "Will sleep"
    sleep 100000
done

