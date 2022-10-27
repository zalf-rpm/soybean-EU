#!/usr/bin/python
# -*- coding: UTF-8

import sys
import os
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
import errno
import gzip
from ruamel_yaml import YAML
from dataclasses import dataclass
import typing
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
import cartopy.feature as cfeature

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
DEFAULT_DPI_PNG=300
PROJECTION="3035" # epsg code

def build() :
    "main"

    pathId = USER
    sourceFolder = ""
    outputFolder = ""
    generatePDF = False
    png_dpi = DEFAULT_DPI_PNG
    projection = PROJECTION
    if len(sys.argv) > 1 and __name__ == "__main__":
        for arg in sys.argv[1:]:
            k, v = arg.split("=")
            if k == "path":
                pathId = v
            if k == "source" :
                sourceFolder = v
            if k == "out" :
                outputFolder = v
            if k == "generatePDF" :
                generatePDF = bool(v)
            if k == "dpi" :
                png_dpi = int(v)
            if k == "projection" :
                projection = v
            
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
                    createSubPlot(image, outpath,png_dpi, projection, pdf=pdf)
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
                        createImgFromMeta( filepath, metapath, out_path, png_dpi, projection, pdf=pdf)
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
    inserts: list
    customLegend: list

@dataclass
class Insert:
    height: str
    width: str
    loc: str
    bboxToAnchor: typing.Tuple[float, float, float, float]
    content: list

@dataclass
class File:
    name: str
    meta: str
    inserts: list

@dataclass
class CustomLegend:
    text: str
    color: str
    hatch: str

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
        inserts = list()
        return File(filepath, metapath, inserts)   
    def readCustomLegend(doc) :
        text = ""
        color = "white"
        hatch = ""
        for entries in doc :
            for entry in entries :
                if entry == "text" :
                    text = entries["text"]
                if entry == "color" :
                    color = entries["color"]
                if entry == "hatch" :
                    hatch = entries["hatch"]
        return CustomLegend(text, color, hatch)
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
                            if entry == "insert" :
                                rowList[-1].inserts.append(readInsert(entries["insert"]))
                    rowContent.append(Row(subtitle, sharedColorBar, rowList))
        return rowContent

    def readMerge(doc) : 
        mergeContent = list()
        mintransparency = list()
        transparencyfactorList = list()
        inserts = list()
        customLegend = list()
        for entry in doc :
            for f in entry:
                if f == "file" :
                    mergeContent.append(readFile(entry["file"]))
                    mintransparency.append(1.0)
                    transparencyfactorList.append(1.0)
                if f == "customLegend" :
                    customLegend.append(readCustomLegend(entry["customLegend"]))
                if f == "mintransparent" :
                    val = float(entry["mintransparent"])
                    mintransparency[len(mintransparency) - 1] = val
                if f == "transparencyfactor" :
                    val = float(entry["transparencyfactor"])
                    transparencyfactorList[len(transparencyfactorList) - 1] = val
        return Merge(mintransparency, transparencyfactorList, mergeContent, inserts, customLegend)

    def readInsert(doc) :
        height = "30%"
        width = "30%"
        loc = "lower left"
        bbTA = [0,0,1,1]
        insertContent = list()
        for entry in doc :
            if entry == "height" :
                height = doc["height"]
            if entry == "width" :
                width = doc["width"]
            if entry == "loc" :
                loc = doc["loc"]
            if entry == "bboxToAnchorX" :
                bbTA[0] = float(doc["bboxToAnchorX"])
            if entry == "bboxToAnchorY" :
                bbTA[1] = float(doc["bboxToAnchorY"])
            if entry == "bboxToAnchorXext" :
                bbTA[2] = float(doc["bboxToAnchorXext"])
            if entry == "bboxToAnchorYext" :
                bbTA[3] = float(doc["bboxToAnchorYext"])
            if entry == "file" :
                insertContent.append(readFile(doc["file"]))
            if entry == "merge" :
                insertContent.append(readMerge(doc["merge"]))

        return Insert(height, width, loc,(bbTA[0], bbTA[1], bbTA[2],bbTA[3] ), insertContent )

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
                    elif entry == "insert" :
                        imageContent[-1].inserts.append(readInsert(item["image"][entry]))
                if sizeX > 0 and sizeY > 0 :
                    imgSize = (sizeX, sizeY)
                imageList.append(Image(imagename, title, imgSize,
                                adjBottom, adjTop, adRight, adLeft, adhspace, adwspace, imageContent))
    return imageList


def createImgFromMeta(ascii_path, meta_path, out_path, png_dpi, projectionID, pdf=None) :

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
    colorlisttype = None
    cbarLabel = None
    factor = 1
    ticklist = None
    maxValue = ascii_nodata
    maxLoaded = False
    minValue = ascii_nodata
    minLoaded = False
    border = False
    showbars = True

    if os.path.isfile(meta_path)  :
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
                elif item == "colorlist" :
                    cMap = doc
                elif item == "colorlisttype" :
                    colorlisttype = doc
                elif item == "cbarLabel" :
                    cbarLabel = doc
                elif item == "ticklist" :
                    ticklist = list()
                    for i in doc :
                        ticklist.append(float(i))
                elif item == "border" :
                    border = bool(doc)
                elif item == "showbar" :
                    showbars = bool(doc)
    if colormap == "temperature" :
    # add ticklist, add colorlist if not already given
        if cMap == None :
            cMap = temphexMap
            if not minLoaded :
                minLoaded = True
                minValue = -46
            if not maxLoaded :
                maxLoaded = True
                maxValue = 56

    # Read in the ascii data array
    ascii_data_array = np.loadtxt(ascii_path, dtype=np.float, skiprows=6)

    if ascii_data_array.ndim == 1 :
        reshaped_to_2d = np.reshape(ascii_data_array, (ascii_rows,-1 ))
        ascii_data_array = reshaped_to_2d

    # Set the nodata values to nan
    ascii_data_array[ascii_data_array == ascii_nodata] = np.nan

    # data is stored as an integer but scaled by a factor
    ascii_data_array *= factor
    maxValue *= factor
    minValue *= factor
    if border :
        ascii_data_array = np.flip(ascii_data_array, 0)

    image_extent = [
        ascii_xll, ascii_xll + ascci_cols * ascii_cs,
        ascii_yll, ascii_yll + ascii_rows * ascii_cs]
    
    # Plot data array
    projection = None
    if border :
        projection = ccrs.epsg(projectionID)
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1, projection=projection)

    ax.set_title(title)
    if border :
        ax.set_extent(image_extent, crs=projection)

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
        if colorlisttype == "LinearSegmented":
            colorM = matplotlib.colors.LinearSegmentedColormap.from_list("mycmap", cMap)
        else :
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

    if showbars :
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
    if border :
        ax.add_feature(cfeature.COASTLINE.with_scale('10m'), linewidth=0.2)
        ax.add_feature(cfeature.BORDERS.with_scale('10m'), linewidth=0.2)
        ax.add_feature(cfeature.OCEAN.with_scale('50m'))

    # save image and pdf 
    makeDir(out_path)
    if pdf :
        pdf.savefig()
    plt.savefig(out_path, dpi=png_dpi)
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
    colorlisttype : str
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
    lineColor: str
    lineHatch: str
    lineLabelAnchorX: float
    lineLabelAnchorY: float
    lineLabelLoc: str
    xLabel: str
    yLabel: str
    YaxisMappingFile: str
    YaxisMappingRefColumn: str
    YaxisMappingTarColumn: str
    YaxisMappingTarColumnAsF: bool
    YaxisMappingFormat: str
    XaxisMappingFile: str
    XaxisMappingRefColumn: str
    XaxisMappingTarColumn: str
    XaxisMappingTarColumnAsF: bool
    XaxisMappingFormat: str
    densityReduction: int
    densityFactor: float
    occurrenceIndex: list
    yTitle: float
    xTitle: float
    removeEmptyColumns: bool
    border: bool
    violinOffset: int
    violinOffsetDistance: int
    violinHatch: str

def readMeta(meta_path, ascii_nodata, showCBar) :
    title="" 
    label=""
    colormap = 'viridis'
    minColor = ""
    cMap = None
    cbarLabel = None
    factor = 1.0
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
    lineColor = ""
    lineLabelAnchorX = 1.0
    lineLabelAnchorY = 1.0
    lineLabelLoc = "none"
    xLabel = ""
    yLabel = ""
    YaxisMappingFile = ""
    YaxisMappingRefColumn = ""
    YaxisMappingTarColumn = ""
    YaxisMappingTarColumnAsF = True
    YaxisMappingFormat = ""
    XaxisMappingFile = ""
    XaxisMappingRefColumn = ""
    XaxisMappingTarColumn = ""
    XaxisMappingTarColumnAsF = True
    XaxisMappingFormat = ""
    densityReduction = -1
    densityFactor = 1.0
    yTitle = 1
    xTitle = 1
    removeEmptyColumns = False
    border = False
    colorlisttype = None
    occurrenceIndex = None
    violinOffset = 2
    violinOffsetDistance = 2
    violinHatch = ""
    lineHatch = ""

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
            elif item == "densityReduction" :
                densityReduction = int(doc)
            elif item == "densityFactor" :
                densityFactor = float(doc)
            elif item == "occurrenceIndex" :
                occurrenceIndex = list()
                for i in doc :
                    occurrenceIndex.append(int(i))
            elif item == "mintransparent" :
                mintransparent = float(doc)
            elif item == "transparencyfactor" :
                transparencyfactor = float(doc)
            elif item == "colorlist" :
                cMap = doc
            elif item == "colorlisttype" :
                colorlisttype = doc
            elif item == "renderAs" :
                renderAs = doc
            elif item == "cbarLabel" :
                cbarLabel = doc
            elif item == "lineLabel" :
                lineLabel = doc
            elif item == "lineColor" :
                lineColor = doc

            elif item == "violinOffset":
                violinOffset = int(doc)
            elif item == "violinOffsetDistance":
                violinOffsetDistance = int(doc)
            elif item == "violinHatch":
                violinHatch = doc
            elif item == "lineHatch":
                lineHatch = doc
            elif item == "lineLabelAnchorX":
                lineLabelAnchorX = float(doc)
            elif item == "lineLabelAnchorY":
                lineLabelAnchorY = float(doc)
            elif item == "lineLabelLoc":
                lineLabelLoc = doc
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
            elif item == "YaxisMappingTarColumnAsF" :
                YaxisMappingTarColumnAsF = bool(doc)
            elif item == "YaxisMappingFormat" :
                YaxisMappingFormat = doc
            elif item == "XaxisMappingFile" :
                XaxisMappingFile = doc
            elif item == "XaxisMappingRefColumn" :
                XaxisMappingRefColumn = doc
            elif item == "XaxisMappingTarColumn" :
                XaxisMappingTarColumn = doc
            elif item == "XaxisMappingTarColumnAsF" :
                XaxisMappingTarColumnAsF = bool(doc)
            elif item == "XaxisMappingFormat" :
                XaxisMappingFormat = doc
            elif item == "yTitle" :
                yTitle = float(doc) 
            elif item == "border" :
                border = bool(doc)
            elif item == "xTitle" :
                xTitle = float(doc)
            elif item == "removeEmptyColumns" :
                removeEmptyColumns = bool(doc)
            elif item == "showbar" :
                showbars = bool(doc)
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

    def replaceLinebreaks(str ) :
        cpStr = str.replace("\\n", "\n") 
        return cpStr

    title = replaceLinebreaks(title)
    label = replaceLinebreaks(label)
    lineLabel  = replaceLinebreaks(lineLabel)
    xLabel = replaceLinebreaks(xLabel)
    yLabel = replaceLinebreaks(yLabel)
    if colormap == "temperature" :
    # add ticklist, add colorlist if not already given
        if cMap == None :
            cMap = temphexMap

    return Meta(title, label, colormap, minColor, cMap, colorlisttype,
                cbarLabel, factor, ticklist,yTicklist,xTicklist, maxValue, maxLoaded, minValue, minLoaded, 
                showbars, mintransparent, renderAs, transparencyfactor, 
                lineLabel, lineColor, lineHatch, lineLabelAnchorX, lineLabelAnchorY, lineLabelLoc,
                xLabel, yLabel,
                YaxisMappingFile,YaxisMappingRefColumn,YaxisMappingTarColumn,YaxisMappingTarColumnAsF,YaxisMappingFormat,
                XaxisMappingFile,XaxisMappingRefColumn,XaxisMappingTarColumn,XaxisMappingTarColumnAsF,XaxisMappingFormat,
                densityReduction, densityFactor, occurrenceIndex,
                yTitle,xTitle,removeEmptyColumns,border,
                violinOffset,violinOffsetDistance, violinHatch)

# temperature color map
temphexMap = [
"#5e003e", # 56
"#5e3566", # 54
"#803596", # 52
"#9a3596", # 50
"#8c274f", # 48
"#9d3e4f", # 46
"#b54479", # 44
"#c75197", # 42
"#c0609e", # 40
"#dc5581", # 38
"#dd573f", # 36
"#dc4b42", # 34
"#e37947", # 32
"#e68b4b", # 30
"#f3bf54", # 28
"#f7d65c", # 26
"#f4e75f", # 24
"#f5ee61", # 22
"#e1eab8", # 20
"#c9d968", # 18
"#a2c96b", # 16
"#75b360", # 14
"#4e8d59", # 12
"#65947f", # 10
"#6dbb95", # 8
"#71b973", # 6
"#7dbc74", # 4
"#83c18c", # 2
"#c0e2f0", # 0
"#addbef", # -2
"#8dd0f3", # -4
"#84bde6", # -6
"#759fd1", # -8
"#617bb8", # -10
"#5562a8", # -12
"#51559f", # -14
"#6b549e", # -16
"#7d569d", # -18
"#8e579d", # -20
"#a05a9d", # -22
"#985198", # -24
"#884593", # -26
"#724184", # -28
"#593e6e", # -30
"#595582", # -32
"#596990", # -34
"#5a7a9e", # -36
"#5e8caa", # -38
"#5f9cb6", # -40
"#62afc4", # -42
"#69c0d1", # -44
"#83c9d8", # -46
]
tempMap = [56, 54, 52, 50, 48, 46, 44, 42, 40, 38, 
           36, 34, 32, 30, 28, 26, 24, 22, 20, 18,
           16, 14, 12, 10, 8, 6, 4, 2, 0, -2, -4, 
           -6, -8, -10, -12, -14, -16, -18, -20, -22, -24, 
           -26, -28, -30, -32, -34, -36, -38, -40, -42, -44, -46]
def prepareColor() :
    temphexMap.reverse()
    

def createSubPlot(image, out_path, png_dpi, projectionID, pdf=None) :
        
    nplotRows = 0
    nplotCols = 0
    asciiHeaderLs = dict()
    metaLs = dict()
    asciiHeaderInsertLs = dict()
    metaInsertLs = dict()
    subPositions = dict()
    subtitles = list()
    customLegendls = dict()

    def readContent(content) :
        asciiHeaderList = list()
        metaList = list()
        insertAsciiHeaderList = list()
        insertMetaList = list()
        insertPosition = dict()
        if type(content) is File :
            name = content.name
            metaName = content.meta
            asciiHeader = readAsciiHeader(name)
            meta = readMeta(metaName, asciiHeader.ascii_nodata, True)  
            asciiHeaderList.append(asciiHeader)
            metaList.append(meta)
            if len(content.inserts) > 0 :
                ah, met, _, _, iDic = readContent(content.inserts[0])
                for i in range(len(ah)):
                    insertAsciiHeaderList.append(ah[i])
                    insertMetaList.append(met[i])
                insertPosition = iDic
        elif type(content) is Merge:
            transparencyList = content.mintransparency
            transparencyfactorList = content.transparencyfactor
            idxT = 0
            for f in content.content :
                asciiHeader = readAsciiHeader(f.name)         
                meta = readMeta(f.meta, asciiHeader.ascii_nodata, True) 
                meta.mintransparent = min(transparencyList[idxT], meta.mintransparent)
                meta.transparencyfactor = transparencyfactorList[idxT]
                asciiHeaderList.append(asciiHeader)
                metaList.append(meta)
                idxT += 1
            if len(content.inserts) > 0 :
                ah, met, _, _, iDic = readContent(content.inserts[0])
                for i in range(len(ah)):
                    insertAsciiHeaderList.append(ah[i])
                    insertMetaList.append(met[i])
                insertPosition = iDic
        elif type(content) is Insert:
            insertPosition["height"] = content.height
            insertPosition["width"] = content.width
            insertPosition["loc"] = content.loc
            insertPosition["bbox_to_anchor"] = content.bboxToAnchor
            ah, met, _, _, _ = readContent(content.content[0])
            for i in range(len(ah)):
                asciiHeaderList.append(ah[i])
                metaList.append(met[i])

        return (asciiHeaderList,metaList,insertAsciiHeaderList,insertMetaList, insertPosition)

    for content in image.content :
        if type(content) is File or type(content) is Merge:
            asciiHeader, meta, asciiHeaderInsert, metaInsert, subPosi = readContent(content)
            nplotRows += 1
            nplotCols += 1             
            asciiHeaderLs[(nplotRows, nplotCols)] = asciiHeader 
            metaLs[(nplotRows, nplotCols)] = meta
            asciiHeaderInsertLs[(nplotRows, nplotCols)] = asciiHeaderInsert
            metaInsertLs[(nplotRows, nplotCols)] = metaInsert
            subPositions[(nplotRows, nplotCols)] = subPosi
            if type(content) is Merge :
                customLegendls[(nplotRows, nplotCols)] = content.customLegend
            break
        elif type(content) is Row :
            nplotRows += 1
            numCol = 0
            subtitles.append(content.subtitle)
            shareCBar = content.sharedColorBar
            lastCol = len(content.content)
            for col in content.content :
                numCol += 1
                #showBar = not shareCBar or (numCol == lastCol) 
                if type(col) is File or type(col) is Merge :
                    asciiHeader, meta, asciiHeaderInsert, metaInsert, subPosi = readContent(col)
                    asciiHeaderLs[(nplotRows, numCol)] = asciiHeader 
                    metaLs[(nplotRows, numCol)] = meta
                    asciiHeaderInsertLs[(nplotRows, numCol)] = asciiHeaderInsert
                    metaInsertLs[(nplotRows, numCol)] = metaInsert
                    subPositions[(nplotRows, numCol)] = subPosi
                    for m in metaLs[(nplotRows, numCol)] :
                        #m.showbars = showBar
                        m.showbars = (shareCBar and numCol == lastCol) or (not shareCBar and m.showbars)
                    if type(col) is Merge :
                        customLegendls[(nplotRows, numCol)] = col.customLegend
            if numCol > nplotCols : 
                nplotCols = numCol
                
    # Plot data array
    projection = None
    if meta[0].border :
        projection = ccrs.epsg(projectionID)
    fig, axs = plt.subplots(nrows=nplotRows, ncols=nplotCols, squeeze=False, sharex=True, sharey=True, figsize=image.size, subplot_kw={'projection': projection})

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

    for idxRow in range(1,nplotRows+1) :
        for idxCol in range(1,nplotCols+1) :
            ax = axs[idxRow-1][idxCol-1]
            asciiHeaders = asciiHeaderLs[(idxRow,idxCol)]
            metas = metaLs[(idxRow,idxCol)]
            customLegend = None
            if (idxRow,idxCol) in customLegendls :
                customLegend = customLegendls[(idxRow,idxCol)]
            for idxMerg in range(len(asciiHeaders)) :
                asciiHeader = asciiHeaders[idxMerg]
                meta = metas[idxMerg]
                subtitle = ""
                if len(subtitles) >= idxRow and len(subtitles[idxRow-1]) > 0 :
                    subtitle = subtitles[idxRow-1]
                onlyOnce = (idxMerg == len(asciiHeaders)-1)
                plotLayer(fig, ax, idxCol, nplotCols, asciiHeader, meta, subtitle, onlyOnce, projectionID, customLegend=customLegend)
            if (len(metaInsertLs[(idxRow,idxCol)]) > 0 and 
                len(asciiHeaderInsertLs[(idxRow,idxCol)]) > 0 and 
                len(subPositions[(idxRow,idxCol)]) > 0) :

                asciiHeaders = asciiHeaderInsertLs[(idxRow,idxCol)]
                metas = metaInsertLs[(idxRow,idxCol)]
                subPosi = subPositions[(idxRow,idxCol)]
                
                inset_ax = inset_axes(ax,
                                    # height="{:5.2f}%".format(subPosi["height"]), 
                                    # width="{:5.2f}%".format(subPosi["width"]),
                                    # loc=subPosi["loc"])
                                    # height="30%",
                                    # width="30%",
                                    #width="50%", height="100%",
                                    width=subPosi["width"], height=subPosi["height"],
                                    bbox_to_anchor=subPosi["bbox_to_anchor"],
                                    #bbox_to_anchor=(-0.565, 0., 1, 1), #outside
                                    #bbox_to_anchor=(0, 0.1, .24, .8), # inside
                                    #bbox_to_anchor=(.057, .4, .233, .5), #looks ok
                                    #bbox_transform=ax.transAxes, loc=3,
                                    bbox_transform=ax.transAxes, 
                                    loc=subPosi["loc"],
                                    borderpad=0
                                    )
                fontsize = 10
                axlabelpad = 1
                axtickpad = 0
                for idxMerg in range(len(asciiHeaders)) :
                    asciiHeader = asciiHeaders[idxMerg]
                    meta = metas[idxMerg]
                    subtitle = ""
                    onlyOnce = (idxMerg == len(asciiHeaders)-1)
                    plotLayer(fig, inset_ax, idxCol, nplotCols, asciiHeader, meta, subtitle, onlyOnce, projectionID, fontsize=fontsize, axlabelpad=axlabelpad, axtickpad=axtickpad)


    # save image and pdf 
    makeDir(out_path)
    if pdf :
        pdf.savefig(dpi=150)
    plt.savefig(out_path, dpi=png_dpi)
    plt.close(fig)

def plotLayer(fig, ax, idxCol, numCols, asciiHeader, meta, subtitle, onlyOnce, projectionID, customLegend=None, fontsize = 10, axlabelpad = None, axtickpad = None) :
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
        if meta.colorlisttype == "LinearSegmented":
            newColorMap = matplotlib.colors.LinearSegmentedColormap.from_list("mycmap", meta.cMap)
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
        elif meta.transparencyfactor < 1.0 or meta.mintransparent < 1.0:
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
        if meta.removeEmptyColumns :
            ascii_data_array = ascii_data_array[:,~np.isnan(ascii_data_array).all(axis=0)]
        rowcol = ascii_data_array.shape
        image_extent = [
                asciiHeader.ascii_xll, asciiHeader.ascii_xll + rowcol[1] * asciiHeader.ascii_cs,
                asciiHeader.ascii_yll, asciiHeader.ascii_yll + asciiHeader.ascii_rows * asciiHeader.ascii_cs] 
        # data is stored as an integer but scaled by a factor
        ascii_data_array *= meta.factor
        projection = None
        if meta.border :
            ascii_data_array = np.flip(ascii_data_array, 0)
            projection = ccrs.epsg(projectionID)
            ax.set_extent(image_extent, crs=projection)


        if meta.minLoaded and meta.maxLoaded:
            img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmin=meta.minValue, vmax=meta.maxValue)
        elif meta.minLoaded :
            img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmax=meta.minValue)
        elif meta.maxLoaded :
            img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmax=meta.maxValue)
        else :
            img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none')

        if meta.border :
            ax.add_feature(cfeature.COASTLINE.with_scale('10m'), linewidth=0.2)
            ax.add_feature(cfeature.BORDERS.with_scale('10m'), linewidth=0.2)
            ax.add_feature(cfeature.OCEAN.with_scale('50m'))
        if meta.showbars :
            axins = inset_axes(ax,
            width="5%",  # width = 5% of parent_bbox width
            height="85%",  # height : 50% --if more than 3 lable lines then set to 85% 
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
                cbar.ax.set_title(meta.label, loc='left', fontsize=fontsize) 
            if meta.cbarLabel :
                cbar.ax.set_yticklabels(meta.cbarLabel) 

        if len(meta.title) > 0 :
            ax.set_title(meta.title, y=meta.yTitle, x=meta.xTitle)   
        if len(subtitle) > 0 :
            ax.set_title(subtitle)    
    
        #ax.set_axis_off()
        
        ax.grid(False)
        ax.axes.xaxis.set_visible(False)
        ax.axes.yaxis.set_visible(True)
  
        if idxCol != 1 :
            ax.axes.yaxis.set_visible(False)

        if onlyOnce :

            if meta.yTicklist :
                ax.set_yticks(meta.yTicklist)
            if axtickpad != None :
                ax.yaxis.set_tick_params(which='major', pad=axtickpad)

            applyTickLabelMapping(meta.YaxisMappingFile,
                                meta.YaxisMappingRefColumn, 
                                meta.YaxisMappingTarColumn, 
                                meta.YaxisMappingTarColumnAsF,
                                meta.YaxisMappingFormat, 
                                ax.yaxis)

            if len(meta.yLabel) > 0 :
                ax.set_ylabel(meta.yLabel, labelpad=axlabelpad) 

    if meta.renderAs == "densitySpread" : 
        # if onlyOnce :
        #     ax.axes.invert_yaxis()                    
        ascii_data_array[ascii_data_array == asciiHeader.ascii_nodata] = np.nan
        arithemticMean = np.nanmean(ascii_data_array, axis=1)
        arithemticMean = np.nan_to_num(arithemticMean)
        arithemticMean *= meta.densityFactor
        maxV = np.max(arithemticMean)
        minV = np.min(arithemticMean)
        if meta.densityReduction > 0 :
            y = np.linspace(0, len(arithemticMean)-1, len(arithemticMean))
            spl = spy.UnivariateSpline(y, arithemticMean)    
            ys = np.linspace(0, len(arithemticMean), meta.densityReduction)
            y_new = np.linspace(0, len(arithemticMean), 500)
            a_BSpline = spy.interpolate.make_interp_spline(ys, spl(ys))
            x_new = a_BSpline(y_new)
            x_new[x_new < minV] = minV
            x_new[x_new > maxV] = maxV
            if len(meta.lineColor) > 0 :
                ax.plot(x_new,y_new, label=meta.lineLabel, color=meta.lineColor)
            else :
                ax.plot(x_new,y_new, label=meta.lineLabel)
        else :
            y = np.linspace(0, len(arithemticMean)-1, len(arithemticMean))
            if len(meta.lineColor) > 0 :
                ax.plot(arithemticMean, y, label=meta.lineLabel, color=meta.lineColor)
            else :
                ax.plot(arithemticMean, y, label=meta.lineLabel)

        if len(meta.lineLabel) > 0 :
            if meta.lineLabelLoc == "none" :
                ax.legend(fontsize=6, handlelength=1)
            else :
                ax.legend(fontsize=6, handlelength=1, bbox_to_anchor=(meta.lineLabelAnchorX, meta.lineLabelAnchorY), loc=meta.lineLabelLoc)
        
        ax.axes.xaxis.set_visible(False)
        if idxCol != 1 :
            ax.axes.yaxis.set_visible(False)

        if onlyOnce :
            # do this only once

            def update_ticks(val, pos):
                val *= (1/meta.densityFactor)
                val *= meta.factor
                return str(val)
            ax.xaxis.set_major_formatter(mticker.FuncFormatter(update_ticks))

            if meta.yTicklist :
                ax.set_yticks(meta.yTicklist)
            if meta.xTicklist :
                ax.set_xticks(meta.xTicklist)

            if axtickpad != None :
                ax.yaxis.set_tick_params(which='major', pad=axtickpad)
                ax.xaxis.set_tick_params(which='major', pad=axtickpad)

            # def applyTickLabelMapping(file, ref, tar, tarAsFloat, textformat, axis):
            #     if len(file) > 0 and len(ref) > 0 and len(tar) > 0 :
            #         lookup = readAxisLookup(file, ref, tar, tarAsFloat)
            #         def update_ticks_fromLookup(val, pos):
            #             if val in lookup :
            #                 if len(textformat) > 0 :
            #                     newVal = lookup[val]
            #                     return textformat.format(newVal)
            #                 return str(lookup[val])
            #             return ''
            #         axis.set_major_formatter(mticker.FuncFormatter(update_ticks_fromLookup))

            applyTickLabelMapping(meta.YaxisMappingFile,
                                meta.YaxisMappingRefColumn, 
                                meta.YaxisMappingTarColumn, 
                                meta.YaxisMappingTarColumnAsF,
                                meta.YaxisMappingFormat, 
                                ax.yaxis)
            applyTickLabelMapping(meta.XaxisMappingFile,
                                meta.XaxisMappingRefColumn, 
                                meta.XaxisMappingTarColumn, 
                                meta.XaxisMappingTarColumnAsF,
                                meta.XaxisMappingFormat, 
                                ax.xaxis)
            if len(meta.yLabel) > 0 :
                ax.set_ylabel(meta.yLabel, labelpad=axlabelpad) 
            if len(meta.xLabel) > 0 :
                ax.set_xlabel(meta.xLabel, labelpad=axlabelpad) 
            if len(meta.title) > 0 :
                ax.set_title(meta.title, y=meta.yTitle, x=meta.xTitle)   
            for item in ([ax.xaxis.label, ax.yaxis.label] +
                            ax.get_xticklabels() + ax.get_yticklabels()):
                item.set_fontsize(fontsize)

    if meta.renderAs == "occurrenceSpread" : 
        # TODO
        if onlyOnce :
            ax.axes.invert_yaxis()                    
        ascii_data_array[ascii_data_array == asciiHeader.ascii_nodata] = np.nan

        occIndex = 0
        if meta.occurrenceIndex != None :
            occIndex = meta.occurrenceIndex[0]
        numInArray = np.count_nonzero(~np.isnan(ascii_data_array), axis=1)
        numXInArray = np.count_nonzero((ascii_data_array == occIndex), axis=1)
        occurenceArray = np.array([0.0] * len(numInArray))
        for idx in range(len(numInArray)) : 
            if numInArray[idx] > 0 :
                occurenceArray[idx] = float(numXInArray[idx]) * 100.0 / float(numInArray[idx])
        
        occurenceArray *= meta.densityFactor
        maxV = np.max(occurenceArray)
        minV = np.min(occurenceArray)
        if meta.densityReduction > 0 :
            y = np.linspace(0, len(occurenceArray)-1, len(occurenceArray))
            spl = spy.UnivariateSpline(y, occurenceArray)    
            ys = np.linspace(0, len(occurenceArray), meta.densityReduction)
            y_new = np.linspace(0, len(occurenceArray), 500)
            a_BSpline = spy.interpolate.make_interp_spline(ys, spl(ys))
            x_new = a_BSpline(y_new)
            x_new[x_new < minV] = minV
            x_new[x_new > maxV] = maxV
            if len(meta.lineColor) > 0 :
                ax.plot(x_new,y_new, label=meta.lineLabel, color=meta.lineColor)
            else :
                ax.plot(x_new,y_new, label=meta.lineLabel)
        else :
            y = np.linspace(0, len(occurenceArray)-1, len(occurenceArray))
            if len(meta.lineColor) > 0 :
                ax.plot(occurenceArray, y, label=meta.lineLabel, color=meta.lineColor)
            else :
                ax.plot(occurenceArray, y, label=meta.lineLabel)

        if len(meta.lineLabel) > 0 :
            ax.legend(fontsize=6, handlelength=1)
            #ax.legend(fontsize=fontsize, handlelength=1, bbox_to_anchor=(1.05, 1), loc='upper left')
        
        if onlyOnce :
            # do this only once

            def update_ticks(val, pos):
                val *= (1/meta.densityFactor)
                val *= meta.factor
                return str(val)
            ax.xaxis.set_major_formatter(mticker.FuncFormatter(update_ticks))

            if meta.yTicklist :
                ax.set_yticks(meta.yTicklist)
            if meta.xTicklist :
                ax.set_xticks(meta.xTicklist)

            if axtickpad != None :
                ax.yaxis.set_tick_params(which='major', pad=axtickpad)
                ax.xaxis.set_tick_params(which='major', pad=axtickpad)

            # def applyTickLabelMapping(file, ref, tar, textformat, axis):
            #     if len(file) > 0 and len(ref) > 0 and len(tar) > 0 :
            #         lookup = readAxisLookup(file, ref, tar)
            #         def update_ticks_fromLookup(val, pos):
            #             if val in lookup :
            #                 if len(textformat) > 0 :
            #                     newVal = lookup[val]
            #                     return textformat.format(newVal)
            #                 return str(lookup[val])
            #             return ''
            #         axis.set_major_formatter(mticker.FuncFormatter(update_ticks_fromLookup))

            applyTickLabelMapping(meta.YaxisMappingFile,
                                meta.YaxisMappingRefColumn, 
                                meta.YaxisMappingTarColumn, 
                                meta.YaxisMappingTarColumnAsF,
                                meta.YaxisMappingFormat, 
                                ax.yaxis)
            applyTickLabelMapping(meta.XaxisMappingFile,
                                meta.XaxisMappingRefColumn, 
                                meta.XaxisMappingTarColumn, 
                                meta.XaxisMappingTarColumnAsF,
                                meta.XaxisMappingFormat, 
                                ax.xaxis)
            if len(meta.yLabel) > 0 :
                ax.set_ylabel(meta.yLabel, labelpad=axlabelpad) 
            if len(meta.xLabel) > 0 :
                ax.set_xlabel(meta.xLabel, labelpad=axlabelpad) 
            if len(meta.title) > 0 :
                ax.set_title(meta.title, y=meta.yTitle, x=meta.xTitle)   
            for item in ([ax.xaxis.label, ax.yaxis.label] +
                            ax.get_xticklabels() + ax.get_yticklabels()):
                item.set_fontsize(fontsize)

    if meta.renderAs == "violinOccurrenceSpread" : 
       
        ascii_data_array[ascii_data_array == asciiHeader.ascii_nodata] = np.nan

        numInRowC = np.count_nonzero(~np.isnan(ascii_data_array), axis=1)
        numberOfBucketsC = len(numInRowC)
        if meta.densityReduction > 0 :
            numberOfBucketsC = meta.densityReduction        
        numRowsC = len(numInRowC)
        inBucketC = int(numRowsC / numberOfBucketsC)
        if numRowsC % numberOfBucketsC > 0 :
            inBucketC += 1
        
        def calculateDistribution(occIndex, numberOfBuckets, inBucket, numRows, numInRow, allIndex = False) : 

            occurenceArray = calculateOccurrence(ascii_data_array, occIndex, numberOfBuckets, inBucket, numRows, numInRow, allIndex)
            sumArr = np.sum(occurenceArray)
            distr = np.array([0] * sumArr)
            rIdx = -1
            for idx in range(numberOfBuckets) : 
                val = occurenceArray[idx]
                for i in range(val) :
                    rIdx += 1
                    distr[rIdx] = idx
            return distr

        listOfVPlots = list()
        listOfVPlotIdx = list()
        vplotColorList = list()
        offset = meta.violinOffset
        offestDistance = meta.violinOffsetDistance
        cIdx = 0
        if meta.occurrenceIndex != None :
            for occIndex in meta.occurrenceIndex :
                distr = calculateDistribution(occIndex, numberOfBucketsC, inBucketC, numRowsC, numInRowC)
                if len(distr) > 0 :
                    listOfVPlots.append(distr)
                    listOfVPlotIdx.append(offset)
                    if meta.cMap != None and len(meta.cMap) > cIdx :
                        vplotColorList.append(meta.cMap[cIdx])
                cIdx +=1
                offset = offset + offestDistance
        else :
            distr = calculateDistribution(-1, numberOfBucketsC, inBucketC, numRowsC, numInRowC, allIndex=True)
            if len(distr) > 0 :
                listOfVPlots.append(distr)
                listOfVPlotIdx.append(offset)
                if meta.cMap != None and len(meta.cMap) > 0 :
                    vplotColorList.append(meta.cMap[0])
            offset = offset + offestDistance
                
        vp = ax.violinplot(listOfVPlots, listOfVPlotIdx , widths=1.5, showmeans=True, showmedians=False, showextrema=True)

        cIdx = -1
        for body in vp['bodies']:
            cIdx += 1
            if len(vplotColorList) > cIdx :
                body.set_facecolor(vplotColorList[cIdx])
            body.set_linewidth(0.5)
            body.set_alpha(0.5)
            body.set_edgecolor('black')
            ax.set(xlim=(0, offset), ylim=(0, numberOfBucketsC))
            if len(meta.violinHatch) > 0:
                body.set_hatch(meta.violinHatch)
            
        vp['cmeans'].set_edgecolor('black')
        vp['cmaxes'].set_edgecolor('black')
        vp['cmins'].set_edgecolor('black')
        vp['cbars'].set_edgecolor('black')
        vp['cmeans'].set_linewidth(0.75)
        vp['cmaxes'].set_linewidth(0.75)
        vp['cmins'].set_linewidth(0.75)
        vp['cbars'].set_linewidth(0.75)
        

        if onlyOnce :
            if customLegend :
                # legend
                legend_elements = list()
                for element in customLegend :
                    legend_elements.append( Patch(facecolor=element.color, 
                                                hatch=element.hatch, 
                                                edgecolor='black',
                                                label=element.text))                    
                ax.legend(handles=legend_elements, fontsize=6, loc='upper right')                

            ax.axes.invert_yaxis()
            # do this only once

            if meta.yTicklist :
                ax.set_yticks(meta.yTicklist)
            if meta.xTicklist :
                ax.set_xticks(meta.xTicklist)

            if axtickpad != None :
                ax.yaxis.set_tick_params(which='major', pad=axtickpad)
                ax.xaxis.set_tick_params(which='major', pad=axtickpad)

            applyTickLabelMapping(meta.YaxisMappingFile,
                                meta.YaxisMappingRefColumn, 
                                meta.YaxisMappingTarColumn, 
                                meta.YaxisMappingTarColumnAsF,
                                meta.YaxisMappingFormat, 
                                ax.yaxis)
            applyTickLabelMapping(meta.XaxisMappingFile,
                                meta.XaxisMappingRefColumn, 
                                meta.XaxisMappingTarColumn, 
                                meta.XaxisMappingTarColumnAsF,
                                meta.XaxisMappingFormat, 
                                ax.xaxis)
            if len(meta.yLabel) > 0 :
                ax.set_ylabel(meta.yLabel, labelpad=axlabelpad) 
            if len(meta.xLabel) > 0 :
                ax.set_xlabel(meta.xLabel, labelpad=axlabelpad) 
            if len(meta.title) > 0 :
                ax.set_title(meta.title, y=meta.yTitle, x=meta.xTitle)   
            for item in ([ax.xaxis.label, ax.yaxis.label] +
                            ax.get_xticklabels() + ax.get_yticklabels()):
                item.set_fontsize(fontsize)

    if meta.renderAs == "stackedArea" : 
        if onlyOnce :
            # do this only once
            ax.axes.invert_yaxis()
        ascii_data_array[ascii_data_array == asciiHeader.ascii_nodata] = np.nan

        numInRowC = np.count_nonzero(~np.isnan(ascii_data_array), axis=1)
        numberOfBucketsC = len(numInRowC)
        if meta.densityReduction > 0 :
            numberOfBucketsC = meta.densityReduction        
        numRowsC = len(numInRowC)
        inBucketC = int(numRowsC / numberOfBucketsC)
        if numRowsC % numberOfBucketsC > 0 :
            inBucketC += 1
        
        stackedPlots = list()
        stackedColorList = list()
        cIdx = 0
        if meta.occurrenceIndex != None :
            for occIndex in meta.occurrenceIndex :
                distr = calculateOccurrence(ascii_data_array, occIndex, numberOfBucketsC, inBucketC, numRowsC, numInRowC)
                if len(distr) > 0 :
                    stackedPlots.append(distr)
                    if meta.cMap != None and len(meta.cMap) > cIdx :
                        stackedColorList.append(meta.cMap[cIdx])
                cIdx +=1
        else :
            print("error missing 'occurrenceIndex'")

        x = np.arange(numberOfBucketsC)

        # Basic stacked bar chart.
        yLeft = [0] * numberOfBucketsC
        for idx in range(0, len(meta.occurrenceIndex)) :
            ax.barh(x, stackedPlots[idx], height=1, color=stackedColorList[idx], left=yLeft)
            for bucket in range(len(stackedPlots[idx])) :
                yLeft[bucket] += stackedPlots[idx][bucket]

        if meta.showbars :
            axins = inset_axes(ax,
            width="5%",  # width = 5% of parent_bbox width
            height="89%",  # height : 50%
            loc='lower left',
            bbox_to_anchor=(1.05, 0., 1, 1),
            bbox_transform=ax.transAxes,
            borderpad=0,
            )

            norm = matplotlib.colors.Normalize(vmin=0, vmax=len(meta.occurrenceIndex))
            if meta.ticklist :
                # Place a colorbar next to the map
                cbar = fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap=colorM),
                        orientation='vertical', 
                        ticks=meta.ticklist,
                        shrink=0.5, aspect=14, cax=axins)
            else :
                # Place a colorbar next to the map
                cbar = fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap=colorM),
                        orientation='vertical', 
                        shrink=0.5, aspect=14, cax=axins)
            if len(meta.label) > 0 :
                #cbar.ax.set_label(meta.label)
                cbar.ax.set_title(meta.label, loc='left', fontsize=fontsize) 
            if meta.cbarLabel :
                cbar.ax.set_yticklabels(meta.cbarLabel) 

        ax.axes.xaxis.set_visible(True)
        if idxCol != 1 :
            ax.axes.yaxis.set_visible(False)

        if onlyOnce :
            # do this only once
            def update_ticks(val, pos):
                val *= (1/meta.densityFactor)
                val *= meta.factor
                return '{:,g}'.format(val)
            ax.xaxis.set_major_formatter(mticker.FuncFormatter(update_ticks))

            if meta.yTicklist :
                ax.set_yticks(meta.yTicklist)
            if meta.xTicklist :
                ax.set_xticks(meta.xTicklist)

            if axtickpad != None :
                ax.yaxis.set_tick_params(which='major', pad=axtickpad)
                ax.xaxis.set_tick_params(which='major', pad=axtickpad)

            applyTickLabelMapping(meta.YaxisMappingFile,
                                meta.YaxisMappingRefColumn, 
                                meta.YaxisMappingTarColumn, 
                                meta.YaxisMappingTarColumnAsF,
                                meta.YaxisMappingFormat, 
                                ax.yaxis)
            applyTickLabelMapping(meta.XaxisMappingFile,
                                meta.XaxisMappingRefColumn, 
                                meta.XaxisMappingTarColumn, 
                                meta.XaxisMappingTarColumnAsF,
                                meta.XaxisMappingFormat, 
                                ax.xaxis)
            if len(meta.yLabel) > 0 :
                ax.set_ylabel(meta.yLabel, labelpad=axlabelpad) 
            if len(meta.xLabel) > 0 :
                ax.set_xlabel(meta.xLabel, labelpad=axlabelpad) 
            if len(meta.title) > 0 :
                ax.set_title(meta.title, y=meta.yTitle, x=meta.xTitle)   
            for item in ([ax.xaxis.label, ax.yaxis.label] +
                            ax.get_xticklabels() + ax.get_yticklabels()):
                item.set_fontsize(fontsize)

    if meta.renderAs == "avgBarPlot" : 
        if onlyOnce :
            # do this only once
            ax.axes.invert_yaxis()
        ascii_data_array[ascii_data_array == asciiHeader.ascii_nodata] = np.nan
        ascii_data_array[ascii_data_array == 0] = np.nan
        numInRowC = np.count_nonzero(~np.isnan(ascii_data_array), axis=1)
        numberOfBucketsC = len(numInRowC)
        if meta.densityReduction > 0 :
            numberOfBucketsC = meta.densityReduction        
        numRowsC = len(numInRowC)
        inBucketC = int(numRowsC / numberOfBucketsC)
        if numRowsC % numberOfBucketsC > 0 :
            inBucketC += 1
        
        def calculateAvg(ascii_data_array, numberOfBuckets, inBucket, numRows, numInRow) : 
            numRows = len(numInRow)
            sumInArray = np.nansum(ascii_data_array, axis=1)
            avgArray = np.array([0] * numberOfBuckets)
            currBucketIdx = 0
            numAllInBucket = 0
            sumOfBucket = 0
            for idx in range(numRows) : 
                if numInRow[idx] > 0 :
                    numAllInBucket += numInRow[idx]
                    sumOfBucket += sumInArray[idx]
                if (((idx + 1) % inBucket) == 0) or ((idx + 1) == numRows) : 
                    if numAllInBucket > 0 :
                        avgArray[currBucketIdx] = int(sumOfBucket / numAllInBucket)
                    currBucketIdx += 1
                    numAllInBucket = 0
                    sumOfBucket = 0
            return avgArray
        avgArr = calculateAvg(ascii_data_array, numberOfBucketsC, inBucketC, numRowsC, numInRowC)

        x = np.arange(np.max(numberOfBucketsC))

        # Basic bar chart.
        if meta.cMap :
            meta.cMap[0]
            ax.barh(x, avgArr, height=1, color=meta.cMap[0])
        else :
            ax.barh(x, avgArr, height=1)

        ax.axes.xaxis.set_visible(True)
        if idxCol != 1 :
            ax.axes.yaxis.set_visible(False)
        
        if onlyOnce :
            # do this only once
            def update_ticks(val, pos):
                val *= (1/meta.densityFactor)
                val *= meta.factor
                return str(int(val))
            ax.xaxis.set_major_formatter(mticker.FuncFormatter(update_ticks))

            if meta.yTicklist :
                ax.set_yticks(meta.yTicklist)
            if meta.xTicklist :
                ax.set_xticks(meta.xTicklist)

            if axtickpad != None :
                ax.yaxis.set_tick_params(which='major', pad=axtickpad)
                ax.xaxis.set_tick_params(which='major', pad=axtickpad)

            applyTickLabelMapping(meta.YaxisMappingFile,
                                meta.YaxisMappingRefColumn, 
                                meta.YaxisMappingTarColumn, 
                                meta.YaxisMappingTarColumnAsF,
                                meta.YaxisMappingFormat, 
                                ax.yaxis)
            applyTickLabelMapping(meta.XaxisMappingFile,
                                meta.XaxisMappingRefColumn, 
                                meta.XaxisMappingTarColumn, 
                                meta.XaxisMappingTarColumnAsF,
                                meta.XaxisMappingFormat, 
                                ax.xaxis)
            if len(meta.yLabel) > 0 :
                ax.set_ylabel(meta.yLabel, labelpad=axlabelpad) 
            if len(meta.xLabel) > 0 :
                if idxCol == numCols :
                    ax.set_xlabel(meta.xLabel, labelpad=axlabelpad) 
            if len(meta.title) > 0 :
                ax.set_title(meta.title, y=meta.yTitle, x=meta.xTitle)   
            for item in ([ax.xaxis.label, ax.yaxis.label] +
                            ax.get_xticklabels() + ax.get_yticklabels()):
                item.set_fontsize(fontsize)

    if meta.renderAs == "avgCurvePlot" : 
        if onlyOnce :
            # do this only once
            ax.axes.invert_yaxis()
        ascii_data_array[ascii_data_array == asciiHeader.ascii_nodata] = np.nan
        ascii_data_array[ascii_data_array == 0] = np.nan
        numInRowC = np.count_nonzero(~np.isnan(ascii_data_array), axis=1)
        numberOfBucketsC = len(numInRowC)
        if meta.densityReduction > 0 :
            numberOfBucketsC = meta.densityReduction        
        numRowsC = len(numInRowC)
        inBucketC = int(numRowsC / numberOfBucketsC)
        if numRowsC % numberOfBucketsC > 0 :
            inBucketC += 1
        
        def calculateAvg(ascii_data_array, numberOfBuckets, inBucket, numRows, numInRow) : 
            numRows = len(numInRow)
            sumInArray = np.nansum(ascii_data_array, axis=1)
            avgArray = np.array([0] * numberOfBuckets)
            currBucketIdx = 0
            numAllInBucket = 0
            sumOfBucket = 0
            for idx in range(numRows) : 
                if numInRow[idx] > 0 :
                    numAllInBucket += numInRow[idx]
                    sumOfBucket += sumInArray[idx]
                if (((idx + 1) % inBucket) == 0) or ((idx + 1) == numRows) : 
                    if numAllInBucket > 0 :
                        avgArray[currBucketIdx] = int(sumOfBucket / numAllInBucket)
                    currBucketIdx += 1
                    numAllInBucket = 0
                    sumOfBucket = 0
            return avgArray
        avgArr = calculateAvg(ascii_data_array, numberOfBucketsC, inBucketC, numRowsC, numInRowC)

        #y = np.linspace(0, len(arithemticMean)-1, len(arithemticMean))
        y = np.arange(np.max(numberOfBucketsC))
        lines = ax.plot(avgArr, y, label=meta.lineLabel)
        if len(meta.lineColor) > 0 :
            for line in lines : 
                line.set_color(meta.lineColor)
            #  = ax.plot(avgArr, y, label=meta.lineLabel, color=meta.lineColor, hatch=meta.lineHatch)
        if len(meta.lineHatch) > 0 :
            for line in lines : 
                line.set_linestyle(meta.lineHatch)


        ax.axes.xaxis.set_visible(True)
        if idxCol != 1 :
            ax.axes.yaxis.set_visible(False)

        if len(meta.lineLabel) > 0 :
            ax.legend(fontsize=6, handlelength=3.5)
            
        if onlyOnce :
            # do this only once
            def update_ticks(val, pos):
                val *= (1/meta.densityFactor)
                val *= meta.factor
                return str(int(val))
            ax.xaxis.set_major_formatter(mticker.FuncFormatter(update_ticks))

            if meta.yTicklist :
                ax.set_yticks(meta.yTicklist)
            if meta.xTicklist :
                ax.set_xticks(meta.xTicklist)

            if axtickpad != None :
                ax.yaxis.set_tick_params(which='major', pad=axtickpad)
                ax.xaxis.set_tick_params(which='major', pad=axtickpad)

            applyTickLabelMapping(meta.YaxisMappingFile,
                                meta.YaxisMappingRefColumn, 
                                meta.YaxisMappingTarColumn, 
                                meta.YaxisMappingTarColumnAsF,
                                meta.YaxisMappingFormat, 
                                ax.yaxis)
            applyTickLabelMapping(meta.XaxisMappingFile,
                                meta.XaxisMappingRefColumn, 
                                meta.XaxisMappingTarColumn, 
                                meta.XaxisMappingTarColumnAsF,
                                meta.XaxisMappingFormat, 
                                ax.xaxis)
            if len(meta.yLabel) > 0 :
                ax.set_ylabel(meta.yLabel, labelpad=axlabelpad) 
            if len(meta.xLabel) > 0 :
                if idxCol == numCols :
                    ax.set_xlabel(meta.xLabel, labelpad=axlabelpad) 
            if len(meta.title) > 0 :
                ax.set_title(meta.title, y=meta.yTitle, x=meta.xTitle)   
            for item in ([ax.xaxis.label, ax.yaxis.label] +
                            ax.get_xticklabels() + ax.get_yticklabels()):
                item.set_fontsize(fontsize)

    if meta.renderAs == "densityCurvePlot" : 
        if onlyOnce :
            if idxCol == 1 :  
                # do this only once
                ax.axes.invert_yaxis()

        ascii_data_array[ascii_data_array == asciiHeader.ascii_nodata] = np.nan
        
        numInRowC = np.count_nonzero(~np.isnan(ascii_data_array), axis=1)
        numberOfBucketsC = len(numInRowC)
        if meta.densityReduction > 0 :
            numberOfBucketsC = meta.densityReduction        
        numRowsC = len(numInRowC)
        inBucketC = int(numRowsC / numberOfBucketsC)
        if numRowsC % numberOfBucketsC > 0 :
            inBucketC += 1
        
        occurenceArray = calculateOccurrence(ascii_data_array, -1, numberOfBucketsC, inBucketC, numRowsC, numInRowC, allIndex=True)

        y = np.arange(np.max(numberOfBucketsC))
        lines = ax.plot(occurenceArray, y, label=meta.lineLabel)
        if len(meta.lineColor) > 0 :
            for line in lines : 
                line.set_color(meta.lineColor)
        if len(meta.lineHatch) > 0 :
            for line in lines : 
                line.set_linestyle(meta.lineHatch)

        ax.axes.xaxis.set_visible(True)
        if idxCol != 1 :
            ax.axes.yaxis.set_visible(False)

        # if len(meta.lineLabel) > 0 :
        #     ax.legend(fontsize=6, handlelength=2.5)
            
        if onlyOnce :
            if customLegend :
                # legend
                custom_lines = list()
                custom_label = list()
                for element in customLegend :
                    custom_lines.append(Line2D([0], [0], color=element.color, ls=element.hatch, lw=1.3))
                    custom_label.append(element.text)                    
                ax.legend(custom_lines, custom_label, fontsize=6, handlelength=3, loc='lower right')    

            # do this only once
            def update_ticks(val, pos):
                val *= (1/meta.densityFactor)
                val *= meta.factor
                return str(int(val))
            ax.xaxis.set_major_formatter(mticker.FuncFormatter(update_ticks))

            if meta.yTicklist :
                ax.set_yticks(meta.yTicklist)
            if meta.xTicklist :
                ax.set_xticks(meta.xTicklist)

            if axtickpad != None :
                ax.yaxis.set_tick_params(which='major', pad=axtickpad)
                ax.xaxis.set_tick_params(which='major', pad=axtickpad)

            applyTickLabelMapping(meta.YaxisMappingFile,
                                meta.YaxisMappingRefColumn, 
                                meta.YaxisMappingTarColumn, 
                                meta.YaxisMappingTarColumnAsF,
                                meta.YaxisMappingFormat, 
                                ax.yaxis)
            applyTickLabelMapping(meta.XaxisMappingFile,
                                meta.XaxisMappingRefColumn, 
                                meta.XaxisMappingTarColumn, 
                                meta.XaxisMappingTarColumnAsF,
                                meta.XaxisMappingFormat, 
                                ax.xaxis)
            if len(meta.yLabel) > 0 :
                ax.set_ylabel(meta.yLabel, labelpad=axlabelpad) 
            if len(meta.xLabel) > 0 :
                if idxCol == numCols :
                    ax.set_xlabel(meta.xLabel, labelpad=axlabelpad) 
            if len(meta.title) > 0 :
                ax.set_title(meta.title, y=meta.yTitle, x=meta.xTitle)   
            for item in ([ax.xaxis.label, ax.yaxis.label] +
                            ax.get_xticklabels() + ax.get_yticklabels()):
                item.set_fontsize(fontsize)

def calculateOccurrence(ascii_data_array, occIndex, numberOfBuckets, inBucket, numRows, numInRow, allIndex = False) : 
    numRows = len(numInRow)
    if allIndex :
        numXInArray = np.count_nonzero((ascii_data_array > 0), axis=1)
    else :
        numXInArray = np.count_nonzero((ascii_data_array == occIndex), axis=1)
    occurenceArray = np.array([0] * numberOfBuckets)
    currBucketIdx = 0
    numAllInBucket = 0
    numOfType = 0
    for idx in range(numRows) : 
        if numInRow[idx] > 0 :
            numAllInBucket += numInRow[idx]
            numOfType += numXInArray[idx]
        if (((idx + 1) % inBucket) == 0) or ((idx + 1) == numRows) : 
            if numAllInBucket > 0 :
                occurenceArray[currBucketIdx] = round(float(numOfType) * 100.0 / float(numAllInBucket))
            currBucketIdx += 1
            numAllInBucket = 0
            numOfType = 0
    return occurenceArray

def applyTickLabelMapping(file, ref, tar, tarAsFloat, textformat, axis):
    if len(file) > 0 and len(ref) > 0 and len(tar) > 0 :
        lookup = readAxisLookup(file, ref, tar, tarAsFloat)
        def update_ticks_fromLookup(val, pos):
            if val in lookup :
                if len(textformat) > 0 :
                    newVal = lookup[val]
                    return textformat.format(newVal)
                return str(lookup[val])
            return ''
        axis.set_major_formatter(mticker.FuncFormatter(update_ticks_fromLookup))

def readAxisLookup(filename, refCol, tarCol, asFloat) :
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
            if asFloat :
                lookup[float(out[0])] = float(out[1])
            else :
                lookup[float(out[0])] = out[1]
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
    prepareColor()
    build()