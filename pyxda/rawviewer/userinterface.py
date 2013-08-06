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

from traits.api import HasTraits, Instance
from enthought.traits.ui.api import View, HSplit,VSplit, VGroup, UItem, Group, Item
from traits.api import on_trait_change
from enable.api import ComponentEditor, Component
from enthought.traits.ui.menu import NoButtons
from chaco.api import HPlotContainer, VPlotContainer

from rawviewer import RawViewer
from controlpanel import ControlPanel, MetadataPanel, MessageLog
from handler import PyXDAHandler
import sys
import time
from enthought.pyface.image_resource import ImageResource

LOGO = ImageResource('SrXes-Icon.ico')

class UserInterface(HasTraits):
    '''UserInterface Class
    
    GUI for SrXes. Uses traits to watch for user interaction and then adds
    jobs to a queue for processing. 
    '''

    def __init__(self, **kwargs):
        '''Constructor for UserInterface object
        
        Adds panels and plots to a userinterface window.
        '''
        
        super(UserInterface, self).__init__()
        self.add_trait('rawviewer', RawViewer())
        self.add_trait('cpanel', ControlPanel())
        self.add_trait('mdpanel', MetadataPanel())
        self.add_trait('messagelog', MessageLog())

        self.rawviewer.startProcessJob()
        self.cpanel.sync_trait('datalistlength', self.rawviewer)

        self.imagepanel = Instance(Component)
        self.createImagePanel()
        self.rrpanel = Instance(Component)
        self.rrpanel = VPlotContainer(stack_order = 'top_to_bottom',
                                        resizeable='', use_backbuffer=True,
                                        bgcolor='transparent')
        self.rrpanel.get_preferred_size()
    
    

    # TODO: Adjust view
    view = View(
             HSplit(
               VSplit(
                    UItem('imagepanel', editor=ComponentEditor(), padding=0),
                    UItem('mdpanel', style="custom", padding=5, height=85, width=700)
                     ),
               VGroup(
                    UItem('cpanel', style="custom", width=-430, padding=10),
                    UItem('messagelog', style ="custom", width=-430, padding =10),
                    UItem('rrpanel', editor=ComponentEditor(), style='custom')
                     ),
                show_labels=False,
                  ),
            resizable = True,
            height = 0.96, width = 1.0,
            handler = PyXDAHandler(),
            buttons = NoButtons,
            title = 'SrXes',
            icon = LOGO)

    #############################
    # UI Action Handling
    #############################
    @on_trait_change('cpanel.left_arrow', post_init=True)
    def _left_arrow_fired(self):
        '''Left arrow has been pushed
        
        Changes the image display to the left one over if it exists.
        '''
        
        self.rawviewer.jobqueue.put(['updatecache', ['left']])
        return
    
    @on_trait_change('cpanel.right_arrow', post_init=True)
    def _right_arrow_fired(self):
        '''Right arrow has been pushed
        
        Changes the image display to the right one over if it exists.
        '''
        
        self.rawviewer.jobqueue.put(['updatecache', ['right']])
        return
    
    @on_trait_change('cpanel.generate', post_init=True)
    def _generate_fired(self):
        '''Generate Intensity button has been pushed
        
        Creates a reduced representation plot in the GUI.
        '''
        
        self.rawviewer.jobqueue.put(['plotrr', [self.cpanel.rrchoice]])
        time.sleep(0.5)
        self.updateRRPanel(self.cpanel.rrchoice)
        return
    
    @on_trait_change('cpanel.dirpath', post_init=True)
    def _dirpath_changed(self):
        '''Directory path has changed
        
        If there are tiff images in the folder path, they will be loaded and 
        the first image will be plotted to the screen. If there are no tiff
        images or the path is invalid, rawviewer.message will be changed to a
        string explaining the error.
        '''
        
        self.rawviewer.jobqueue.put(['startload', [self.cpanel.dirpath]])
    
    @on_trait_change('rawviewer.pic', post_init=True)
    def _pic_changed(self):
        '''The displayed 2D image has been changed
        
        Changes the control panel index, and the metadata associated with it.
        '''
        
        pic =  self.rawviewer.pic
        self.cpanel.index = pic.n + 1
        self.mdpanel.name = pic.name
        if pic.metadata:
            for key in pic.metadata.keys():
                setattr(self.mdpanel, key, pic.metadata[key])
        return
        
    @on_trait_change('rawviewer.display.filename', post_init=True)
    def _filename_changed(self):
        '''The filename of the 2D image has changed
        
        Changes the displayed filename to the updated one.
        '''
        
        print 'filename changed'
        if self.rawviewer.display.filename == -1:
            self.cpanel.filename = ''
        else:
            self.cpanel.filename = self.rawviewer.datalist[self.rawviewer.display.filename].name
    
    @on_trait_change('rawviewer.loadimage.message', post_init=True)
    def handleMessage(self):
        '''Rawviewer.message has changed
        
        Displays the new message in messagelog. If there is already a message 
        inside messagelog, the new one is plotted below it.
        '''
    
        if self.rawviewer.loadimage.message != '':
            if self.messagelog.line_pos == 0:     
                self.messagelog.line1 = 'Out: ' + self.rawviewer.loadimage.message
                self.messagelog.line_pos = self.messagelog.line_pos +1
                return
            if self.messagelog.line_pos == 1:
                self.messagelog.line2 = 'Out: ' + self.rawviewer.loadimage.message
                self.messagelog.line_pos = self.messagelog.line_pos + 1
                return
            if self.messagelog.line_pos == 2:
                self.messagelog.line3 = 'Out: ' + self.rawviewer.loadimage.message
                self.messagelog.line_pos = 0
                return
        return

    
    # TODO: Update
    def createImagePanel(self):
        '''Creates the Image Panel
        
        Creates the image panel that contains the 2D image, colorbarm histogram,
        and 1D slice.
        '''
        
        cont = VPlotContainer(stack_order = 'top_to_bottom',
                                bgcolor = 'transparent',
                                use_backbuffer=True)

        imageplot = getattr(self.rawviewer, 'imageplot')
        colorbar = getattr(self.rawviewer.display, 'colorbar')
        histogram = getattr(self.rawviewer, 'histogram')
        plot1d = getattr(self.rawviewer, 'plot1d')

        imgcont = HPlotContainer(imageplot, colorbar, bgcolor = 'transparent',
                                    spacing = 20.0)
        cont.add(imgcont)
        cont.add(histogram)
        cont.add(plot1d)
        
        self.imagepanel = cont
        self.imagepanel.get_preferred_size()
        self.imagepanel.invalidate_draw()
        return

    def updateRRPanel(self, choice):
        '''Updates the Reduced Representation Panel
        
        Args:
            choice: the new variable for the RR. eg: mean, total intensity...
        '''
        
        rrplots = getattr(self.rawviewer, 'rrplots')
        
        if rrplots[choice] not in self.rrpanel._components:
            self.rrpanel.add(rrplots[choice])

        self.rrpanel.invalidate_and_redraw()
        return

def main():
    '''Initializes the GUI window'''
    
    ui = UserInterface()
    ui.configure_traits()

if __name__ == '__main__':
    sys.exit(main())
