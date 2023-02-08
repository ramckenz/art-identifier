#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 10:56:27 2019

@author: robertmckenzie
"""

from ws1 import simple_get

rawHTML = simple_get('https://roobiert.com')
print(len(rawHTML))