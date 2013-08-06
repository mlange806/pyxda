#!/usr/bin/env python
# coding=utf-8
##############################################################################
#
# pyxda.srxes       X-ray Data Analysis Library
#                   (c) 2013 National Synchrotron Light Source II,
#                   Brookhaven National Laboratory, Upton, NY.
#                   All rights reserved.
#
# File coded by:    Michael Saltzman
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################

import numpy as np
import scipy as sp
import scipy.sparse as ssp
import fabio
from traits.api import HasTraits
from collections import deque

class Image(object):
    '''Image class
    
    An image object created from a filepath.
    '''

    def __init__(self, n, path):
        '''Contructor for Image Class
        
        Initializes the properties of a newly created image object.
        
        Ags:
            n: the index of the image file.
            path: the path of the image file.
        '''
        
        if path == '':
            self.name = '2D Image'
            self.metadata = {}
            self.n = -1
            self.data = None
            return
        self.name = path.split('/')[-1]
        self.path = path
        self.n = n
        self.data = None
        self.metadata = self._parseMD()
        return

    def _parseMD(self):
        '''Parse Metadata
        
        Looks for files containing the metadata (files ending in .metadata)
        '''
        
        md = {}
        try:
            fp = open(self.path+'.metadata')

            for i, line in enumerate(fp):
                if line[0] == '[' or line[0] == '\r':
                    continue
                words = line.split('=', 1)
                md[words[0]] = str(words[1])

            fp.close()
        except IOError:
            pass
            #print 'No metadata found for %s' % self.path
        return md

    def load(self):
        '''Load image from path
        
        Loads image data from self.path into self.data
        '''
        
        if self.data is None:
            #print 'load data for ' + self.name
            fo = fabio.open(self.path)
            self.data = fo.data
        return

class ImageCache(HasTraits, object):
    '''ImageCache Class
    
    An an image cache of three loaded image files.
    '''
    
    def __init__(self):
        '''Creates a deque of (-1, 0, 1) value.'''
        
        self.cache = deque(maxlen=3)
        for i in range(3):
            self.cache.append(Image(-1, ''))
        return

    def __str__(self):
        '''Slot wrapper'''
        
        temp1 = self.cache.popleft()
        temp2 = self.cache.popleft()
        temp3 = self.cache.popleft()
        s1 = 'Image Cache:\n%d\n%d\n%d' % (temp1.n, temp2.n, temp3.n)
        self.cache.append(temp1)
        self.cache.append(temp2)
        self.cache.append(temp3)
        return s1

    def append(self, image):
        '''Append an image to the right
        
        Removes the left image data and appends image to the right of the cache.
        
        Ags:
            image: image to be loaded and appended to the cache
        '''
        
        temp = self.cache.popleft()
        if temp.n is not -1:
            temp.data = None
        self.cache.append(image)
        image.load()
        return

    def appendleft(self, image):
        '''Append an image to the left
        
        Removes the right image data and appends image to the left of the cache.
        
        Ags:
            image: image to be loaded and appended to the cache
        '''
        
        temp = self.cache.pop()
        if temp.n is not -1:
            temp.data = None
        self.cache.appendleft(image)
        image.load()
        return

    def pop(self):
        '''Removes and return rightmost image data in cache'''
        
        temp = self.cache.pop()
        self.cache.appendleft(Image(-1, ''))
        return temp

    def popleft(self):
        '''Removes and return leftmost image data in cache'''
        
        temp = self.cache.popleft()
        self.cache.append(Image(-1, ''))
        return temp

    def reverse(self):
        '''Reverses the order of the cache'''
        
        self.cache.reverse()
        return

    def clear(self):
        '''Removes all contents of the cache'''
        
        while True:
            try:
                self.cache.pop().data = None
            except IndexError:
                break
        for i in range(3):
            self.cache.append(Image(-1, ''))
        return
