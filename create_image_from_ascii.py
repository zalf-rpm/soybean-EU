#!/usr/bin/python
# -*- coding: UTF-8

import sys
import os
import math
import statistics 
import matplotlib
matplotlib.use('Agg')
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import collections
import errno
import gzip
from ruamel_yaml import YAML

PATHS = {
    "local": {
        "sourcepath" : "./asciigrids_debug/",
        "outputpath" : ".",
        "png-out" : "png_debug/" , # path to png images
        "pdf-out" : "pdf-out_debug/" , # path to pdf package
    },
    "test": {
        "sourcepath" : "./asciigrid/",
        "outputpath" : "./testout/",
        "png-out" : "png2/" , # path to png images
        "pdf-out" : "pdf-out2/" , # path to pdf package
    },
    "cluster": {
        "sourcepath" : "/source/",
        "outputpath" : "/out/",
        "png-out" : "png/" , # path to png images
        "pdf-out" : "pdf-out/" , # path to pdf package
    }
}
USER = "local" 
NONEVALUE = -9999

def build() :
    "main"

    pathId = USER
    sourceFolder = ""
    outputFolder = ""
    setupfile = ""
    if len(sys.argv) > 1 and __name__ == "__main__":
        for arg in sys.argv[1:]:
            k, v = arg.split("=")
            if k == "path":
                pathId = v
            if k == "source" :
                sourceFolder = v
            if k == "out" :
                outputFolder = v
            if k == "setup" :
                setupfile = v
            
    if not sourceFolder :
        sourceFolder = PATHS[pathId]["sourcepath"]
    if not outputFolder :
        outputFolder = PATHS[pathId]["outputpath"]

    pngFolder = os.path.join(outputFolder, PATHS[pathId]["png-out"])
    pdfFolder = os.path.join(outputFolder,PATHS[pathId]["pdf-out"])

    if setupfile :
        imageList, mergeList = readSetup(setupfile) 
        
        for root, dirs, files in os.walk(sourceFolder):
            if len(files) > 0 :
                print("root", root)
                print("dirs", dirs)
                scenario = os.path.basename(root)
                pdfpath = os.path.join(pdfFolder, "scenario_{0}.pdf".format(scenario))

                makeDir(pdfpath)
                pdf = PdfPages(pdfpath)

                filepaths = dict()
                metapaths = dict()
                outpaths = dict()
                numCol = len(imageList)
                for col in range(numCol) :
                    for file in imageList[col] :
                        if file in files :
                            print("file", file)
                            pngfilename = file[:-3]+"png"
                            metafilename = file+".meta"
                            isGZ = file.endswith(".gz")
                            if isGZ :
                                pngfilename = file[:-6]+"png"
                                metafilename = file[:-2]+"meta"

                            filepath = os.path.join(root, file)
                            metapath = os.path.join(root, metafilename)
                            outpath = os.path.join(pngFolder, scenario, pngfilename)    

                            filepaths[col].append(filepath)     
                            metapaths[col].append(metapath)
                            outpaths[col].append(outpath)

                createSubPlot( filepaths, metapaths, outpaths, pdf=pdf)

                pdf.close()
    else :    
        for root, dirs, files in os.walk(sourceFolder):
            if len(files) > 0 :
                print("root", root)
                print("dirs", dirs)
                scenario = os.path.basename(root)
                pdfpath = os.path.join(pdfFolder, "scenario_{0}.pdf".format(scenario))

                makeDir(pdfpath)
                pdf = PdfPages(pdfpath)
                files.sort()

                filepaths = list()
                metapaths = list()
                for file in files:
                    if not file.endswith(".meta"):
                        print("file", file)
                        pngfilename = file[:-3]+"png"
                        metafilename = file+".meta"
                        isGZ = file.endswith(".gz")
                        if isGZ :
                            pngfilename = file[:-6]+"png"
                            metafilename = file[:-2]+"meta"

                        filepath = os.path.join(root, file)
                        metapath = os.path.join(root, metafilename)
                        out_path = os.path.join(pngFolder, scenario, pngfilename)    
                        filepaths.append(filepath)     
                        metapaths.append(metapath)
                        createImgFromMeta( filepath, metapath, out_path, pdf=pdf)
                #createSubPlot( filepaths, metapaths, out_path, pdf=pdf)

                pdf.close()

# numcolumn: 2
# column0 :
#    - filename1.asc
#    - mergeimg1
# column1 :
#    - filename3.asc
#    - mergeimg2
# nummerge: 2
# mergeimg0:  
#    - filename5.asc
#    - filename2.asc
# mergeimg1:  
#    - filename4.asc
#    - filename6.asc

def readSetup(filename) :

    imageList = dict()
    mergeList = dict()
    numCol = 2
    numMerge = 0
    with open(filename, 'rt') as source:
       # documents = yaml.load(meta, Loader=yaml.FullLoader)
        yaml=YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)
        documents = yaml.load(source)
        #documents = yaml.full_load(meta)
        for item, doc in documents.items():
            print(item, ":", doc)
            if item == "numcolumn" :
                numCol = int(doc)
            if item == "nummerge" :
                numMerge = int(doc)
            else :
                for colIdx in range(numCol) :
                    if item == "column" + str(colIdx) :
                        imgInCol = list()
                        for img in doc :
                            imgInCol.append(img)
                        imageList[colIdx] = imgInCol
                for mgIdx in range(numMerge) :
                    if item == "mergeimg" + str(mgIdx) :
                        iList = list()
                        for img in doc :
                            iList.append(img)
                        mergeList[mgIdx] = iList

    return (imageList, mergeList)


def createImgFromMeta(ascii_path, meta_path, out_path, pdf=None) :

    if ascii_path.endswith(".gz") :
           # Read in ascii header data
        with gzip.open(ascii_path, 'rt') as source:
            ascii_header = source.readlines()[:6] 
    else :
        # Read in ascii header data
        with open(ascii_path, 'r') as source:
            ascii_header = source.readlines()[:6]

    # Read the ASCII raster header
    ascii_header = [item.strip().split()[-1] for item in ascii_header]
    ascci_cols = int(ascii_header[0])
    ascii_rows = int(ascii_header[1])
    ascii_xll = float(ascii_header[2])
    ascii_yll = float(ascii_header[3])
    ascii_cs = float(ascii_header[4])
    ascii_nodata = float(ascii_header[5])
    
    title="" 
    label=""
    colormap = 'viridis'
    minColor = ""
    cMap = None
    cbarLabel = None
    factor = 0.001
    ticklist = None
    maxValue = ascii_nodata
    maxLoaded = False
    minValue = ascii_nodata
    minLoaded = False

    with open(meta_path, 'rt') as meta:
       # documents = yaml.load(meta, Loader=yaml.FullLoader)
        yaml=YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)
        documents = yaml.load(meta)
        #documents = yaml.full_load(meta)

        for item, doc in documents.items():
            print(item, ":", doc)
            if item == "title" :
                title = doc
            elif item == "labeltext" :
                label = doc
            elif item == "factor" :
                factor = float(doc)
            elif item == "maxValue" :
                maxValue = float(doc)
                maxLoaded = True
            elif item == "minValue" :
                minValue = float(doc)
                minLoaded = True
            elif item == "colormap" :
                colormap = doc
            elif item == "minColor" :
                minColor = doc
            elif item == "colorlist" :
                cMap = doc
            elif item == "cbarLabel" :
                cbarLabel = doc
            elif item == "ticklist" :
                ticklist = list()
                for i in doc :
                    ticklist.append(float(i))


    # Read in the ascii data array
    ascii_data_array = np.loadtxt(ascii_path, dtype=np.float, skiprows=6)
    
    # Set the nodata values to nan
    ascii_data_array[ascii_data_array == ascii_nodata] = np.nan

    # data is stored as an integer but scaled by a factor
    ascii_data_array *= factor
    maxValue *= factor
    minValue *= factor

    image_extent = [
        ascii_xll, ascii_xll + ascci_cols * ascii_cs,
        ascii_yll, ascii_yll + ascii_rows * ascii_cs]
    
    # Plot data array
    fig, ax = plt.subplots()
    ax.set_title(title)
    
    # set min color if given
    if len(minColor) > 0 and not cMap:
        newColorMap = matplotlib.cm.get_cmap(colormap, 256)
        newcolors = newColorMap(np.linspace(0, 1, 256))
        rgba = matplotlib.cm.colors.to_rgba(minColor)
        minColorVal = np.array([rgba])
        newcolors[:1, :] = minColorVal
        colorM = ListedColormap(newcolors)
        if minLoaded and maxLoaded:
            img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmin=minValue, vmax=maxValue)
        elif minLoaded :
            img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmax=minValue)
        elif maxLoaded :
            img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmax=maxValue)
        else :
            img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none')

    # Get the img object in order to pass it to the colorbar function
    elif cMap :
        colorM = ListedColormap(cMap)
        if minLoaded and maxLoaded:
            img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmin=minValue, vmax=maxValue)
        elif minLoaded :
            img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmax=minValue)
        elif maxLoaded :
            img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmax=maxValue)
        else :
            img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none')
    else :
        if minLoaded and maxLoaded:
            img_plot = ax.imshow(ascii_data_array, cmap=colormap, extent=image_extent, interpolation='none', vmin=minValue, vmax=maxValue)
        elif minLoaded :
            img_plot = ax.imshow(ascii_data_array, cmap=colormap, extent=image_extent, interpolation='none', vmax=minValue)
        elif maxLoaded :
            img_plot = ax.imshow(ascii_data_array, cmap=colormap, extent=image_extent, interpolation='none', vmax=maxValue)
        else :
            img_plot = ax.imshow(ascii_data_array, cmap=colormap, extent=image_extent, interpolation='none')

    if ticklist :
        # Place a colorbar next to the map
        cbar = plt.colorbar(img_plot, ticks=ticklist, orientation='vertical', shrink=0.5, aspect=14)
    else :
        # Place a colorbar next to the map
        cbar = plt.colorbar(img_plot, orientation='vertical', shrink=0.5, aspect=14)
    cbar.set_label(label)
    if cbarLabel :
        cbar.ax.set_yticklabels(cbarLabel) 

    ax.grid(True, alpha=0.5)
    # save image and pdf 
    makeDir(out_path)
    if pdf :
        pdf.savefig()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)
  

def createSubPlot(ascii_paths, meta_paths, out_paths, pdf=None) :
        
    numSetups = len(ascii_paths)

    for setupIdx in range(numSetups) :

        numImg = len(ascii_paths)
        ascci_cols = [0] * numImg
        ascii_rows = [0] * numImg
        ascii_xll = [0.0] * numImg
        ascii_yll = [0.0] * numImg
        ascii_cs = [0.0] * numImg
        ascii_nodata = [0.0] * numImg

        title=[""] * numImg  
        label=[""] * numImg
        colormap = ['viridis'] * numImg
        minColor = [""] * numImg
        cMap = [None] * numImg
        cbarLabel =[ None] * numImg
        factor = [0.001] * numImg
        ticklist = [None] * numImg
        maxValue = [0.0] * numImg
        maxLoaded = [False] * numImg
        minValue = [0.0] * numImg
        minLoaded =  [False] * numImg

        for i in range(numImg) :
            if ascii_paths[i].endswith(".gz") :
                # Read in ascii header data
                with gzip.open(ascii_paths[i], 'rt') as source:
                    ascii_header = source.readlines()[:6] 
            else :
                # Read in ascii header data
                with open(ascii_paths[i], 'r') as source:
                    ascii_header = source.readlines()[:6]

            # Read the ASCII raster header
            ascii_header = [item.strip().split()[-1] for item in ascii_header]
            ascci_cols[i] = int(ascii_header[0])
            ascii_rows[i] = int(ascii_header[1])
            ascii_xll[i] = float(ascii_header[2])
            ascii_yll[i] = float(ascii_header[3])
            ascii_cs[i] = float(ascii_header[4])
            ascii_nodata[i] = float(ascii_header[5])
        
            maxValue[i] = ascii_nodata[i]
            minValue[i] = ascii_nodata[i]

            with open(meta_paths[i], 'rt') as meta:
            # documents = yaml.load(meta, Loader=yaml.FullLoader)
                yaml=YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)
                documents = yaml.load(meta)
                #documents = yaml.full_load(meta)

                for item, doc in documents.items():
                    print(item, ":", doc)
                    if item == "title" :
                        title[i] = doc
                    elif item == "labeltext" :
                        label[i] = doc
                    elif item == "factor" :
                        factor[i] = float(doc)
                    elif item == "maxValue" :
                        maxValue[i] = float(doc)
                        maxLoaded[i] = True
                    elif item == "minValue" :
                        minValue[i] = float(doc)
                        minLoaded[i] = True
                    elif item == "colormap" :
                        colormap[i] = doc
                    elif item == "minColor" :
                        minColor[i] = doc
                    elif item == "colorlist" :
                        cMap[i] = doc
                    elif item == "cbarLabel" :
                        cbarLabel[i] = doc
                    elif item == "ticklist" :
                        ticklist[i] = list()
                        for ic in doc :
                            ticklist.append(float(ic))



        
        # Plot data array
        # fig, ax = plt.subplots()
        # ax.set_title(title)
        
        fig, axes = plt.subplots(nrows=int(numImg/2), ncols=2)
        fig.subplots_adjust(top=0.95, bottom=0.01, left=0.2, right=0.99,
                            wspace=0.05)

        fig.suptitle('historical     future', fontsize=14, y=1.0, x=0.6)

        i = 0
        for axRow in axes :
            ax = axRow[ i % 2 ]
            # Read in the ascii data array
            ascii_data_array = np.loadtxt(ascii_paths[i], dtype=np.float, skiprows=6)
            
            # Set the nodata values to nan
            ascii_data_array[ascii_data_array == ascii_nodata[i]] = np.nan

            # data is stored as an integer but scaled by a factor
            ascii_data_array *= factor[i]
            maxValue[i] *= factor[i]
            minValue[i] *= factor[i]

            image_extent = [
                ascii_xll[i], ascii_xll[i] + ascci_cols[i] * ascii_cs[i],
                ascii_yll[i], ascii_yll[i] + ascii_rows[i] * ascii_cs[i]]        
            # set min color if given
            if len(minColor) > 0 and not cMap:
                newColorMap = matplotlib.cm.get_cmap(colormap[i], 256)
                newcolors = newColorMap(np.linspace(0, 1, 256))
                rgba = matplotlib.cm.colors.to_rgba(minColor[i])
                minColorVal = np.array([rgba])
                newcolors[:1, :] = minColorVal
                colorM = ListedColormap(newcolors)
                if minLoaded and maxLoaded:
                    img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmin=minValue[i], vmax=maxValue[i])
                elif minLoaded :
                    img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmax=minValue[i])
                elif maxLoaded :
                    img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmax=maxValue[i])
                else :
                    img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none')

            # Get the img object in order to pass it to the colorbar function
            elif cMap[i] :
                colorM = ListedColormap(cMap[i])
                if minLoaded and maxLoaded:
                    img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmin=minValue[i], vmax=maxValue[i])
                elif minLoaded :
                    img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmax=minValue[i])
                elif maxLoaded :
                    img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmax=maxValue[i])
                else :
                    img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none')
            else :
                if minLoaded and maxLoaded:
                    img_plot = ax.imshow(ascii_data_array, cmap=colormap[i], extent=image_extent, interpolation='none', vmin=minValue[i], vmax=maxValue[i])
                elif minLoaded :
                    img_plot = ax.imshow(ascii_data_array, cmap=colormap[i], extent=image_extent, interpolation='none', vmax=minValue[i])
                elif maxLoaded :
                    img_plot = ax.imshow(ascii_data_array, cmap=colormap[i], extent=image_extent, interpolation='none', vmax=maxValue[i])
                else :
                    img_plot = ax.imshow(ascii_data_array, cmap=colormap[i], extent=image_extent, interpolation='none')

            if ticklist[i] :
                # Place a colorbar next to the map
                cbar = plt.colorbar(img_plot, ticks=ticklist[i], orientation='vertical', shrink=0.5, aspect=14)
            else :
                # Place a colorbar next to the map
                cbar = plt.colorbar(img_plot, orientation='vertical', shrink=0.5, aspect=14)
            cbar.set_label(label)
            if cbarLabel[i] :
                cbar.ax.set_yticklabels(cbarLabel[i]) 

            ax.grid(True, alpha=0.5)
            i = i+1

    # save image and pdf 
    makeDir(out_path)
    if pdf :
        pdf.savefig()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)


def makeDir(out_path) :
    if not os.path.exists(os.path.dirname(out_path)):
        try:
            os.makedirs(os.path.dirname(out_path))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

if __name__ == "__main__":
    build()