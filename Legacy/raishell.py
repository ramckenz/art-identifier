#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  5 13:39:31 2019

@author: robertmckenzie
"""

import sys
import statloader
import raistatsengine as ris
import raidentifymp
from PIL import Image

import time

args = sys.argv

statfile = ""
loaded = False

try:
    statfile = args[2]
    f = open(statfile,"r")
    print("Loading...")
    stats = statloader.loadDataFile(f)
    loaded = True
except:
    while not loaded:
        try:
            statfile = input("Database invalid or not provided.\nEnter database filename or type exit: ")
            if statfile == "exit":
                sys.exit()
            f = open(statfile, "r")
            print("Loading...")
            stats = statloader.loadDataFile(f)
            loaded = True
        except:
            loaded = False

print("Loading complete.")

while True:
    imgargs = input("Enter image filename and arguments, or type 'exit': ")
    optimize = False
    if imgargs == "exit":
        sys.exit()
    imgargs = imgargs.split(" ")
    if len(imgargs) > 1 and imgargs[1] == "optimized":
        optimize = True
    try:
        print("Analyzing image...")
        img = Image.open(imgargs[0])
        imstat = ris.getImageStatistics(img)
        print("Searching...")
        startTime = time.process_time()
        if optimize:
            res = raidentifymp.findClosestMatchOptimized(stats, imstat, 10)
        else:
            res = raidentifymp.findClosestMatch(stats, imstat)
        elapsed = time.process_time() - startTime
        print("\nClosest match: " + res[0])
        print("Second closest: " + res[1])
        print("Search took " + str(elapsed) + " seconds.")
    except:
        print("Error: couldn't read image file.")
        