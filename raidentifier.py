#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 15:36:55 2019

@author: robertmckenzie

This script contains code needed to compare image statistics, as well as
search through database files to identify images.
"""

import raidatabaseloader as rdl
import imagestatsengine as ise

from PIL import Image

import sys
import random
import time

import multiprocessing as mp

"""
Fully compares two images by measuring ALL of their reference points against
each other. Very expensive en masse. try to use as little as possible.
"""
def compare_stats(img1, img2):
    #this removes metadata potentially contained in the first element.
    if isinstance(img1[0], str):
        img1 = img1[1:]
    if isinstance(img2[0], str):
        img2 = img2[1:]
        
    """
    Very unlikely unless you're using databases generated with different
    specificity values. Don't do that.
    """
    if not (len(img1) == len(img2)):
        print("incompatible images: " + str(len(img1)) + ", " + str(len(img2)))
        return
    
    diff = 0
    for i in range(len(img1)):
        diff += abs(img1[i][0] - img2[i][0])
        diff += abs(img1[i][1] - img2[i][1])
        diff += abs(img1[i][2] - img2[i][2])
        
    return diff

"""
Partially compares two images to produce an estimate of their difference.

points: array of indices to use.
"""
def compare_stats_shallow(img1, img2, points):
    if isinstance(img1[0], str):
        img1 = img1[1:]
    if isinstance(img2[0], str):
        img2 = img2[1:]
        
    #See lines 27-30
    if not (len(img1) == len(img2)):
        print("incompatible images: " + str(len(img1)) + ", " + str(len(img2)))
        return
    
    diff = 0
    for i in range(len(points)):
        diff += abs(img1[points[i]][0] - img2[points[i]][0])
        diff += abs(img1[points[i]][1] - img2[points[i]][1])
        diff += abs(img1[points[i]][2] - img2[points[i]][2])
        
    return diff

"""
Randomly generates a sample of points to use for shallow comparison.

depth: Number of points to generate.
size: number of reference points in the images. Just pass len(im_stat)
to this and it'll handle the rest.
"""
def generate_comparison_points(depth, size):
    points = []
    for i in range(depth):
        points.append(random.randint(2, size - 2))
    return points

def search_data_region(database, im_stat, depth, region_start, region_end, outpipe):
    cur_closest = 0
    cur_second = -1
    min_diff = 2000000000
    search_points = generate_comparison_points(depth, len(im_stat))
    
    for i in range(region_start, region_end):
        diff = compare_stats_shallow(im_stat, database[i], search_points)
        if diff < min_diff:
            cur_second = cur_closest
            cur_closest = i
            min_diff = diff
    outpipe[0].send((cur_closest, cur_second))
    
"""
Uses an optimized combination of deep and shallow comparisons to find the
closest match for an image in the database provided.

database: database of statistics, probably loaded by the raidatabaseloader.
im_stat: image statistics for the image to be searched.
depth: depth of the shallow comparison. 15 is a good number.
multiprocess: Allow use of multiple processing cores. True by default.
"""
def find_closest_match(database, im_stat, depth, multiprocess = True, keep_time = False):
    outpipe = mp.Pipe()
    n_processes = 1
    if multiprocess:
        n_processes = mp.cpu_count()
    cpu_alloc_size = int(len(database) / n_processes)
    cpu_indices = []
    for x in range(n_processes):
        cpu_indices.append([x * cpu_alloc_size, (x + 1) * cpu_alloc_size])
    cpu_indices[n_processes - 1][1] = len(database)
    
    processes = []
    for i in range(n_processes):
        processes.append(mp.Process(target = search_data_region, args = (
                database, im_stat, depth, cpu_indices[i][0], cpu_indices[i][1],
                outpipe)))
    
    start_time = time.time()
    
    for p in processes:
        p.start()
    for p in processes:
        p.join()
        
    cur_closest = -1
    cur_second = -1
    min_diff = 2000000000
    
    while outpipe[1].poll():
        query = outpipe[1].recv()
        for res in query:
            diff = compare_stats(database[res], im_stat)
            if diff < min_diff:
                cur_second = cur_closest
                cur_closest = res
                min_diff = diff
    
    elapsed_time = time.time() - start_time
    if keep_time:
        print("Done in " + str(elapsed_time) + " seconds.")
        
    return (database[cur_closest][0], database[cur_second][0])

"""
Code to be exectuted if this script is run as the main.
"""
if __name__ == "__main__":
    args = sys.argv
    multiprocess = True
    keep_time = False
    
    try:
        print("Loading image...")
        img = Image.open(args[2])
        im_stat = ise.get_image_stats(img)
    except:
        print("Error loading image. Exiting.")
        sys.exit()
    
    try:
        print("Loading database...")
        dbfile = open(args[1], "r")
        db = rdl.load_data_file(dbfile)
        print("Loaded.")
    except:
        print("Error loading database. Exiting.")
        sys.exit()
    
    if len(args) > 3:
        for i in range(3, len(args)):
            if args[i] == "keeptime":
                keep_time = True
            elif args[i] == "nomulti":
                multiprocess = False
    
    match = find_closest_match(db, im_stat, 15, multiprocess, keep_time)
    print("Closest: " + match[0])
    print("Second:  " + match[1])