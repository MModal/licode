#!/usr/bin/env bash

export ERIZO_ROOT=$LICODE_HOME/erizo
export ERIZO_HOME=$ERIZO_ROOT/
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$ERIZO_ROOT/build/erizo:$ERIZO_ROOT:$LICODE_HOME/build/libdeps/build/lib

. $LICODE_HOME/scripts/checkNvm.sh
cd $LICODE_HOME/erizo_controller/erizoAgent
nvm use
node erizoAgent.js