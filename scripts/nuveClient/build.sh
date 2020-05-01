#!/usr/bin/env bash

set -e

cd ./nuve/nuveClient/tools

./compile.sh

cd ../node

cp ../dist/nuve.js ./nuve.js

npm publish
