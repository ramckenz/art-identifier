#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 12:14:28 2019

@author: robertmckenzie
"""

import os
import shutil

libraryDir = os.fsencode("./library1")
#print(os.listdir(libraryDir))

for folder in os.listdir(libraryDir):
    folderName = os.fsdecode(folder)
    count = 1
    if(os.path.isdir("./library1/" + folderName)):
        filedir = os.fsencode("./library1/" + folderName)
        for file in os.listdir(filedir):
            fileName = os.fsdecode(file)
            newFileName = folderName + str(count)
            shutil.move(("./library1/" + folderName + "/" + fileName),("./trucks/" + newFileName + ".jpg"))
            count = count + 1

