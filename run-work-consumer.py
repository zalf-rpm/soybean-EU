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
#sys.path.insert(0, "C:\\Users\\berg.ZALF-AD\\GitHub\\monica\\project-files\\Win32\\Release")
#sys.path.insert(0, "C:\\Users\\berg.ZALF-AD\\GitHub\\monica\\src\\python")
#sys.path.insert(0, "C:\\Program Files (x86)\\MONICA")
print sys.path

import gc
import csv
import types
import os
from datetime import datetime
from collections import defaultdict

import zmq
print "pyzmq version: ", zmq.pyzmq_version(), " zmq version: ", zmq.zmq_version()

import monica_io
#print "path to monica_io: ", monica_io.__file__

#USER_MODE = "localConsumer-localMonica"
USER_MODE = "localConsumer-remoteMonica"

server = {
    "localConsumer-localMonica": "localhost",
    "localConsumer-remoteMonica": "login01.cluster.zalf.de"
}

CONFIGURATION = {
        "server": server[USER_MODE],
        "server-port": "7778",
        "write_normal_output_files": False,
        "start_writing_lines_threshold": 100#5880
    }

def create_output(row, col, crop_id, co2_id, co2_value, period, gcm, trt_no, prod_case, result):
    "create crop output lines"

    out = []
    if len(result.get("data", [])) > 0 and len(result["data"][0].get("results", [])) > 0:
        year_to_vals = defaultdict(dict)
        
        for data in result.get("data", []):
            results = data.get("results", [])
            oids = data.get("outputIds", [])

            #skip empty results, e.g. when event condition haven't been met
            if len(results) == 0:
                continue

            assert len(oids) == len(results)
            for kkk in range(0, len(results[0])):
                vals = {}
            
                for iii in range(0, len(oids)):
                        
                    oid = oids[iii]
                    
                    val = results[iii][kkk]

                    name = oid["name"] if len(oid["displayName"]) == 0 else oid["displayName"]

                    if isinstance(val, types.ListType):
                        for val_ in val:
                            vals[name] = val_
                    else:
                        vals[name] = val

                if "Year" not in vals:
                    print "Missing Year in result section. Skipping results section."
                    continue

                year_to_vals[vals.get("Year", 0)].update(vals)

        for year, vals in year_to_vals.iteritems():
            if len(vals) > 0 and year > 1980:
                '''
                #long output version
                out.append([
                    "MO",
                    str(row) + "_" + str(col),
                    "soy_" + crop_id,
                    co2_id,
                    period,
                    gcm,
                    str(co2_value),
                    trt_no,
                    prod_case,
                    year,

                    #vals.get("Stage", "na"),
                    #vals.get("HeatRed", "na"),
                    #vals.get("RelDev", "na"),

                    vals.get("Yield", "na"),
                    vals.get("AntDOY", "na"),
                    vals.get("MatDOY", "na"),
                    vals.get("Biom-an", "na"),
                    vals.get("Biom-ma", "na"),
                    vals.get("MaxLAI", "na"),
                    vals.get("WDrain", "na"),
                    vals.get("CumET", "na"),
                    vals.get("SoilAvW", "na") * 100.0 if "SoilAvW" in vals else "na",
                    vals.get("Runoff", "na"),
                    vals["CumET"] - vals["Evap"] if "CumET" in vals and "Evap" in vals else "na",
                    vals.get("Evap", "na"),
                    vals.get("CroN-an", "na"),
                    vals.get("CroN-ma", "na"),
                    vals.get("GrainN", "na"),
                    vals.get("Eto", "na"),
                    vals.get("SowDOY", "na"),
                    vals.get("EmergDOY", "na"),
                    vals.get("reldev", "na"),
                    vals.get("tradef", "na"),
                    vals.get("frostred", "na"),
                    vals.get("frost-risk-days", 0),
                    vals.get("cycle-length", "na"),
                    vals.get("STsow", "na"),
                    vals.get("ATsow", "na")
                ])
                '''

                out.append([
                    "MO",
                    str(row) + "_" + str(col),
                    "soy_" + crop_id,
                    co2_id,
                    period,
                    gcm,
                    str(co2_value),
                    trt_no,
                    prod_case,
                    year,

                    #vals.get("Stage", "na"),
                    #vals.get("HeatRed", "na"),
                    #vals.get("RelDev", "na"),

                    vals.get("Yield", "na"),
                    vals.get("MaxLAI", "na"),
                    vals.get("SowDOY", "na"),
                    vals.get("EmergDOY", "na"),
                    vals.get("AntDOY", "na"),
                    vals.get("MatDOY", "na"),
                    vals.get("HarvDOY", "na"),                    
                    vals.get("cycle-length", "na"),
                    vals.get("tradef", "na"),
                    vals.get("frostred", "na")
                ])

    return out

#+"Stage,HeatRed,RelDev,"\
HEADER_long = "Model,row_col,Crop,ClimPerCO2_ID,period," \
         + "sce,CO2,TrtNo,ProductionCase," \
         + "Year," \
         + "Yield,AntDOY,MatDOY,Biom-an,Biom-ma," \
         + "MaxLAI,WDrain,CumET,SoilAvW,Runoff,Transp,Evap,CroN-an,CroN-ma," \
         + "GrainN,ET0,SowDOY,EmergDOY,reldev,tradef,frostred,frost-risk-days,cycle-length,STsow,ATsow" \
         + "\n"

HEADER = "Model,row_col,Crop,ClimPerCO2_ID,period," \
         + "sce,CO2,TrtNo,ProductionCase," \
         + "Year," \
         + "Yield," \
         + "MaxLAI," \
         + "SowDOY,EmergDOY,AntDOY,MatDOY,HarvDOY,cycle-length,tradef,frostred" \
         + "\n"


#overwrite_list = set()
def write_data(row, col, data):
    "write data"

    path_to_file = "out/EU_SOY_MO_" + str(row) + "_" + str(col) + ".csv"

    if not os.path.isfile(path_to_file):# or (row, col) not in overwrite_list:
        with open(path_to_file, "w") as _:
            _.write(HEADER)
        #overwrite_list.add((row, col))

    with open(path_to_file, 'ab') as _:
        writer = csv.writer(_, delimiter=",")
        for row_ in data[(row, col)]:
            writer.writerow(row_)
        data[(row, col)] = []


def main():
    "collect data from workers"

    data = defaultdict(list)

    i = 1
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.connect("tcp://" + CONFIGURATION["server"] + ":" + str(CONFIGURATION["server-port"]))
    socket.RCVTIMEO = 1000
    leave = False
    write_normal_output_files = CONFIGURATION["write_normal_output_files"]
    start_writing_lines_threshold = CONFIGURATION["start_writing_lines_threshold"]
    while not leave:

        try:
            #result = socket.recv_json()
            result = socket.recv_json(encoding="latin-1")
            #result = socket.recv_string(encoding="latin-1")
            #result = socket.recv_string()
            #print result
            #with open("out/out-latin1.csv", "w") as _:
            #    _.write(result)
            #continue
        except:
            for row, col in data.keys():
                if len(data[(row, col)]) > 0:
                    write_data(row, col, data)
            continue

        if result["type"] == "finish":
            print "received finish message"
            leave = True

        elif not write_normal_output_files:
            print "received work result ", i, " customId: ", result.get("customId", "")

            custom_id = result["customId"]
            ci_parts = custom_id.split("|")
            row_, col_ = ci_parts[0][0:-1].split("/")
            row, col = (int(row_), int(col_))
            period = ci_parts[1]
            gcm = ci_parts[2]
            co2_id, co2_value_ = ci_parts[3][1:-1].split("/")
            co2_value = int(co2_value_)
            trt_no = ci_parts[4]
            prod_case = ci_parts[5]
            crop_id = ci_parts[6]
            
            res = create_output(row, col, crop_id, co2_id, co2_value, period, gcm, trt_no, prod_case, result)
            data[(row, col)].extend(res)

            if len(data[(row, col)]) >= start_writing_lines_threshold:
                write_data(row, col, data)

            i = i + 1

        elif write_normal_output_files:
            print "received work result ", i, " customId: ", result.get("customId", "")

            with open("out/out-" + str(i) + ".csv", 'wb') as _:
                writer = csv.writer(_, delimiter=",")

                for data_ in result.get("data", []):
                    results = data_.get("results", [])
                    orig_spec = data_.get("origSpec", "")
                    output_ids = data_.get("outputIds", [])

                    if len(results) > 0:
                        writer.writerow([orig_spec.replace("\"", "")])
                        for row in monica_io.write_output_header_rows(output_ids,
                                                                      include_header_row=True,
                                                                      include_units_row=True,
                                                                      include_time_agg=False):
                            writer.writerow(row)

                        for row in monica_io.write_output(output_ids, results):
                            writer.writerow(row)

                    writer.writerow([])

            i = i + 1


main()
