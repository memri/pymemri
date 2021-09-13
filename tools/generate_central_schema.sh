#!/bin/bash

SCHEMA_REPO="https://gitlab.memri.io/memri/schema.git"
BRANCH="python-converter"
OUT_DIR="$(pwd)/pymemri/data"
FILENAME="central_schema.py"

if [ ! -d $OUT_DIR ];then
    echo "Run script from pymemri root folder."
    exit 1
fi

mkdir -p /tmp/pymemri && cd /tmp/pymemri

{
    cd schema
    git pull
} &> /dev/null || {
    git clone -b $BRANCH $SCHEMA_REPO 
    cd schema
} &> /dev/null

python tools/export_pymemri.py -o $OUT_DIR/$FILENAME

rm -rf /tmp/pymemri/schema