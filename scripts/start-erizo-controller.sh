#!/usr/bin/env bash

. $LICODE_HOME/scripts/checkNvm.sh
cd $LICODE_HOME/erizo_controller/erizoController
# Curious why this is needed, initLicode script had it. Maybe to give nuve to finish some init asynchronously?
sleep 5
node erizoController.js