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
#print(sys.path)

import gc
import csv
import types
import os
from datetime import datetime
from collections import defaultdict

import zmq
print("pyzmq version: ", zmq.pyzmq_version(), " zmq version: ", zmq.zmq_version())

import monica_io3
#print("path to monica_io: ", monica_io.__file__)

#USER_MODE = "localConsumer-localMonica"
#USER_MODE = "remoteConsumer-remoteMonica"
USER_MODE = "localConsumer-remoteMonica"

server = {
    "localConsumer-localMonica": "localhost",
    "localConsumer-remoteMonica": "login01.cluster.zalf.de",
    "remoteConsumer-remoteMonica": "login01.cluster.zalf.de"
}

CONFIGURATION = {
        "mode": "localConsumer-localMonica",
        "server": None,
        "port": "7777",
        "write_normal_output_files": "false",
        "start_writing_lines_threshold": 1000 , 
        "timeout": 600000 # 10 minutes

    }
# local testing: python .\run-work-consumer.py port=6007 mode=localConsumer-remoteMonica timeout=100000 > out_consumer.txt


def create_output(soil_ref, crop_id, first_cp, co2_id, co2_value, period, gcm, trt_no, prod_case, result):
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

                    if isinstance(val, list):
                        for val_ in val:
                            vals[name] = val_
                    else:
                        vals[name] = val

                if "Year" not in vals:
                    print("Missing Year in result section. Skipping results section.")
                    continue

                year_to_vals[vals.get("Year", 0)].update(vals)

        for year, vals in year_to_vals.items():
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
                    vals.get("sum_Nmin", "na")
                ])
                '''
                current_crop = vals["Crop"],
                if "maize" in current_crop[0]:
                    AntDOY = vals.get("AntDOY_maize", "na")
                elif "soy" in current_crop[0]:
                    AntDOY = vals.get("AntDOY_soy", "na")
                
                #calculate SWC (i.e., SWC-PWP [mm])
                def convert_SWC(SWC, PWP, depth_mm):
                    return max((SWC-PWP) * depth_mm, 0)
                
                #
                AWC_30_14Mar = convert_SWC(vals["Mois_0_30_14Mar"], vals["Pwp_0_30"], 300)
                AWC_30_sow = convert_SWC(vals["Mois_0_30_sow"], vals["Pwp_0_30"], 300)
                AWC_30_harv = convert_SWC(vals["Mois_0_30_harv"], vals["Pwp_0_30"], 300)
                #
                AWC_60_14Mar = convert_SWC(vals["Mois_30_60_14Mar"], vals["Pwp_30_60"], 300)
                AWC_60_sow = convert_SWC(vals["Mois_30_60_sow"], vals["Pwp_30_60"], 300)
                AWC_60_harv = convert_SWC(vals["Mois_30_60_harv"], vals["Pwp_30_60"], 300)
                #
                AWC_90_14Mar = convert_SWC(vals["Mois_60_90_14Mar"], vals["Pwp_60_90"], 300)
                AWC_90_sow = convert_SWC(vals["Mois_60_90_sow"], vals["Pwp_60_90"], 300)
                AWC_90_harv = convert_SWC(vals["Mois_60_90_harv"], vals["Pwp_60_90"], 300)

                out.append([
                    "MO",
                    soil_ref,
                    first_cp,
                    current_crop[0],
                    #"soy_" + crop_id,
                    #co2_id,
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
                    AntDOY,
                    vals.get("MatDOY", "na"),
                    vals.get("HarvDOY", "na"),                    
                    vals.get("cycle-length", "na"),

                    vals.get("cum_ET", "na"),

                    AWC_30_14Mar,
                    AWC_60_14Mar,
                    AWC_90_14Mar,

                    AWC_30_sow,
                    AWC_60_sow,
                    AWC_90_sow,

                    AWC_30_harv,
                    AWC_60_harv,
                    AWC_90_harv,

                    vals.get("tradef", "na"),
                    vals.get("frostred", "na"),
                    vals.get("cum_irri", "na"),
                    vals.get("sum_Nmin", "na")
                ])

    return out

#+"Stage,HeatRed,RelDev,"\
HEADER_long = "Model,soil_ref,Crop,period," \
         + "sce,CO2,TrtNo,ProductionCase," \
         + "Year," \
         + "Yield,AntDOY,MatDOY,Biom-an,Biom-ma," \
         + "MaxLAI,WDrain,CumET,SoilAvW,Runoff,Transp,Evap,CroN-an,CroN-ma," \
         + "GrainN,ET0,SowDOY,EmergDOY,reldev,tradef,frostred,frost-risk-days,cycle-length,STsow,ATsow" \
         + "\n"

HEADER = "Model,soil_ref,first_crop,Crop,period," \
         + "sce,CO2,TrtNo,ProductionCase," \
         + "Year," \
         + "Yield," \
         + "MaxLAI," \
         + "SowDOY,EmergDOY,AntDOY,MatDOY,HarvDOY,cycle-length,sum_ET," \
         + "AWC_30_14Mar,AWC_60_14Mar,AWC_90_14Mar," \
         + "AWC_30_sow,AWC_60_sow,AWC_90_sow," \
         + "AWC_30_harv,AWC_60_harv,AWC_90_harv," \
         + "tradef,frostred,sum_irri,sum_Nmin" \
         + "\n"


#overwrite_list = set()
def write_data(soil_ref, data, usermode):
    "write data"

    if usermode=="remoteConsumer-remoteMonica":
        #path_to_file = "/beegfs/stella/out/EU_SOY_MO_" + str(row) + "_" + str(col) + ".csv"
        path_to_file = "/out/EU_SOY_MO_" + soil_ref + ".csv"
    else:
        path_to_file = "./out/EU_SOY_MO_" + soil_ref + ".csv"

    if not os.path.isfile(path_to_file):# or (row, col) not in overwrite_list:
        with open(path_to_file, "w") as _:
            _.write(HEADER)
        #overwrite_list.add((row, col))

    with open(path_to_file, 'a', newline="") as _:
        writer = csv.writer(_, delimiter=",")
        for row_ in data[soil_ref]:
            writer.writerow(row_)
        data[soil_ref] = []


def main():
    "collect data from workers"

    config = CONFIGURATION

    if len(sys.argv) > 1 and __name__ == "__main__":
        for arg in sys.argv[1:]:
            k,v = arg.split("=")
            if k in config:
                if k == "timeout" or k == "start_writing_lines_threshold":
                    config[k] = int(v)
                else :
                    config[k] = v

    if not config["server"]:
        config["server"] = server[config["mode"]]

    print("consumer config:", config)

    data = defaultdict(list)

    i = 1
    context = zmq.Context()
    socket = context.socket(zmq.PULL) # pylint: disable=no-member
    socket.connect("tcp://" + config["server"] + ":" + config["port"])
    socket.RCVTIMEO = config["timeout"]
    leave = False
    write_normal_output_files = config["write_normal_output_files"] == "true"
    start_writing_lines_threshold = config["start_writing_lines_threshold"]
    while not leave:

        try:
            #result = socket.recv_json()
            result = socket.recv_json(encoding="latin-1")

            #result = socket.recv_string(encoding="latin-1")
            #result = socket.recv_string()
            #print(result)
            #with open("out/out-latin1.csv", "w") as _:
            #    _.write(result)
            #continue
        except zmq.error.Again as _e:
            print('no response from the server (with "timeout"=%d ms) ' % socket.RCVTIMEO)
            for soil_ref in data.keys():
                if len(data[soil_ref]) > 0:
                    write_data(soil_ref, data, config["mode"])
            return
        except:
            for soil_ref in data.keys():
                if len(data[soil_ref]) > 0:
                    write_data(soil_ref, data, config["mode"])
            continue


        if result["type"] == "finish":
            print("received finish message")
            leave = True

        elif not write_normal_output_files:
            if len(result["errors"]) > 0 :
                for err in result["errors"] :
                    print(err)

            custom_id = result["customId"]
            #sendID = custom_id["sendID"]
            soil_ref = custom_id["soil_ref"]
            #row = custom_id["row"]
            #col = custom_id["col"]
            period = custom_id["period"]
            gcm = custom_id["gcm"]
            co2_id = custom_id["co2_id"]
            co2_value = custom_id["co2_value"]
            trt_no = custom_id["trt_no"]
            prod_case = custom_id["prod_case"]
            crop_id = custom_id["crop_id"]
            first_cp = custom_id["first_cp"]
            
            #print("recv env ", sendID, "customId: ", list(custom_id.values()))
           # print(custom_id)
            res = create_output(soil_ref, crop_id, first_cp, co2_id, co2_value, period, gcm, trt_no, prod_case, result)
            data[soil_ref].extend(res)

            if len(data[soil_ref]) >= start_writing_lines_threshold:
                write_data(soil_ref, data, config["mode"])

            i = i + 1

        elif write_normal_output_files:
            print("received work result ", i, " customId: ", result.get("customId", ""))
            if result.get("type", "") in ["jobs-per-cell", "no-data", "setup_data"]:
                #print "ignoring", result.get("type", "")
                return

            with open("out/out-" + str(i) + ".csv", 'w') as _:
                writer = csv.writer(_, delimiter=",")

                for data_ in result.get("data", []):
                    results = data_.get("results", [])
                    orig_spec = data_.get("origSpec", "")
                    output_ids = data_.get("outputIds", [])

                    if len(results) > 0:
                        writer.writerow([orig_spec.replace("\"", "")])
                        for row in monica_io3.write_output_header_rows(output_ids,
                                                                      include_header_row=True,
                                                                      include_units_row=True,
                                                                      include_time_agg=False):
                            writer.writerow(row)

                        for row in monica_io3.write_output(output_ids, results):
                            writer.writerow(row)

                    writer.writerow([])

            i = i + 1


main()
