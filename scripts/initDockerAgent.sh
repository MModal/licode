#!/usr/bin/env bash
ROOT=/opt/licode
SCRIPTS="$ROOT"/scripts

setup_config() {
  echo "Setting up config with " $*
  cd $SCRIPTS/config_update
  source env/bin/activate
  #use the Secrets manager key name to get secrets
  python3 configs.py $*
  deactivate
  cd $ROOT/scripts
}

cd $ROOT/scripts

setup_config $*

su -c "$SCRIPTS/runAgent.sh" -s /bin/sh nobody