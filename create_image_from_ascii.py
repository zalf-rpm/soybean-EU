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
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import matplotlib.ticker as mticker
from scipy import interpolate as spy
from datetime import datetime
import collections
import errno
import gzip
from ruamel_yaml import YAML
from dataclasses import dataclass
import typing

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
SETUP_FILENAME = "image-setup.yml"

def build() :
    "main"

    pathId = USER
    sourceFolder = ""
    outputFolder = ""
    generatePDF = False
    if len(sys.argv) > 1 and __name__ == "__main__":
        for arg in sys.argv[1:]:
            k, v = arg.split("=")
            if k == "path":
                pathId = v
            if k == "source" :
                sourceFolder = v
            if k == "out" :
                outputFolder = v
            if k == generatePDF :
                generatePDF = bool(v)
            
    if not sourceFolder :
        sourceFolder = PATHS[pathId]["sourcepath"]
    if not outputFolder :
        outputFolder = PATHS[pathId]["outputpath"]

    pngFolder = os.path.join(outputFolder, PATHS[pathId]["png-out"])
    pdfFolder = os.path.join(outputFolder,PATHS[pathId]["pdf-out"])

    print(os.getcwd())
    # imageList, mergeList = readSetup(setupfile) 
    for root, dirs, files in os.walk(sourceFolder):
        if len(files) > 0 :
            print("root", root)
            print("dirs", dirs)
            scenario = os.path.basename(root)
            pdf = None
            if generatePDF :
                pdfpath = os.path.join(pdfFolder, "scenario_{0}.pdf".format(scenario))
                makeDir(pdfpath)
                pdf = PdfPages(pdfpath)        

            useSetup = any(file == SETUP_FILENAME for file in files)      
            if useSetup :
                # check if folder contains a setup file
                imageList = readSetup(os.path.join(root, SETUP_FILENAME), root, files)
                numImages = len(imageList)

                for imgIdx in range(numImages) :
                    image = imageList[imgIdx]
                    imageName = image.name
                    pngfilename = imageName + ".png"

                    outpath = os.path.join(pngFolder, scenario, pngfilename)  
                    createSubPlot(image, outpath, pdf=pdf)
                if generatePDF :
                    pdf.close()
            else :
                files.sort()
                for file in files:
                    if file.endswith(".asc") or file.endswith(".asc.gz") :
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
                        createImgFromMeta( filepath, metapath, out_path, pdf=pdf)
                if generatePDF :
                    pdf.close()

# image: 
#  name: image filename
#  - row 
#    - file: filename (no ext)
#    - file: filename (no ext)
#  - row
#    - file: filename (no ext)
#    - merge: 
#     - file: filename (no ext)
#     - file: filename (no ext)
# image:
#  - file: filename (no ext) 
# image: 
#  - merge: 
#    - file: filename (no ext)
#    - file: filename (no ext)    

@dataclass
class Image:
    name: str
    title: str
    size: typing.Tuple[float, float]
    adjBottom: float
    adjTop: float
    adRight: float
    adLeft: float
    adhspace: float
    adwspace: float
    content: list

@dataclass
class Row:
    subtitle: str
    sharedColorBar: bool
    content: list

@dataclass
class Merge:
    mintransparency: list
    transparencyfactor: list
    content: list

@dataclass
class File:
    name: str
    meta: str

def readSetup(filename, root, files) :
    imageList = list()
    indexImg = 0

    def readFile(doc) :
        filename = doc
        metafilename = filename+".meta"
        isGZ = filename.endswith(".gz")
        if isGZ :
            metafilename = filename[:-2]+"meta"
        filepath = os.path.join(root, filename)
        metapath = os.path.join(root, metafilename)
        return File(filepath, metapath)   

    def readRows(doc) : 
        rowContent = list()
        for rows in doc :
            for row in rows:
                if row == "row" :
                    rowList = list()
                    sharedColorBar = False
                    subtitle = ""
                    for entries in rows["row"]:
                        for entry in entries :
                            if entry == "sharedColorBar" :
                                sharedColorBar = bool(entries["sharedColorBar"])
                            if entry == "subtitle" :
                                subtitle = entries["subtitle"]
                            if entry == "file" :
                                rowList.append(readFile(entries["file"]))
                            if entry == "merge" :
                                rowList.append(readMerge(entries["merge"]))
                    rowContent.append(Row(subtitle, sharedColorBar, rowList))
        return rowContent

    def readMerge(doc) : 
        mergeContent = list()
        mintransparency = list()
        transparencyfactorList = list()
        for entry in doc :
            for f in entry:
                if f == "file" :
                    mergeContent.append(readFile(entry["file"]))
                    mintransparency.append(1.0)
                    transparencyfactorList.append(1.0)
                if f == "mintransparent" :
                    val = float(entry["mintransparent"])
                    mintransparency[len(mintransparency) - 1] = val
                if f == "transparencyfactor" :
                    val = float(entry["transparencyfactor"])
                    transparencyfactorList[len(transparencyfactorList) - 1] = val
        return Merge(mintransparency, transparencyfactorList, mergeContent)

    with open(filename, 'rt') as source:
       # documents = yaml.load(meta, Loader=yaml.FullLoader)
        yaml=YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)
        documents = yaml.load(source)
        #documents = yaml.full_load(meta)
        for item in documents:
            print(item)
            if "image" in item:
                indexImg = indexImg + 1 
                imagename = "none" + str(indexImg)
                title = ""
                imgSize = None
                sizeX = 0
                sizeY = 0
                adjBottom = 0.15
                adjTop = 0.95
                adRight = 0.95
                adLeft = 0.15
                adhspace = 0.0
                adwspace = 0.0
                imageContent = list()
                for entry in item["image"] :
                    if entry == "name"  :
                        imagename = item["image"][entry]
                    if entry == "title"  :
                        title = item["image"][entry]
                    if entry == "sizeX"  :
                        sizeX = float(item["image"][entry])
                    if entry == "sizeY"  :
                        sizeY = float(item["image"][entry])
                    if entry == "adjBottom" :
                        adjBottom = float(item["image"][entry])
                    if entry == "adjTop" :
                        adjTop = float(item["image"][entry])
                    if entry == "adRight" :
                        adRight = float(item["image"][entry])
                    if entry == "adLeft" :
                        adLeft = float(item["image"][entry])
                    if entry == "adhspace" :
                        adhspace = float(item["image"][entry])
                    if entry == "adwspace" :
                        adwspace = float(item["image"][entry])
                    elif entry == "file" :
                        imageContent.append(readFile(item["image"][entry]))
                    elif entry == "rows" :
                        imageContent = readRows(item["image"][entry])
                    elif entry == "merge" :
                        imageContent.append(readMerge(item["image"][entry]))
                if sizeX > 0 and sizeY > 0 :
                    imgSize = (sizeX, sizeY)
                imageList.append(Image(imagename, title, imgSize,
                                adjBottom, adjTop, adRight, adLeft, adhspace, adwspace, imageContent))
    return imageList


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

    if os.path.isfile(meta_path)  :
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
  

@dataclass
class AsciiHeader:
    ascii_path: str
    ascci_cols: int
    ascii_rows: int
    ascii_xll: float
    ascii_yll: float
    ascii_cs: float
    ascii_nodata: float
    image_extent: list

def readAsciiHeader(ascii_path) :
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

    image_extent = [
                ascii_xll, ascii_xll + ascci_cols * ascii_cs,
                ascii_yll, ascii_yll + ascii_rows * ascii_cs] 

    return AsciiHeader(ascii_path, ascci_cols, ascii_rows, ascii_xll, ascii_yll, ascii_cs, ascii_nodata, image_extent)

@dataclass
class Meta:
    title: str
    label: str
    colormap: str
    minColor: str
    cMap : list
    cbarLabel: str
    factor: float
    ticklist: list
    yTicklist: list
    xTicklist: list
    maxValue: float
    maxLoaded: bool
    minValue: float
    minLoaded: bool
    showbars: bool
    mintransparent: float
    renderAs: str
    transparencyfactor: float
    lineLabel: str
    xLabel: str
    yLabel: str
    YaxisMappingFile: str
    YaxisMappingRefColumn: str
    YaxisMappingTarColumn: str
    YaxisMappingFormat: str
    XaxisMappingFile: str
    XaxisMappingRefColumn: str
    XaxisMappingTarColumn: str
    XaxisMappingFormat: str

def readMeta(meta_path, ascii_nodata, showCBar) :
    title="" 
    label=""
    colormap = 'viridis'
    minColor = ""
    cMap = None
    cbarLabel = None
    factor = 0.001
    ticklist = None
    xTicklist = None
    yTicklist = None
    maxValue = ascii_nodata
    maxLoaded = False
    minValue = ascii_nodata
    minLoaded = False
    showbars = showCBar
    mintransparent = 1.0
    renderAs = "heatmap"
    transparencyfactor = 1.0
    lineLabel = ""
    xLabel = ""
    yLabel = ""
    YaxisMappingFile = ""
    YaxisMappingRefColumn = ""
    YaxisMappingTarColumn = ""
    YaxisMappingFormat = ""
    XaxisMappingFile = ""
    XaxisMappingRefColumn = ""
    XaxisMappingTarColumn = ""
    XaxisMappingFormat = ""

    with open(meta_path, 'rt', encoding='utf-8') as meta:
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
            elif item == "mintransparent" :
                mintransparent = float(doc)
            elif item == "transparencyfactor" :
                transparencyfactor = float(doc)
            elif item == "colorlist" :
                cMap = doc
            elif item == "renderAs" :
                renderAs = doc
            elif item == "cbarLabel" :
                cbarLabel = doc
            elif item == "lineLabel" :
                lineLabel = doc
            elif item == "xLabel" :
                xLabel = doc
            elif item == "yLabel" :
                yLabel = doc
            elif item == "YaxisMappingFile" :
                YaxisMappingFile = doc
            elif item == "YaxisMappingRefColumn" :
                YaxisMappingRefColumn = doc
            elif item == "YaxisMappingTarColumn" :
                YaxisMappingTarColumn = doc
            elif item == "YaxisMappingFormat" :
                YaxisMappingFormat = doc
            elif item == "XaxisMappingFile" :
                XaxisMappingFile = doc
            elif item == "XaxisMappingRefColumn" :
                XaxisMappingRefColumn = doc
            elif item == "XaxisMappingTarColumn" :
                XaxisMappingTarColumn = doc
            elif item == "XaxisMappingFormat" :
                YaxisMappingFormat = doc
            elif item == "ticklist" :
                ticklist = list()
                for i in doc :
                    ticklist.append(float(i))
            elif item == "yTicklist" :
                yTicklist = list()
                for i in doc :
                    yTicklist.append(float(i))
            elif item == "xTicklist" :
                xTicklist = list()
                for i in doc :
                    xTicklist.append(float(i))
    maxValue *= factor
    minValue *= factor
    return Meta(title, label, colormap, minColor, cMap,
                cbarLabel, factor, ticklist,yTicklist,xTicklist, maxValue, maxLoaded, minValue, minLoaded, 
                showbars, mintransparent, renderAs, transparencyfactor, lineLabel, xLabel, yLabel,
                YaxisMappingFile,YaxisMappingRefColumn,YaxisMappingTarColumn,YaxisMappingFormat,
                XaxisMappingFile,XaxisMappingRefColumn,XaxisMappingTarColumn,XaxisMappingFormat)


def createSubPlot(image, out_path, pdf=None) :
        
    nplotRows = 0
    nplotCols = 0
    asciiHeaderLs = dict()
    metaLs = dict()
    subtitles = list()
    for content in image.content :

        if type(content) is File :
            name = content.name
            meta = content.meta
            asciiHeader = readAsciiHeader(name)
            meta = readMeta(meta, asciiHeader.ascii_nodata, True)  
            nplotRows += 1
            nplotCols += 1             
            asciiHeaderLs[(nplotRows, nplotCols)] = asciiHeader 
            metaLs[(nplotRows, nplotCols)] = meta
            break
        elif type(content) is Row :
            nplotRows += 1
            numCol = 0
            subtitles.append(content.subtitle)
            shareCBar = content.sharedColorBar
            lastCol = len(content.content)
            for col in content.content :
                numCol += 1
                showBar = not shareCBar or (numCol == lastCol) 
                if type(col) is File :
                    asciiHeader = readAsciiHeader(col.name)         
                    asciiHeaderLs[(nplotRows, numCol)] = asciiHeader
                    metaLs[(nplotRows, numCol)] = readMeta(col.meta, asciiHeader.ascii_nodata, showBar) 
                elif type(col) is Merge :
                    mergeHeaderList = list()
                    mergeMetaList = list()
                    transparencyList = col.mintransparency
                    transparencyfactorList = col.transparencyfactor
                    idxT = 0
                    for f in col.content :
                        asciiHeader = readAsciiHeader(f.name)         
                        meta = readMeta(f.meta, asciiHeader.ascii_nodata, showBar) 
                        meta.mintransparent = min(transparencyList[idxT], meta.mintransparent)
                        meta.transparencyfactor = transparencyfactorList[idxT]
                        mergeHeaderList.append(asciiHeader)
                        mergeMetaList.append(meta)
                        idxT += 1
                    asciiHeaderLs[(nplotRows, numCol)] = mergeHeaderList
                    metaLs[(nplotRows, numCol)] = mergeMetaList

            if numCol > nplotCols : 
                nplotCols = numCol
                
        elif type(content) is Merge:
            mergeHeaderList = list()
            mergeMetaList = list()
            transparencyList = content.mintransparency
            transparencyfactorList = content.transparencyfactor
            idxT = 0
            for f in content.content :
                asciiHeader = readAsciiHeader(f.name)         
                meta = readMeta(f.meta, asciiHeader.ascii_nodata, True) 
                meta.mintransparent = min(transparencyList[idxT], meta.mintransparent)
                meta.transparencyfactor = transparencyfactorList[idxT]
                mergeHeaderList.append(asciiHeader)
                mergeMetaList.append(meta)
                idxT += 1
            nplotRows += 1
            nplotCols += 1 
            asciiHeaderLs[(nplotRows, nplotCols)] = mergeHeaderList
            metaLs[(nplotRows, nplotCols)] = mergeMetaList
            break
    # Plot data array
    # fig, ax = plt.subplots()
    # ax.set_title(title)
    
    fig, axs = plt.subplots(nrows=nplotRows, ncols=nplotCols, squeeze=False, sharex=True, sharey=True, figsize=image.size)
    # defaults
    # image.adjBottom = 0.15
    # image.adjTop = 0.95
    # image.adRight = 0.95
    # image.adLeft = 0.15
    # image.adhspace = 0.0
    # image.adwspace = 0.0
    fig.subplots_adjust(top=image.adjTop, bottom=image.adjBottom, left=image.adLeft, right=image.adRight, wspace=image.adwspace, hspace=image.adhspace)
    
    if image.title :
        fig.suptitle(image.title, fontsize='xx-large')

    #fig.suptitle('historical     future', fontsize=14, y=1.0, x=0.6)

    for idxRow in range(1,nplotRows+1) :
        for idxCol in range(1,nplotCols+1) :
            ax = axs[idxRow-1][idxCol-1]
            asciiHeaders = asciiHeaderLs[(idxRow,idxCol)]
            metas = metaLs[(idxRow,idxCol)]
            asciiHeadersLs = list()
            matchMetaLs = list()
            if type(asciiHeaders) is not list :
                asciiHeadersLs.append(asciiHeaders)
                matchMetaLs.append(metas)
            else :
                asciiHeadersLs = asciiHeaders
                matchMetaLs = metas
            for idxMerg in range(len(asciiHeadersLs)) :
                asciiHeader = asciiHeadersLs[idxMerg]
                meta = matchMetaLs[idxMerg]
                # Read in the ascii data array
                ascii_data_array = np.loadtxt(asciiHeader.ascii_path, dtype=np.float, skiprows=6)
                
                colorM = None
                # set min color if given
                if len(meta.minColor) > 0 and not meta.cMap:
                    newColorMap = matplotlib.cm.get_cmap(meta.colormap, 256)
                    newcolors = newColorMap(np.linspace(0, 1, 256))
                    for idC in range(256) :
                        if idC == 0 :
                            alpha = meta.mintransparent * meta.transparencyfactor
                            rgba = matplotlib.cm.colors.to_rgba(meta.minColor, alpha=alpha)
                            minColorVal = np.array([rgba])
                            newcolors[:1, :] = minColorVal
                        else :
                            newcolors[idC:idC+1, 3:4] = meta.transparencyfactor
                    colorM = ListedColormap(newcolors)
                # Get the img object in order to pass it to the colorbar function
                elif meta.cMap :
                    if meta.transparencyfactor < 1.0 or meta.mintransparent < 1.0:
                        newColorMap = ListedColormap(meta.cMap)
                        newcolors = newColorMap(np.linspace(0, 1, len(meta.cMap)))
                        for idC in range(len(meta.cMap)) :
                            alpha = meta.transparencyfactor
                            if idC == 0 :
                                alpha = meta.mintransparent * meta.transparencyfactor
                            rgba = matplotlib.cm.colors.to_rgba(meta.cMap[idC], alpha=alpha)
                            newcolors[idC:idC+1, :] = np.array([rgba])
                        colorM = ListedColormap(newcolors)
                    else :
                        colorM = ListedColormap(meta.cMap)
                else :
                # use color map name 
                    newColorMap = matplotlib.cm.get_cmap(meta.colormap, 256)
                    newcolors = newColorMap(np.linspace(0, 1, 256))
                    for idC in range(256) :
                        alpha = meta.transparencyfactor
                        if idC == 0 :
                            alpha = meta.mintransparent * meta.transparencyfactor
                        newcolors[idC:idC+1, 3:4] = alpha
                    colorM = ListedColormap(newcolors)

                if meta.renderAs == "heatmap" :
                    # Set the nodata values to nan
                    ascii_data_array[ascii_data_array == asciiHeader.ascii_nodata] = np.nan
                    # data is stored as an integer but scaled by a factor
                    ascii_data_array *= meta.factor

                    if meta.minLoaded and meta.maxLoaded:
                        img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=asciiHeader.image_extent, interpolation='none', vmin=meta.minValue, vmax=meta.maxValue)
                    elif meta.minLoaded :
                        img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=asciiHeader.image_extent, interpolation='none', vmax=meta.minValue)
                    elif meta.maxLoaded :
                        img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=asciiHeader.image_extent, interpolation='none', vmax=meta.maxValue)
                    else :
                        img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=asciiHeader.image_extent, interpolation='none')

                    if meta.showbars :
                        axins = inset_axes(ax,
                        width="5%",  # width = 5% of parent_bbox width
                        height="90%",  # height : 50%
                        loc='lower left',
                        bbox_to_anchor=(1.05, 0., 1, 1),
                        bbox_transform=ax.transAxes,
                        borderpad=0,
                        )
                        if meta.ticklist :
                            # Place a colorbar next to the map
                            cbar = fig.colorbar(img_plot, ticks=meta.ticklist, orientation='vertical', shrink=0.5, aspect=14, cax=axins)
                        else :
                            # Place a colorbar next to the map
                            cbar = fig.colorbar(img_plot, orientation='vertical', shrink=0.5, aspect=14, cax=axins)
                        if len(meta.label) > 0 :
                            #cbar.ax.set_label(meta.label)
                            cbar.ax.set_title(meta.label, loc='left') 
                        if meta.cbarLabel :
                            cbar.ax.set_yticklabels(meta.cbarLabel) 

                    if len(meta.title) > 0 :
                        ax.set_title(meta.title, y=0.90, x=0.05)   
                    if len(subtitles) >= idxRow and len(subtitles[idxRow-1]) > 0 :
                        ax.set_title(subtitles[idxRow-1])    
                
                    #ax.set_axis_off()
                    ax.grid(True, alpha=0.5)
                    ax.axes.xaxis.set_visible(False)
                    ax.axes.yaxis.set_visible(False)
                
                if meta.renderAs == "densitySpread" : 
                    ascii_data_array[ascii_data_array == asciiHeader.ascii_nodata] = np.nan
                    arithemticMean = np.nanmean(ascii_data_array, axis=1)
                    arithemticMean = np.nan_to_num(arithemticMean)
                    x = np.linspace(0, len(arithemticMean)-1, len(arithemticMean))
                    spl = spy.UnivariateSpline(x, arithemticMean)
                    xs = np.linspace(0, len(arithemticMean), 20)

                    x_new = np.linspace(0, len(arithemticMean), 500)
                    a_BSpline = spy.interpolate.make_interp_spline(xs, spl(xs))
                    if idxMerg == len(asciiHeadersLs)-1 :
                        ax.axes.invert_yaxis()
                    ax.plot(a_BSpline(x_new),x_new, label=meta.lineLabel)
                    if len(meta.lineLabel) > 0 :
                        ax.legend()
                    
                    if idxMerg == len(asciiHeadersLs)-1 :
                        # do this only once

                        def update_ticks(val, pos):
                            val *= meta.factor
                            return str(val)
                        ax.xaxis.set_major_formatter(mticker.FuncFormatter(update_ticks))

                        if meta.yTicklist :
                            ax.set_yticks(meta.yTicklist)
                        if meta.xTicklist :
                            ax.set_xticks(meta.xTicklist)

                        def applyTickLabelMapping(file, ref, tar, textformat, axis):
                            if len(file) > 0 and len(ref) > 0 and len(tar) > 0 :
                                lookup = readAxisLookup(file, ref, tar)
                                def update_ticks_fromLookup(val, pos):
                                    if val in lookup :
                                        if len(textformat) > 0 :
                                            newVal = lookup[val]
                                            return textformat.format(newVal)
                                        return str(lookup[val])
                                    return ''
                                axis.set_major_formatter(mticker.FuncFormatter(update_ticks_fromLookup))

                        applyTickLabelMapping(meta.YaxisMappingFile,
                                            meta.YaxisMappingRefColumn, 
                                            meta.YaxisMappingTarColumn, 
                                            meta.YaxisMappingFormat, 
                                            ax.yaxis)
                        applyTickLabelMapping(meta.XaxisMappingFile,
                                            meta.XaxisMappingRefColumn, 
                                            meta.XaxisMappingTarColumn, 
                                            meta.XaxisMappingFormat, 
                                            ax.xaxis)
                        if len(meta.yLabel) > 0 :
                            ax.set_ylabel(meta.yLabel) 
                        if len(meta.xLabel) > 0 :
                            ax.set_xlabel(meta.xLabel) 
                        if len(meta.title) > 0 :
                            ax.set_title(meta.title)   

    # save image and pdf 
    makeDir(out_path)
    if pdf :
        pdf.savefig(dpi=150)
    plt.savefig(out_path, dpi=250)
    plt.close(fig)

def readAxisLookup(filename, refCol, tarCol) :
    lookup = dict()
    with open(filename) as sourcefile:
        firstLine = True
        refColIdx = -1
        tarColIdx = -1
        for line in sourcefile:
            if firstLine :
                firstLine = False
                header = ReadHeader(line)
                refColIdx = header[refCol]
                tarColIdx = header[tarCol]
                continue
            out = loadLine(line,refColIdx,tarColIdx )
            lookup[float(out[0])] = float(out[1])
    return lookup

def loadLine(line, refColIdx, tarColIdx) :
    tokens = line.split(",")
    out = [""] * 2
    out[0] = tokens[refColIdx].strip()
    out[1] = tokens[tarColIdx].strip()
    return out

def ReadHeader(line) : 
    colDic = dict()
    tokens = line.split(",")
    i = -1
    for token in tokens :
        token = token.strip()
        i = i+1
        colDic[token] = i
    return colDic

def makeDir(out_path) :
    if not os.path.exists(os.path.dirname(out_path)):
        try:
            os.makedirs(os.path.dirname(out_path))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

if __name__ == "__main__":
    build()