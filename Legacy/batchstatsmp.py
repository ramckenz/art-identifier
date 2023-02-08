#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 08 13:27:00 2019

@author: robertmckenzie
"""

import raistatsengine as ris
from PIL import Image
#import statistics
import os
import sys
import time

import multiprocessing as mp

def processListRegion(directory, dirlist, outPipe, startIndex, endIndex):
    for i in range(startIndex,endIndex):
        filename = os.fsdecode(dirlist[i])
        if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
            im = Image.open(os.fsdecode(directory) + "/" + filename)
            try:
                outPipe[0].send(filename + " " + ris.statsToString(ris.getImageStatistics(im)) + "\n\n")
            except TypeError:
                print("Type Error on " + filename)
                
def writefrompipe(outpipe, datafile, dirsize = None):
    count = 0
    percent = 0
    fivepercent = int(dirsize / 20)
    if not dirsize == None:
        print("Progress:\n0%")
    while outpipe[1].poll(10):
        try:
            datafile.write(outpipe[1].recv())
            count += 1
            if count == fivepercent:
                percent += 5
                count = 0
                print(str(percent) + "%")
        except EOFError:
            return
    print("Polling timeout!")
    return

if __name__ == "__main__":
    args = sys.argv
    
    if len(args) == 1:
        print("Not enough arguments. Directory needed!")
        sys.exit()
        
    if not os.path.isdir(args[1]):
        print("Invalid directory. Exiting")
        sys.exit()
    
    datafile = open("imageStatsmp.txt", "w+")
    
    directory = os.fsencode(args[1])
    size = len(os.listdir(directory))
    
    #multiprocessing code:
    outPipe = mp.Pipe()
    n_procs = mp.cpu_count() - 1
    cpuallocsize = int(size / n_procs)
    cpuindices = []
    for x in range(n_procs):
        cpuindices.append([x * cpuallocsize, (x + 1) * cpuallocsize])
    cpuindices[n_procs - 1][1] = size
    
    procs = []
    for i in range(n_procs):
        procs.append(mp.Process(target = processListRegion, args = 
                                (directory, os.listdir(directory),outPipe,
                                 cpuindices[i][0],cpuindices[i][1])))
    
    pipeProc = mp.Process(target = writefrompipe, args = (outPipe, datafile, size))
    pipeProc.start()
    
    startTime = time.time()
    
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    outPipe[1].close()
    pipeProc.join()
    elapsedTime = time.time() - startTime
        
    #print(outQueue)
    
    print("Done in " + str(elapsedTime) + " seconds.")
    