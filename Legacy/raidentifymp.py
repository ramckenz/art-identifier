#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 12:10:47 2019

@author: robertmckenzie
"""


import statloader
import raistatsengine
from PIL import Image
import sys
import random
import time

import multiprocessing as mp

if __name__ == "__main__":
    
    args = sys.argv
    
    if len(args) == 1:
        print("Not enough arguments. File needed!")
        sys.exit()
        
    try:
        datafile = open("imageStats.txt", "r")
    except:
        print("Error: bad or no data file. Exiting")
        sys.exit()
        
    try:
        im = Image.open(args[1])
    except:
        print("Image file could not be opened. Exiting")
        sys.exit()
        
    stats = statloader.loadDataFile(datafile) #image database
    imstat = raistatsengine.getImageStatistics(im) #image to compare
    
    print("Loading complete")

def compareStats(img1, img2):
    """
    I should make it so that all image stats have their info as the first element.
    """
    if isinstance(img1[0],str):
        img1 = img1[1:]
    if isinstance(img2[0],str):
        img2 = img2[1:]
        
    if not (len(img1) == len(img2)):
        print("incompatible images: " + str(len(img1)) + ", " + str(len(img2)))
        return
    
    diff = 0
    for i in range(len(img1)):
        diff += abs(img1[i][0] - img2[i][0])
        diff += abs(img1[i][1] - img2[i][1])
        diff += abs(img1[i][2] - img2[i][2])
    
    return diff

def shallowCompare(img1, img2, points):
    if isinstance(img1[0],str):
        img1 = img1[1:]
    if isinstance(img2[0],str):
        img2 = img2[1:]
        
    if not (len(img1) == len(img2)):
        print("incompatible images: " + str(len(img1)) + ", " + str(len(img2)))
        return
    
    diff = 0
    for i in range(len(points)):
        diff += abs(img1[points[i]][0] - img2[points[i]][0])
        diff += abs(img1[points[i]][1] - img2[points[i]][1])
        diff += abs(img1[points[i]][2] - img2[points[i]][2])
        
    return diff
        
def compareAll():    
    for stat in stats:
        print("Comparing " + args[1] + " with " + stat[0])
        print("Diff: ")
        diff = compareStats(imstat, stat)
        print(str(diff) + "\n")
        
def generatecomparisonpoints(depth, size):
    points = []
    for i in range(depth):
        points.append(random.randint(2,size - 1))
    return points
        
def searchdataregion(stats, imstat, depth, regionstart, regionend, outpipe):
    closestInd = 0
    secondInd = -1
    minDiff = 2000000000
    searchpoints = generatecomparisonpoints(depth, len(imstat))
    for i in range(regionstart, regionend):
        diff = shallowCompare(imstat, stats[i], searchpoints)
        if diff < minDiff:
            secondInd = closestInd
            closestInd = i
            minDiff = diff
    outpipe[0].send((closestInd, secondInd))
        

def findClosestMatchOptimized(stats, imstat, depth):
    outpipe = mp.Pipe()
    n_procs = mp.cpu_count()
    cpuallocsize = int(len(stats) / n_procs)
    cpuindices = []
    for x in range(n_procs):
        cpuindices.append([x * cpuallocsize, (x + 1) * cpuallocsize])
    cpuindices[n_procs - 1][1] = len(stats)
    
    procs = []
    for i in range(n_procs):
        procs.append(mp.Process(target=searchdataregion, args=(
                                stats, imstat, depth, cpuindices[i][0],
                                cpuindices[i][1], outpipe)))
    starttime = time.time()
    for p in procs:
        p.start()
    for p in procs:
        p.join()
        
    closest = -1
    second = -1
    lowDiff = 2000000000
    
    while outpipe[1].poll():
        query = outpipe[1].recv()
        for res in query:
            diff = compareStats(stats[res], imstat)
            if diff < lowDiff:
                second = closest
                closest = res
                lowDiff = diff
    
    elapsed = time.time() - starttime
    #print("Done in " + str(elapsed) + " seconds.")
    
    return (stats[closest][0], stats[second][0])
    

def findClosestMatch(stats, imstat):
    closest = ""
    second = ""
    lowDiff = 2000000000
    for stat in stats:
        diff = compareStats(imstat, stat)
        if diff < lowDiff:
            lowDiff = diff
            second = closest
            closest = stat[0]
    return(closest,second)
    
if __name__ == "__main__":
    if len(args) == 3 and args[2] == "all":
        compareAll()
    elif len(args) == 3 and args[2] == "optimized":
        match = findClosestMatchOptimized(stats, imstat,10)
        print("Closest: " + match[0])
        print("Second closest: " + match[1])
    else:
        match = findClosestMatch(stats, imstat)
        print("Closest: " + match[0])
        print("Second closest: " + match[1])
    