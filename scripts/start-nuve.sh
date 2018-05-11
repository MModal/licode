#!/usr/bin/env bash

. ${LICODE_HOME}/scripts/checkNvm.sh
cd ${LICODE_HOME}/nuve/nuveAPI
echo "will run nvm"
nvm use
echo "will start nuve"
node nuve.js