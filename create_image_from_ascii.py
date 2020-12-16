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
from datetime import datetime
import collections
import errno
import gzip
from ruamel_yaml import YAML
from dataclasses import dataclass

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
    if len(sys.argv) > 1 and __name__ == "__main__":
        for arg in sys.argv[1:]:
            k, v = arg.split("=")
            if k == "path":
                pathId = v
            if k == "source" :
                sourceFolder = v
            if k == "out" :
                outputFolder = v
            
    if not sourceFolder :
        sourceFolder = PATHS[pathId]["sourcepath"]
    if not outputFolder :
        outputFolder = PATHS[pathId]["outputpath"]

    pngFolder = os.path.join(outputFolder, PATHS[pathId]["png-out"])
    pdfFolder = os.path.join(outputFolder,PATHS[pathId]["pdf-out"])


    # imageList, mergeList = readSetup(setupfile) 
    
    for root, dirs, files in os.walk(sourceFolder):
        if len(files) > 0 :
            print("root", root)
            print("dirs", dirs)
            scenario = os.path.basename(root)
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
    size: (float, float) 
    content: list

@dataclass
class Row:
    subtitle: str
    sharedColorBar: bool
    content: list

@dataclass
class Merge:
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
        for entry, entrydoc in doc.items() :
            if entry == "file" :
                mergeContent.append(readFile(entrydoc))
        return Merge(mergeContent)

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
                    elif entry == "file" :
                        imageContent.append(readFile(item["image"][entry]))
                    elif entry == "rows" :
                        imageContent = readRows(item["image"][entry])
                    elif entry == "merge" :
                        imageContent.append(readMerge(item["image"][entry]))
                if sizeX > 0 and sizeY > 0 :
                    imgSize = (sizeX, sizeY)
                imageList.append(Image(imagename, title, imgSize, imageContent))
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
    maxValue: float
    maxLoaded: bool
    minValue: float
    minLoaded: bool
    showbars: bool

def readMeta(meta_path, ascii_nodata, showCBar) :
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
    showbars = showCBar

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
    maxValue *= factor
    minValue *= factor
    return Meta(title, label, colormap, minColor, cMap,
                cbarLabel, factor, ticklist, maxValue, maxLoaded, minValue, minLoaded, showbars)


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
                    for f in col.content :
                        asciiHeader = readAsciiHeader(f.name)         
                        meta = readMeta(f.meta, asciiHeader.ascii_nodata, showBar) 
                        mergeHeaderList.append(asciiHeader)
                        mergeMetaList.append(meta)
                    asciiHeaderLs[(nplotRows, numCol)] = mergeHeaderList
                    metaLs[(nplotRows, numCol)] = mergeMetaList

            if numCol > nplotCols : 
                nplotCols = numCol
                
        elif type(content) is Merge:
            mergeHeaderList = list()
            mergeMetaList = list()
            for f in content.content :
                asciiHeader = readAsciiHeader(f.name)         
                meta = readMeta(f.meta, asciiHeader.ascii_nodata, True) 
                mergeHeaderList.append(asciiHeader)
                mergeMetaList.append(meta)
            nplotRows += 1
            nplotCols += 1 
            asciiHeaderLs[(nplotRows, nplotCols)] = mergeHeaderList
            metaLs[(nplotRows, nplotCols)] = mergeMetaList
            break
    # Plot data array
    # fig, ax = plt.subplots()
    # ax.set_title(title)
    
    fig, axs = plt.subplots(nrows=nplotRows, ncols=nplotCols, squeeze=False, sharex=True, sharey=True, figsize=image.size)
    fig.subplots_adjust(top=0.95, bottom=0.01, left=0.2, right=0.99, wspace=0.05)
    
    if image.title :
        fig.suptitle(image.title, fontsize='xx-large')

    #fig.suptitle('historical     future', fontsize=14, y=1.0, x=0.6)

    for idxRow in range(1,nplotRows+1) :
        # if len(subtitles) >= idxRow and len(subtitles[idxRow-1]) > 0:
        #     fig.suptitle(subtitles[idxRow-1])
        for idxCol in range(1,nplotCols+1) :
            ax = axs[idxRow-1][idxCol-1]
            asciiHeader = asciiHeaderLs[(idxRow,idxCol)]
            meta = metaLs[(idxRow,idxCol)]
            if type(asciiHeader) is not list :
                # Read in the ascii data array
                ascii_data_array = np.loadtxt(asciiHeader.ascii_path, dtype=np.float, skiprows=6)
        
                # Set the nodata values to nan
                ascii_data_array[ascii_data_array == asciiHeader.ascii_nodata] = np.nan

                # data is stored as an integer but scaled by a factor
                ascii_data_array *= meta.factor

                # set min color if given
                if len(meta.minColor) > 0 and not meta.cMap:
                    newColorMap = matplotlib.cm.get_cmap(meta.colormap, 256)
                    newcolors = newColorMap(np.linspace(0, 1, 256))
                    rgba = matplotlib.cm.colors.to_rgba(meta.minColor)
                    minColorVal = np.array([rgba])
                    newcolors[:1, :] = minColorVal
                    colorM = ListedColormap(newcolors)
                    if meta.minLoaded and meta.maxLoaded:
                        img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=asciiHeader.image_extent, interpolation='none', vmin=meta.minValue, vmax=meta.maxValue)
                    elif meta.minLoaded :
                        img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=asciiHeader.image_extent, interpolation='none', vmax=meta.minValue)
                    elif meta.maxLoaded :
                        img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=asciiHeader.image_extent, interpolation='none', vmax=meta.maxValue)
                    else :
                        img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=asciiHeader.image_extent, interpolation='none')

                # Get the img object in order to pass it to the colorbar function
                elif meta.cMap :
                    colorM = ListedColormap(meta.cMap)
                    if meta.minLoaded and meta.maxLoaded:
                        img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=asciiHeader.image_extent, interpolation='none', vmin=meta.minValue, vmax=meta.maxValue)
                    elif meta.minLoaded :
                        img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=asciiHeader.image_extent, interpolation='none', vmax=meta.minValue)
                    elif meta.maxLoaded :
                        img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=asciiHeader.image_extent, interpolation='none', vmax=meta.maxValue)
                    else :
                        img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=asciiHeader.image_extent, interpolation='none')
                else :
                    if meta.minLoaded and meta.maxLoaded:
                        img_plot = ax.imshow(ascii_data_array, cmap=meta.colormap, extent=asciiHeader.image_extent, interpolation='none', vmin=meta.minValue, vmax=meta.maxValue)
                    elif meta.minLoaded :
                        img_plot = ax.imshow(ascii_data_array, cmap=meta.colormap, extent=asciiHeader.image_extent, interpolation='none', vmax=meta.minValue)
                    elif meta.maxLoaded :
                        img_plot = ax.imshow(ascii_data_array, cmap=meta.colormap, extent=asciiHeader.image_extent, interpolation='none', vmax=meta.maxValue)
                    else :
                        img_plot = ax.imshow(ascii_data_array, cmap=meta.colormap, extent=asciiHeader.image_extent, interpolation='none')

                if meta.showbars :
                    ax_divider = make_axes_locatable(ax)
                    cax = ax_divider.append_axes("right", size="7%", pad="2%")
                    if meta.ticklist :
                        # Place a colorbar next to the map
                        cbar = fig.colorbar(img_plot, ticks=meta.ticklist, orientation='vertical', shrink=0.5, aspect=14, cax=cax)
                    else :
                        # Place a colorbar next to the map
                        cbar = fig.colorbar(img_plot, orientation='vertical', shrink=0.5, aspect=14, cax=cax)
                    cbar.set_label(meta.label)
                    if meta.cbarLabel :
                        cbar.ax.set_yticklabels(meta.cbarLabel) 

                    if len(subtitles) >= idxRow and len(subtitles[idxRow-1]) > 0 :
                        ax.set_title(subtitles[idxRow-1])                        
                ax.set_axis_off()
                ax.grid(True, alpha=0.5)
    
    plt.tight_layout()
    
    # save image and pdf 
    makeDir(out_path)
    if pdf :
        pdf.savefig(dpi=150)
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