#!/bin/sh
# Copyright (c) 2018
# Cavium
#
# SPDX-License-Identifier: Apache-2.0
#
# Author: chencho <smunoz@cavium.com>

set -e 

mosquitto -d -c /config/mosquitto.conf

sleep 3
cd test
echo $@
python demo_cli.py $@
