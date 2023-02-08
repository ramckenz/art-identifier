#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 10:44:19 2019

@author: robertmckenzie
"""

from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup as bs

def simple_get(url):
    """
    makes an HTTP GET request
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None
    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None
    
def is_good_response(resp):
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)
    
def log_error(e):
    print(e)

def get_names():
    url = 'http://www.fabpedigree.com/james/mathmen.htm'
    response = simple_get(url)
    
    if response is not None:
        html = bs(response, 'html.parser')
        names = set() #sets ensure you don't have duplicates
        for li in html.select('li'):
            for name in li.text.split('\n'):
                if len(name) > 0:
                    names.add(name.strip())
        return list(names)
    
    raise Exception('Error retrieving contents at {}'.format(url))
    
def get_hits_on_name(name):
    