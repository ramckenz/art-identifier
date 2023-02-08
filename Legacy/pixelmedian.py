#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 27 14:24:58 2019

@author: robertmckenzie
"""

from PIL import Image
import os
import statistics

def medianAtPixel(pxmap, x, y, xlen, ylen, strength):
    lowestX = int(x - strength / 2)
    highestX = int(x + strength / 2)
    lowestY = int(y - strength / 2)
    highestY = int(y + strength / 2)
    
    if lowestX < 0:
        lowestX = 0
    if highestX > xlen:
        highestX = xlen
    if lowestY < 0:
        lowestY = 0
    if highestY > ylen:
        highestY = ylen
    
    rVals = []
    gVals = []
    bVals = []
    
    for cx in range(lowestX, highestX):
        for cy in range(lowestY, highestY):
            rVals.append(pxmap[cx,cy][0])
            gVals.append(pxmap[cx,cy][1])
            bVals.append(pxmap[cx,cy][2])
    
    resR = int(statistics.median(rVals))
    resG = int(statistics.median(gVals))
    resB = int(statistics.median(bVals))
    
    return(resR, resG, resB)
    
def meanAtPixel(pxmap, x, y, xlen, ylen, strength):
    lowestX = int(x - strength / 2)
    highestX = int(x + strength / 2)
    lowestY = int(y - strength / 2)
    highestY = int(y + strength / 2)
    
    if lowestX < 0:
        lowestX = 0
    if highestX > xlen:
        highestX = xlen
    if lowestY < 0:
        lowestY = 0
    if highestY > ylen:
        highestY = ylen
    
    rVals = []
    gVals = []
    bVals = []
    
    for cx in range(lowestX, highestX):
        for cy in range(lowestY, highestY):
            rVals.append(pxmap[cx,cy][0])
            gVals.append(pxmap[cx,cy][1])
            bVals.append(pxmap[cx,cy][2])
    
    resR = int(statistics.mean(rVals))
    resG = int(statistics.mean(gVals))
    resB = int(statistics.mean(bVals))
    
    return(resR, resG, resB)