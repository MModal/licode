#!/usr/bin/env bash

set -e

SCRIPT=`pwd`/$0
FILENAME=`basename $SCRIPT`
PATHNAME=`dirname $SCRIPT`
ROOT=$PATHNAME/..
NVM_CHECK="$ROOT"/scripts/checkNvm.sh
BUILD_DIR=$ROOT/build
CURRENT_DIR=`pwd`
DB_DIR="$BUILD_DIR"/db

. $NVM_CHECK

cd $PATHNAME

cd nuveAPI

echo [nuve] Installing node_modules for nuve

nvm use
npm install --loglevel error amqp express mongojs aws-sdk log4js@1.0.1 node-getopt body-parser
echo [nuve] Done, node_modules installed

cd $CURRENT_DIR
