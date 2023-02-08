#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 15:39:18 2019

@author: robertmckenzie

This script loads a previously written RAI database file into Python list
format.
"""

def load_data_file(file):
    contents = file.read()
    entries = contents.split("\n\n")
    
    result = []
    
    for entry in entries:
        if len(entry) > 1:
            entryArr = entry.split("!")
            entry_metadata = entryArr[0]
            entry = entryArr[1]
            
            entryRes = [entry_metadata]
            for point in entry.split("%"):
                if len(point) > 1:
                    vals = point.split(",")
                    entryRes.append((int(vals[0]),int(vals[1]),int(vals[2])))
            result.append(entryRes)
            
    return result