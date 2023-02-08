#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul  7 14:50:41 2019

@author: robertmckenzie
"""

import os
import sys
import random
from PIL import Image

import statloader
import raidentifymp
import raistatsengine as ris

imgdir = os.fsencode("./Images")
compdir = os.fsencode("./cnr")

def getImageSample(directory, percentage):
    for imgfile in os.listdir(imgdir):
        if random.random() < (float(percentage) / 100.0):
            imgname = os.fsdecode(imgfile)
            img = Image.open("./Images/" + imgname)
            imgres = img.size
            newWidth = int(imgres[0] * (random.random() + 0.35))
            newHeight = int(imgres[1] * (random.random() + 0.35))
            newQual = random.randint(50, 100)
            img = img.resize((newWidth, newHeight))
            img.save(("./cnr/" + imgname),quality = newQual)
            
def testSample():
    targetNum = 0
    correctHits = 0
    print("Loading database...")
    datafile = open("imageStatsmp.txt","r")
    stats = statloader.loadDataFile(datafile)
    print("Loaded. Testing")
    for compImg in os.listdir(compdir):
        imname = os.fsdecode(compImg)
        if imname.endswith(".jpg"):
            img = Image.open("./Images/" + imname)
            try:
                stat = ris.getImageStatistics(img)
                res = raidentifymp.findClosestMatchOptimized(stats, stat, 10)
                targetNum += 1
                if res[0] == imname:
                    correctHits += 1
                else:
                    print("Miss: identified " + imname + " as " + res[0])
            except TypeError:
                print("Type Error on " + imname)
    print("Done.")
    print(str(correctHits) + "/" + str(targetNum) + " images correctly identified.")


if __name__ == "__main__":
    args = sys.argv
    if args[1] == "sample":
        getImageSample(imgdir, 10)
    elif args[1] == "test":
        testSample()
    