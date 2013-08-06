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

from enthought.traits.api import HasTraits, Instance, Event, Int, List, Bool, Str
from chaco.api import Plot
import numpy as np
import Queue
import threading

from display import Display
from imagecontainer import Image, ImageCache
from loadimages import LoadImage

class RawViewer(HasTraits):
    
    def __init__(self, **kwargs):
        """Constructor called when a RawViewer object is initialized
        
        Creates thread and defines thread attributes. Creates a job queue, list
        of image data, and length of list. Establishes trait change attributes
        for pic and datalistlengthadd. 
    	"""
    	
        super(RawViewer, self).__init__()
        
        self.processing_job = threading.Thread(target=self.processJob)
        self.processing_job.daemon = True
        
        self.jobqueue = Queue.Queue()
        self.add_trait('datalist', List())
        self.add_trait('datalistlength', Int(0))
        
        self.on_trait_change(self.plotData, 'pic', dispatch='new')
        self.on_trait_change(self.datalistLengthAdd,'datalistlengthadd', 
                             dispatch='ui')
       
        self.initLoadimage()
        self.initDisplay()
        self.initCMap()
        return
    
    def initLoadimage(self):
        '''Initializes load variables'''
        
        self.cache = ImageCache()
        self.add_trait('pic', Instance(Image, Image(-1, '')))
        self.pic.data = np.zeros((2048, 2048))
        self.add_trait('hasImage', Bool(False))
        return

    def initDisplay(self):
        '''Initializes plots and plot settings'''
        
        self.add_trait('display', Display(self.jobqueue))
        self.add_trait('loadimage', Instance(LoadImage))
        # TODO: Move to Display.
        self.add_trait('imageplot', Instance(Plot, 
                                        self.display.plotImage(self.pic)))
        self.add_trait('plot1d', Instance(Plot,
                                        self.display.plotHistogram(self.pic)))
        self.plot1d.value_axis.title = "1D Cut"
        self.add_trait('histogram', Instance(Plot,
                                        self.display.plotHistogram(self.pic)))
        self.newndx = -1
        return
    
    # TODO: Update
    def initCMap(self):
        '''Initializes rrplots and hascmap'''
        
        self.hascmap = False
        #TODO
        #self.add_trait('rrplot', Instance(Plot, 
        #                        self.display.plotRRMap(None, None)))
        self.rrplots = {}

    ##############################################
    # Tasks  
    ##############################################
    def addNewImage(self, path, **kwargs):
        '''Add new image
        
        Adds new image and create jobs to process new image.
        
        Args:
            path: File path of the image.
        Exceptions:
            TypeError: path is not a valid image path
        '''
        
        #print 'Image Added'
        listn = len(self.datalist)
        self.datalist.append(Image(listn, path))
        self.hasImage = True
        self.jobqueue.put(['datalistlengthadd'])
        return
   
    
    def plotData(self):
        '''Plot current data
        
        Plots the image located from pic.path. Plots an associated histogram
        and 1D Plot.
        '''
        
        print 'Plot Data'
        self.pic.load()
        self.imageplot = self.display.plotImage(self.pic, self.imageplot)
        #TODO
        self.histogram = self.display.plotHistogram(self.pic, self.histogram)
        self.plot1d = self.display.plotHistogram(self.pic, None)
        return

    # TODO
    datalistlengthadd = Event
    def datalistLengthAdd(self):
        '''Add datalistlength by 1
        
        Notice:
            Only use this method to modify the datalistlength
            otherwise there will be some problem of frame range in UI
        '''

        self.datalistlength += 1
        return

    def startLoad(self, dirpath):
        '''Start loading thread
        
        Display is reset if there is already data plotted. A LoadImage object
        is created with access to jobqueue and dirpath. This object starts its
        own thread that adds the first three image paths and then an initialize 
        cache command to the jobqueue. After this, it continues to load the rest
        of the image paths in the folder to the jobqueue.  
        
        Args:
            dirpath: The folder path containing tiff files.
        Exceptions:
            No exceptions are thrown. However, if dirpath contains no tiff files
            or the folder path is nonexistant, the message variable of loadimage
            will change to a string with information why the path is invalid. 
        '''
        
        print 'Load Started'
        if self.hasImage == True:
            self.resetViewer()   
        self.loadimage = LoadImage(self.jobqueue, dirpath) 
        self.loadimage.start()
              
    # TODO: not as important
    def initCache(self):
        '''Initialize the Image Cache
        
        Creates the initial image chache. The first image is loaded and ploted
        to the screen. Then the next two are loaded.
        '''
        
        print 'Init Cache'
        self.pic = self.datalist[0]
        for i in range(2):
            pic = self.datalist[i]
            self.cache.append(pic)
            pic.load()
        return 

    def changeIndex(self, newndx):
        '''Changes the image based on index
        
        The parameter, newndx, is made the new image index, self.newndx, and the
        image of that index is plotted to the screen.
        
        Args:
            newndx: An integer representing the next image index
        '''
        
        print 'Change Index'
        self.newndx = newndx

        #if self.hascmap == False:
        #    return
        
        currentpos = self.pic.n

        if newndx - currentpos == -1:
            print 'Click left'
            self.updateCache('left')
        elif newndx - currentpos == 1:
            print 'Click right'
            self.updateCache('right')
        elif newndx - currentpos == 0:
            print 'Click same'
            return
        elif newndx < self.datalistlength and newndx >= 0:
            print 'Click skip'
            self.updateCache('click')
        return

    def updateCache(self, strnext):
        '''Updates the image cache
        
        Loads and plots the image at index strnext. Two other images are loaded
        behind and infront of that index. If this index is the first or last
        in the list, it will only have one in front or behind loaded.
        
        Args:
            strnext: An integer representing the next image index
        '''
        
        print 'Update Cache'
        print self.cache
        n = self.pic.n
        if n == -1:
            print 'Cannot traverse ' + strnext
            return
        if strnext == 'left':
            self.newndx = n - 1
            print '%d -> %d' % (n, self.newndx)
            if n == 0:
                return
            else:
                self._innerCache(n, -1)
        elif strnext == 'right':
            self.newndx = n + 1
            print '%d -> %d' % (n, self.newndx)
            if n == self.datalistlength - 1:
                return
            else:
                self.cache.reverse()
                self._innerCache(n, 1)
                self.cache.reverse()
        elif strnext == 'click':
            print '%d -> %d' % (n, self.newndx)
            self.cache.clear()
            if self.newndx == 0:
                self.initCache()
            else:
                self.pic = self.datalist[self.newndx]

                self.cache.append(self.datalist[self.newndx-1])
                self.cache.append(self.pic)
                if self.newndx is not self.datalistlength - 1:
                    self.cache.append(self.datalist[self.newndx+1])
                else:
                    self.cache.append(Image(-1, ''))

                #for i in range(2):
                #    n = self.newndx - i
                #    pic = self.datalist[n]
                #    self.cache.appendleft(pic)
                #    if i == 0:
                #        self.pic = pic
                #        self.plotnow = {}
                #if self.newndx is not self.datalistlength - 1:
                #    temp = self.datalist[self.newndx+1]
                #    self.cache.append(temp)
                #else:
                    self.cache.append(Image(-1, ''))
                    
        print self.cache
        return

    def _innerCache(self, n, i):
        '''Plots new index
        
        Pops off the left side of cache and plots it. The cache is then updated.
        
        Args;
            n: The new index.
            i: Direction the index has traveled. -1 for left and 1 for right.
        '''
        
        self.pic = self.cache.popleft()

        self.cache.appendleft(self.pic)
        if (n > 1 and i == -1) or (n < self.datalistlength-2 and i == 1):
            pic = self.datalist[n+i*2]
            self.cache.appendleft(pic)

        if (n == 1 and i == -1) or (n == self.datalistlength-2 and i == 1):
            self.cache.pop()
        return

    def createRRPlot(self, rrchoice):
        '''Creates a Reduced representation plot
        
        Creates a reduced representation plot for the image that is currently
        being displayed. 
        
        Args:
            rrchoice: The reduced representation to be plotted.
        
        '''
        
        if self.datalistlength is 0 or self.hascmap is True:
            print 'Intensity Map Cannot be (Re)created.......'
            return
        elif rrchoice == 'Choose a Reduced Representation':
            return

        if rrchoice == 'Mean':
            f = lambda x: np.mean(x)

        elif rrchoice == 'Total Intensity':
            f = lambda x: np.sum(x)

        elif rrchoice == 'Standard Deviation':
            f = lambda x: np.std(x)

        elif rrchoice == 'Pixels Above Upper Bound':
            return

        elif rrchoice == 'Pixels Below Lower Bound':
            return

        if rrchoice not in self.rrplots:
            self.rrplots[rrchoice] = rrplot = self.display.plotRRMap(None, rrchoice, None)
        else:
            return

        print 'Generating Intensity Map........'
        for i, image in enumerate(self.datalist):
            image.load()
            print '%d: %s........Loaded' % (i, image.name)
            rr = f(image.data)
            rrplot = self.display.plotRRMap(rr, rrchoice, rrplot)
            image.data = None

        #self.hascmap = True
        print 'Loading Complete'
        return

    def resetViewer(self):
        '''Resets the displays
        
        Resets the displays to the state they were in when the program first 
        loaded.
        '''
        
        print 'Reset'
        if self.hasImage == False:
            return

        self.rrplots = {}
        #self.rrplot = self.display.plotImage(None, 'Total Intensity Map')
        self.hascmap = False
        self.hasImage = False
        self.newndx = -1

        with self.jobqueue.mutex:
            self.jobqueue.queue.clear()
        
        self.cache.clear()
        del self.datalist[:]
        self.datalistlength = 0
        return

    ##############################################
    # Job Processing
    ##############################################
    def startProcessJob(self):
        '''Start Job Process Thread
        
        Call processImage thread and start image processing. This 
        method should be called before the imageload thread.
        '''
        
        self.processing_job.start()
        return
    
    def processJob(self):
        '''Job Processing
        
        Waits for the job queue to fill up and then processes them.
        '''
        
        while True:
            #retrieve job data
            jobdata = self.jobqueue.get(block=True)
            jobtype = jobdata[0]
            kwargs = jobdata[1] if len(jobdata)==2 else {}
            
            #deal with different jobs
            if jobtype == 'newimage':
                self.addNewImage(**kwargs)
            elif jobtype == 'updatecache':
                self.updateCache(*kwargs)
            elif jobtype == 'plotdata':
                self.plotnow = kwargs
            elif jobtype == 'datalistlengthadd':
                self.datalistlengthadd = True
            elif jobtype == 'initcache':
                self.initCache()
            elif jobtype == 'plotrr':
                self.createRRPlot(*kwargs)
            elif jobtype == 'changendx':
                self.changeIndex(*kwargs)
            elif jobtype == 'reset':
                self.resetViewer()
            elif jobtype == 'startload':
                self.startLoad(*kwargs)
            jobdata = []
            self.jobqueue.task_done()
            
        return