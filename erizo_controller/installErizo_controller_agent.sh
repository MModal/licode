#!/usr/bin/env bash
set -e

SCRIPT=`pwd`/$0
FILENAME=`basename $SCRIPT`
ROOT=`dirname $SCRIPT`
LICODE_ROOT="$ROOT"/..
CURRENT_DIR=`pwd`
NVM_CHECK="$LICODE_ROOT"/scripts/checkNvm.sh

. $NVM_CHECK

echo [erizo_controller_agent] Installing node_modules for erizo_agent

nvm use
npm install --loglevel error amqp aws-sdk log4js@1.0.1 node-getopt

echo [erizo_controller_agent] Done, node_modules installed
