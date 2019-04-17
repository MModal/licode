#!/usr/bin/env bash

set -e

echo "Starting the erizo client build"

ROOT=/opt/licode
BUILD_DIR=$ROOT/build
SCRIPT=$ROOT/scripts
NVM_CHECK=$SCRIPT/checkNvm.sh
LIB_DIR=$BUILD_DIR/libdeps
CURRENT_DIR=`pwd`

install_nvm_node() {
  if [ -d $LIB_DIR ]; then
    export NVM_DIR=$(readlink -f "$LIB_DIR/nvm")
    if [ ! -s "$NVM_DIR/nvm.sh" ]; then
      if [ ! -d $NVM_DIR ]; then
        mkdir -p $NVM_DIR
      fi
      curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash
      cd "$SCRIPT"
    fi
    . $NVM_CHECK
    nvm install
  else
    mkdir -p $LIB_DIR
    install_nvm_node
  fi
}

install_nvm_node
nvm use

npm install
npm install -g gulp-cli@2.0.0 node-gyp@3.6.2

cd $ROOT/erizo_controller/erizoClient/

echo "I am in `pwd`"

npm install gulp@3.9.1 run-sequence@2.2.0 del@3.0.0 gulp-sourcemaps@2.6.3 gulp-eslint@3.0.1 google-closure-compiler-js@20171203.0.0 webpack@3.10.0 webpack-stream@4.0.0 script-loader@0.7.2 expose-loader@0.7.4

gulp erizo

cd $SCRIPT/erizoClient

VERSIONVAL=`cat version`
echo "My version is $VERSIONVAL"
sed -i -e 's/__version__/'"$VERSIONVAL"'/g' bower.json

cp ../../erizo_controller/erizoClient/dist/debug/erizo/erizo.js .

tar -czvf erizo-$VERSIONVAL.tgz bower.json erizo.js

curl -XPUT https://artifactory-pit.mmodal-npd.com/artifactory/internal-bower-pit/ffs/erizo/ -T erizo-$VERSIONVAL.tgz
