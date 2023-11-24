'''
@file benchtop.py
@author Scott L. Williams
@pakage POLI
@brief top wxPanel for Python On Line Imaging (POLI)
@section LICENSE

#  Copyright (C) 2010-2024 Scott L. Williams.

#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

@section DESCRIPTION
Top level panel for POLI, a graphical interface for data processing usng NumPy.
'''
bench_top_copyright = 'benchtop.py Copyright (c) 2010-2024 Scott L. Williams, released under GNU GPL V3.0'

#  top panel for all poli components
import os
import wx
import sys
import configparser

# our modules
from display import display_panel

from oper_mess import oper_mess
from pan_tools import pan_tools
from pan_zoom import zoomer

class benchtop( wx.Panel ): 
    def __init__( self, parent, config_file ):
        wx.Panel.__init__( self, parent, 
                           style=wx.SUNKEN_BORDER )

        self.SetPosition( (6,2) )    # make border visible from frame

        # constant panel sizes
        self.UTIL_SIZE_X = 272       # utility panel 222
        self.OPER_SIZE_Y = 220       # operator panel
        self.REPORT_SIZE_Y = 20      # report line
        self.MIN_DISPLAY_SIZE = 520  # min size for display panel

        self.version = 'version 2020.07' # need this?
        self.op = []                 # start the operator list

        # setting the project locator, initializes everything
        self.setup_project( config_file )

    # resize the top panel and layout components
    def layout( self, size ):
        size -= ( 21,21 )            # allows scroll bars te shown

        min_total_x = self.MIN_DISPLAY_SIZE + self.UTIL_SIZE_X + 6
        min_total_y = self.OPER_SIZE_Y + self.MIN_DISPLAY_SIZE \
                      + self.REPORT_SIZE_Y + 6

        # current mins =(528,546)

        # check for minimum size
        if size.x < min_total_x:
            size.x = min_total_x     # overide x size

        if size.y < min_total_y:
            size.y = min_total_y     # overide y size

        self.SetClientSize( size )   # adjust benchtop panel size
        
        # set report line position and size
        self.report.SetPosition( (0,0) )
        self.report.SetSize( (size.x, self.REPORT_SIZE_Y) )

        self.set_display_size( size )
        self.set_split_panels( size )

    def set_split_panels( self, size ):          # position splitter windows
        d_size = self.display.GetSize()
        
        # set position and size for the pan and tools split panel
        self.pan_tools.SetPosition( (d_size.x+1, self.REPORT_SIZE_Y) )
        self.pan_tools.SetSize( (self.UTIL_SIZE_X, d_size.y) )

        # set position and size for operator and message split panel
        self.oper_mess.SetPosition( (0, d_size.y+
                                     self.REPORT_SIZE_Y+1) )
        self.oper_mess.SetSize( (size.x,
                                 self.OPER_SIZE_Y ) )

        # make sash follow display size
        self.oper_mess.SetSashPosition( d_size.x-2, True )

    # setup initial locators from  project config file
    def setup_project( self, config_file ):
        self.setup_suite_locators( config_file ) # find project locator files
        self.DestroyChildren()                   # remove existing panels
                        
        # create components for this panel

        # set up the display canvas
        self.display = display_panel( self )
        
        # set up a report line on top of panel
        size = self.GetClientSize()  
        self.report = wx.StaticText( self, -1, '', (size.x, 20), 
                                     style=wx.ALIGN_LEFT )

        # setup operator and message panels (bottom panel)
        self.oper_mess = oper_mess( self )
        self.messages = self.oper_mess.messages
        self.op_note = self.oper_mess.op_note

        # set up utilities (side panel)
        self.pan_tools = pan_tools( self )  # create top level split panes
        self.pan = self.pan_tools.pan
        self.zoom = zoomer( self )          # manages display size

    def set_display_size( self, size ):     # resize display panel

        # set the display position and size
        size_x = size.x - self.UTIL_SIZE_X - 1
        size_y = size.y - self.OPER_SIZE_Y - self.REPORT_SIZE_Y - 1

        self.display.SetPosition( (0,self.REPORT_SIZE_Y) )
        self.display.SetSize( (size_x,size_y) )      

    # setup initial locators for operators and images
    def setup_suite_locators( self, config_file ):

        # set locators to None in case of bad or null file
        self.operator_suites = None
        self.image_suites = None
        self.project_config = None

        if config_file == None:
            return

        if not os.path.isfile( config_file ):
            print('configuration file ' + config_file + 'is not a file',
                  file=sys.stderr )
            return

        project = configparser.RawConfigParser()
        project.read( config_file )  # TODO: catch open error
             
        # project config is meant to be only an initialization 
        # TODO: add suites via menu
       
        try:
            # store suite locators
            self.operator_suites = project.items( 'operator_suites' )
            self.image_suites = project.items( 'image_suites' )

            # TODO: add sessions and output data locators here

        except configparser.ReadError as e:    
            print( 'setup_suite_locator error: ', file=sys.stderr )
            print( e, file=sys.stderr )
            return

        self.proj_config = config_file   # retained only for reporting 
                                         # not used again

    # distribute images and data to controls
    def set_images( self, op_panel, index=None ):
        self.pan.set_source( op_panel.thumb_image )
        index = self.zoom.set_source( op_panel.display_image,
                                      op_panel.display_overlay_image,
                                      index )

        # register origin and scale with this operator
        op_panel.areal_index = index

        # register navigation data to display image
        self.pan_tools.nav.set_nav_data( op_panel.nav_data,
                                         op_panel.nav_tags,
                                         op_panel.sink )

        self.pan_tools.hist.set_histogram( op_panel.hist )

    def clear( self ):          # clear sub-panels of graphics
        self.display.clear()
        self.pan.clear()
        self.pan_tools.nav.clear()
        self.pan_tools.hist.clear()
         
    def finalize( self ):       # make a clean exit
        pass                    # don't seem to need it now
        #self.op_note.finalize()
 
    '''
    // 
    public void finalizeOperators() {
        
        OpPanel o = null;
        
        int last  = op.size();
        
        // work through the operators
        for ( int i=0; i<last; i++ ) {

            // get the operator and process
            o = (op.get(i));
            o.opFinalize();
        } 
        
	// check if an mpi operator has instantiated 
	// a finalize method
	if ( mpiLib != null ) {
	    mpiLib.Finalize();
	}
	    
    } // end finalizeOperators
    '''

# end benchtop.py
