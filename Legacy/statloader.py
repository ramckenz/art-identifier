#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  1 13:30:16 2019

@author: robertmckenzie
"""

#import batchstats
#import robsimagestatistics as ris
import pixelmedian
#import os
import sys
from PIL import Image

    
def loadDataFile(file):
    contents = file.read()
    entries = contents.split("\n\n")
    
    result = []
    
    for entry in entries:
        if len(entry) > 1:
            entryArr = entry.split(" ")
            entryFile = entryArr[0]
            entry = entryArr[1]
            
            entryRes = [entryFile]
            for point in entry.split("%"):
                if len(point) > 1:
                    vals = point.split(",")
                    #print(vals)
                    entryRes.append((int(vals[0]),int(vals[1]),int(vals[2])))
            result.append(entryRes)
            
    #print(result)
    return result

if __name__ == "__main__":
    try:
        datafile = open("imageStats.txt", "r")
    except:
        print("Error: bad or no data file. Exiting")
        sys.exit()
    
    loadDataFile(datafile)