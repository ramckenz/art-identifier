#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  1 14:09:12 2019

@author: robertmckenzie
"""

import statloader
import raistatsengine
from PIL import Image
import sys
import random
import time

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

def findClosestMatchOptimized(stats, imstat, depth):
    points = []
    potentialMatches = []
    lowDiff = 2000000000
    
    starttime = time.time()
    
    for i in range(depth):
        points.append(random.randint(1,len(imstat) - 1))
        
    for stat in stats:
        diff = shallowCompare(stat, imstat, points)
        if diff < lowDiff:
            potentialMatches.append(stat)
            lowDiff = diff
            
    closest = ""
    second = ""
    lowDiff = 2000000000
    for stat in potentialMatches:
        diff = compareStats(imstat, stat)
        if diff < lowDiff:
            lowDiff = diff
            second = closest
            closest = stat[0]
            
    elapsed = time.time() - starttime
    print("Done in " + str(elapsed) + " seconds.")
            
    return(closest,second)
    

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
        match = findClosestMatchOptimized(stats, imstat, 10)
        print("Closest: " + match[0])
        print("Second closest: " + match[1])
    else:
        match = findClosestMatch(stats, imstat)
        print("Closest: " + match[0])
        print("Second closest: " + match[1])
    
            
    