#!/usr/bin/env bash

ROOT=/opt/licode
SCRIPTS=$ROOT/scripts

run_nvm() {
  echo "Running NVM"
  . $ROOT/build/libdeps/nvm/nvm.sh
}

run_nuve() {
  echo "Starting nuve"
  cd $ROOT/nuve/nuveAPI
  node nuve.js &
}

echo "Running as `id -u -n`"

cd $SCRIPTS

run_nvm
nvm use

run_nuve
wait

while [ : ]
do
    echo "Will sleep"
    sleep 100000
done

