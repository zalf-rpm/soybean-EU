#!/usr/bin/python
# -*- coding: UTF-8

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/. */

# Authors:
# Michael Berg-Mohnicke <michael.berg@zalf.de>
# Tommaso Stella <tommaso.stella@zalf.de>
#
# Maintainers:
# Currently maintained by the authors.
#
# This file has been created at the Institute of
# Landscape Systems Analysis at the ZALF.
# Copyright (C: Leibniz Centre for Agricultural Landscape Research (ZALF)

import sys
#print sys.path

import zmq
#print "pyzmq version: ", zmq.pyzmq_version(), " zmq version: ", zmq.zmq_version()

config = {
    "server": "localhost",
    "port": "7777"
}

if len(sys.argv) > 1:
    for arg in sys.argv[1:]:
        k, v = arg.split("=")
        if k in config:
            config[k] = v

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.connect("tcp://" + config["server"] + ":" + config["port"])

i = 0
while True:
    socket.recv_json(encoding="latin-1")
    if i%10 == 0:
        print(i, end="")
    i = i + 1
