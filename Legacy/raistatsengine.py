#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 27 14:39:26 2019

@author: robertmckenzie
"""

import pixelmedian
from PIL import Image

standardHeight = 1000
standardWidth = 1000

specificity = 20
"""
approximately this number squared "reference points" will be created on the image.
Higher specificity means higher accuracy, but also higher performance and storage
costs.
"""

def standardizeImage(img):
    res = img.resize((standardWidth, standardHeight),Image.BICUBIC)
    if len(res.getbands()) == 1:
        newIm = Image.new("RGB",(standardWidth, standardHeight))
        for cx in range(standardWidth):
            for cy in range(standardHeight):
                val = res.getpixel((cx,cy))
                newIm.putpixel((cx, cy), (val, val, val))
        res = newIm
    return res

def getImageStatistics(img):
    img = standardizeImage(img)
    pixelMap = img.load()
    sizeX = img.size[0]
    sizeY = img.size[1]
    
    sampleMarginX = int(sizeX / specificity)
    sampleMarginY = int(sizeY / specificity)
    
    sampleSpacingX = int((sizeX - (2 * sampleMarginX)) / specificity)
    sampleSpacingY = int((sizeY - (2 * sampleMarginY)) / specificity)
    
    imgStats = []
    
    for cx in range(specificity):
        for cy in range(specificity):
            mean = pixelmedian.meanAtPixel(pixelMap,
                                            sampleMarginX + cx * sampleSpacingX, 
                                            sampleMarginY + cy * sampleSpacingY,
                                            sizeX, sizeY, sampleSpacingX)
            """
            #Legacy: this method didn't work well. Delete later
            app = [False, False, False] #(red > blue, blue > green, green > red)
            if med[0] > med[1]:
                app[0] = True
            if med[1] > med[2]:
                app[1] = True
            if med[2] > med[0]:
                app[2] = True
            """
                
            imgStats.append(mean)
            
    return imgStats

"""
def bts(b):
    if b == True:
        return 't'
    else:
        return 'f'
    
def boolsToCode(b1, b2, b3):
    res = 0
    if b3:
        res += 1
    if b2:
        res += 2
    if b1:
        res += 4
    return str(res)
"""

def statsToString(stats):
    res = ""
    for stat in stats:
        res = res + str(stat[0]) + "," + str(stat[1]) + "," + str(stat[2]) + "%"
    return res
