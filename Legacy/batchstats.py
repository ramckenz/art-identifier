#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 11:43:00 2019

@author: robertmckenzie
"""

import raistatsengine as ris
from PIL import Image
#import statistics
import os
import sys
import time

def main():
    
    args = sys.argv
    
    if len(args) == 1:
        print("Not enough arguments. Directory needed!")
        sys.exit()
        
    if not os.path.isdir(args[1]):
        print("Invalid directory. Exiting")
        sys.exit()
    
    datafile = open("imageStats3.txt", "w+")
    
    directory = os.fsencode(args[1])
    size = len(os.listdir(directory))
    fivepercent = int(size / 20)
    
    count = 1
    percent = 0
    
    startTime = time.time()
    
    print("Progress:")
    print("0%")
    for file in os.listdir(directory):
        if count == fivepercent:
            count = 0
            percent += 5
            print(str(percent) + "%")
        count += 1
        filename = os.fsdecode(file)
        if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
            im = Image.open(args[1] + "/" + filename)
            #print(filename, ris.statsToString(ris.getImageStatistics(im)),"\n")
            try:
                datafile.write(filename + " " + ris.statsToString(ris.getImageStatistics(im)) + "\n\n")
            except TypeError:
                print("Type Error on " + filename)
    
    elapsedTime = time.time() - startTime
    print("Done in " + str(elapsedTime) + " seconds")
    
if __name__ == "__main__":
    main()