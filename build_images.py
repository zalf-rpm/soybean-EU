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
from ruamel_yaml import YAML


PATHS = {
    "local": {
        "sourcepath" : "./asciigrid/",
        "outputpath" : ".",
        "png-out" : "png/" , # path to png images
        "pdf-out" : "pdf-out/" , # path to pdf package
    },
    "test": {
        "sourcepath" : "./asciigrid2/",
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
CROPNAME = "soybean"
NONEVALUE = -9999

def build() :

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


    for root, dirs, files in os.walk(sourceFolder):
        path = root.split(os.sep)
        scenario = "_".join(dirs)
        pdfpath = os.path.join(pdfFolder, "scenario_{0}.pdf".format(scenario))
        pdf = PdfPages(pdfpath)
        outfolder = os.path.join(pngFolder, scenario)
        makeDir(pdfpath)
        makeDir(outfolder)
        for file in files:
            if not file.endsWith("meta"):
                createImgFromMeta(file, file + ".meta", outfolder, pdf=pdf)
        pdf.close()


def createImgFromMeta(ascii_path, meta_path, out_path, pdf=None) :

    title="" 
    label=""
    colormap = 'viridis'
    cMap = None
    cbarLabel = None
    factor = 0.001
    ticklist = None
    maxValue = None
    minValue = None

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
                maxValue = int(doc)
            elif item == "minValue" :
                minValue = int(doc)
            elif item == "colormap" :
                colormap = doc
            elif item == "colorlist" :
                cMap = ListedColormap(doc)
            elif item == "cbarLabel" :
                cbarLabel = doc
            elif item == "ticklist" :
                ticklist = list()
                for i in doc :
                    ticklist.append(float(i))

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
    
    # Read in the ascii data array
    ascii_data_array = np.loadtxt(ascii_path, dtype=np.float, skiprows=6)
    
    # Set the nodata values to nan
    ascii_data_array[ascii_data_array == ascii_nodata] = np.nan
    
    # data is stored as an integer but scaled by a factor
    ascii_data_array *= factor

    image_extent = [
        ascii_xll, ascii_xll + ascci_cols * ascii_cs,
        ascii_yll, ascii_yll + ascii_rows * ascii_cs]
    
    # Plot data array
    fig, ax = plt.subplots()
    ax.set_title(title)
    
    # Get the img object in order to pass it to the colorbar function
    if cMap :
        img_plot = ax.imshow(ascii_data_array, cmap=cMap, extent=image_extent, vmin=minValue, vmax=maxValue)
    else :
        img_plot = ax.imshow(ascii_data_array, cmap=colormap, extent=image_extent, vmin=minValue, vmax=maxValue)

    if ticklist :
        # tick = 0.5 - len(cbarLabel) / 100 
        # tickslist = [tick] * len(cbarLabel)
        # for i in range(len(cbarLabel)) :
        #     tickslist[i] += i * 2 * tick
        # tickslist = [0] * (len(cbarLabel) * 2)
        # for i in range(len(cbarLabel)) :
        #      tickslist[i] += i 
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
  

def makeDir(out_path) :
    if not os.path.exists(os.path.dirname(out_path)):
        try:
            os.makedirs(os.path.dirname(out_path))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

if __name__ == "__main__":
    build()