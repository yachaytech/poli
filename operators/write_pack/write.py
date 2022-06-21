#! /usr/bin/env /usr/bin/python3
'''
@file write.py
@author Scott L. Williams.
@package POLI
@brief Write out numpy array as image file. 
@LICENSE
#
#  Copyright (C) 2010-2022 Scott L. Williams.
# 
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
'''
# write out numpy array as image file

# embed copyright in binary
write_copyright = 'write.py Copyright (c) 2010-2022 Scott L. Williams, released under GNU GPL V3.0'

import wx
import os
import sys
import getopt

import numpy as np
from scipy import misc

from op_panel import op_panel, attr

# return an instance of 'write' class 
# without having to know its name
def instantiate():	
    return write( get_name() )

def get_name(): 
    return 'write'

class write_parameters():
    def __init__( self ):
        self.filepath = ''            

class write( op_panel ):          
    def __init__( self, name ):       # initialize op_panel but no graphics
        self.op_id = 'write version 0.0'
        self.params = write_parameters()
        op_panel.__init__( self, name )
        
    def run( self ):                    
        
        # check if source is 2-d, (3-d with 3rd dim = 1)
        height, width, nbands = self.source.shape
        if nbands == 1 :
            self.source.shape = height,width  # really make it 2-d
            
        try:
            misc.imsave( self.params.filepath, self.source )            
            self.sink = self.source            # pass along data
        except IOError:
            print 'bad file name'

        if nbands == 1 :
            self.source.shape = height,width,1 # revert to 3-d 
                                               # with 3rd dim = 1

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        print >> sys.stderr, 'usage: write.py'
        print >> sys.stderr, '       -h, --help'
        print >> sys.stderr, '       -p paramfile, --params=paramfile'
        print >> sys.stderr, '       -f filepath, --file=filepath'
        print >> sys.stderr, '       param file overrides line arguments'
        print >> sys.stderr, '       input is stdin, output is file'

    def set_params( self, argv ):
        params = None
        try:                                
            opts, args = getopt.getopt( argv,
                                        'hp:f:', 
                                        ['help','param=','file='])
        except getopt.GetoptError:           
            self.usage()              
            sys.exit(2)  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit(0)                  
            elif opt in ( '-p', '--params' ):
                params = arg      
            elif opt in ( '-f', '--file' ):
                self.params.filepath = arg    

        if params == None and self.params.filepath == None:
            print >> sys.stderr, \
                'write: warning: no filename given'

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                sys.exit( 2 )

    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):       # scan panel parameters
        self.params.filepath = self.t_filepath.GetValue()

    def write_params_to_panel( self ):        # write parameters to panel
        self.t_filepath.SetValue( self.params.filepath )

    # initialize graphics
    def init_panel( self, benchtop ):
        op_panel.init_panel( self, benchtop ) # start with basics

        # file input text control
        prompt = wx.StaticText( self.p_client, -1, 
                                'enter output filepath:' )
        self.t_filepath = wx.TextCtrl( self.p_client, -1 )       
        self.t_filepath.SetToolTipString( 'enter filename' )
        self.t_filepath.Bind( wx.EVT_KEY_DOWN, self.on_file_key ) 
        dt = FileDrop( self.t_filepath, self )
        self.t_filepath.SetDropTarget( dt )

        # browse directory button
        b_browse = wx.Button( self.p_client, -1, 'browse', 
                              (232,79), (60,25) )
        b_browse.Bind( wx.EVT_LEFT_UP, self.on_browse )             
        b_browse.SetToolTipString( 'browse directory for image file' )

        # implement sizers
        v_sizer = wx.BoxSizer( wx.VERTICAL )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        h_sizer.Add( (4, 1) )   # spacer from left
        h_sizer.Add( prompt, 0, wx.TOP, 8 )  # lower prompt

        h_sizer.Add( (1, 1),1 ) # '1' pushes button to right
        h_sizer.Add( b_browse, 0 )

        v_sizer.Add( h_sizer, 1, wx.EXPAND )
        v_sizer.Add( self.t_filepath, 1, wx.EXPAND )

        self.p_client.SetSizer( v_sizer )

        self.write_params_to_panel()
        
    # intercept keystroke; look for CR
    def on_file_key( self, event ):
        keycode = event.GetKeyCode()

        if keycode == wx.WXK_RETURN:   
            self.on_apply( None )    # as if pressing 'apply' button
        event.Skip()                 # pass along event

    def on_write( self, event ):
        print 'hello'

    # respond to file browse click
    def on_browse( self, event ):
        dlg = wx.FileDialog( self, "Choose an image to read", 
                             os.getcwd(), "", "*", wx.OPEN )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            path = path.strip()
            self.t_filepath.SetValue( path ) # update filename to gui

        dlg.Destroy()

# clean up text after drop in filepath textctrl
# TODO: what happens if x remote dropped?
class FileDrop( wx.FileDropTarget ):
    def __init__( self, window, op_panel ):
        wx.FileDropTarget.__init__(self)
        self.window = window
        self.op_panel = op_panel
        
    # url prefixes get removed as do trailing non-printables
    # just by running through this method; if not intercepted
    # url prefixes and non-printable characters appear
    def OnDropFiles( self, x, y, filenames ):        
        self.window.SetValue( filenames[0] ) # use just the first name
        self.op_panel.on_apply( None )

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':      
    oper = instantiate()           # source point for pipe
    oper.set_params( sys.argv[1:] )
    oper.run()            
    oper.sink.dump( sys.stdout )   # send downstream    
