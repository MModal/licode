#!/usr/bin/env bash

set -e

npm install --save-dev google-closure-compiler-js@20171203.0.0

cd ./tools

./compile.sh

cd ..

cp ./dist/nuve.js ./nuve.js

npm publish
