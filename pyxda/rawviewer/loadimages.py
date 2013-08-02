#!/usr/bin/env python
import time
import os
import threading
import glob
from enthought.traits.api import HasTraits, Instance, Str

# TODO: Enable Live Mode
class LoadImage(HasTraits, threading.Thread):
    """Thread that loads image paths into queue
    
    Waits until dirpath is not empty and then loads all .tif paths into a list.
    These paths are then inserted into an associated job queue with the title
    'newimage'.
    
    Exceptions:
        TypeError: Is thrown on instantiation when a queue and dirpath are not 
                   specified or are of the wrong type.             
    """

    def __init__(self, queue, dirpath):
        """Constructor called when a LoadImage object is initialized
        
        Creates thread and defines thread attributes. Specifies the directory 
        path. Gives the object access to a queue of processes.

    	Args:
    	    queue:   Job queue of processes  
       	    dirpath: Path of the directory containing the image files 
    	"""
    	
        threading.Thread.__init__(self)
        super(LoadImage, self).__init__() 

        self.dirpath = dirpath
        self.filelist = []

        self.jobqueue = queue
        self.backgroundenable = False
        self.daemon=True
        self.add_trait('message', Str(''))
        
        return

    def run(self):
        """Called when a LoadImage object's start() method is called
        
        Makes method calls that extract tiff images from the directory located
        at dirpath and inserts them into jobqueue.    
    	"""
    	
        self.loadPath()
        self.putPath()
        return

    def loadPath(self):
        """Extracts .tif paths from dirpath into filelist
        
        Loops until dirpath is not empty. When dirpath
        contains a string it will load all .tif file paths in that directory 
        into filelist and break the loop.   
        
        Exceptions:
                 NoTiffs:     Raised when a chosen directory contains no tiff 
                              files
                 InvalidPath: Raised when the path is not real  
    	"""
    	try:
            while True:
                if self.dirpath == '':
                    time.sleep(0.5)
                elif os.path.isdir(self.dirpath):
                    self.filelist = glob.glob(self.dirpath + '/*.tif')
                    if len(self.filelist) == 0:
                            raise Exception('No tiff files in that directory.')
                    self.message = str(' ')
                    break
                else:
                    raise Exception('Invalid file path selected.')
                    break 
        except Exception as msg:
            self.message = str(msg)
        return

    def putPath(self):
        """Inserts paths in filelist into jobqueue with job description
        
        Adds image paths to the queue in the following pattern:
            [['newimage', {'path':<path1>}],
             ['newimage', {'path':<path2>}],
             ['newimage', {'path':<path3>}],
             ['initcache']]
            etc...  
    	"""
        
        #TODO: Hard Coded
        for i in range(len(self.filelist)):
            self.jobqueue.put(['newimage', {'path':self.filelist[i]}])
            if i == 2:
                self.jobqueue.put(['initcache'])
        return