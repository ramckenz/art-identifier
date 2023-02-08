#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 16:01:00 2019

@author: robertmckenzie
"""

from PIL import Image
import os
import statistics

def lineMedianEffect(img, strength):
    pixelMap = img.load()
    res = Image.new(img.mode, img.size)
    xlen = img.size[0]
    ylen = img.size[1]
    for x in range(xlen):
        for y in range(ylen):
            res.putpixel((x,y),lineMedian(pixelMap, strength, x, y, xlen, ylen))
            
    return res
    
def squareMedianEffect(img, strength):
    pixelMap = img.load()
    res = Image.new(img.mode, img.size)
    xlen = img.size[0]
    ylen = img.size[1]
    for x in range(xlen):
        for y in range(ylen):
            res.putpixel((x,y),squareMedian(pixelMap, strength, x, y, xlen, ylen))
            
    return res
    
def lineMedian(pxmap, strength, x, y, xlen, ylen):
    lowestX = x - strength
    highestX = x + strength
    lowestY = y - strength
    highestY = y + strength
    
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
        rVals.append(pxmap[cx,y][0])
        gVals.append(pxmap[cx,y][1])
        bVals.append(pxmap[cx,y][2])
        #print(pxmap[cx,y][0])
    for cy in range(lowestY, highestY):
        rVals.append(pxmap[x,cy][0])
        gVals.append(pxmap[x,cy][1])
        bVals.append(pxmap[x,cy][2])
    
    newR = int(statistics.median(rVals))
    newG = int(statistics.median(gVals))
    newB = int(statistics.median(bVals))
    
    return(newR, newG, newB)
    
def squareMedian(pxmap, strength, x, y, xlen, ylen):
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
    
    newR = int(statistics.median(rVals))
    newG = int(statistics.median(gVals))
    newB = int(statistics.median(bVals))
    
    return(newR, newG, newB)
    
    
image1 = Image.open('choco.jpeg')
image2 = lineMedianEffect(image1, 15)
image2.show()
image3 = squareMedianEffect(image1, 15)
image3.show()
    
"""
from PIL import Image
im = Image.open('leaf.jpg')
pixelMap = im.load()

img = Image.new( im.mode, im.size)
pixelsNew = img.load()
for i in range(img.size[0]):
    for j in range(img.size[1]):
        if 205 in pixelMap[i,j]:
            pixelMap[i,j] = (0,0,0,255)
        else:
            pixelsNew[i,j] = pixelMap[i,j]
img.show()
"""
    