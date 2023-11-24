#! /usr/bin/env /usr/bin/python3

'''
@file npy_source.py
@author Scott L. Williams
@package POLI
@brief Reads a numpy pickle file.
@section LICENSE
# 
#  Copyright (C) 2016-2024 Scott L. Williams.
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

# create a source operator from numpy pickle file

npy_source_copyright = 'npy_source.py Copyright (c) 2016-2024 Scott L. Williams,released under GNU GPL V3.0'

import os
import wx
import sys
import urllib
import getopt

import numpy as np

from threads import apply_thread
from threads import monitor_thread
from op_panel import op_panel

# return an instance of 'npy_source' class 
# without having to know its name
def instantiate():	
    return npy_source( get_name() )

def get_name(): 
    return 'npy_source'

class FileDrop( wx.FileDropTarget ):         # clean up text after drop
    def __init__( self, window, op_panel ):
        wx.FileDropTarget.__init__(self)
        self.window = window
        self.op_panel = op_panel

    # url prefixes get removed as do trailing non-printables
    # just by running throughg this method; if not intercepted
    # url prefixes and non-printable characters appear
    def OnDropFiles( self, x, y, filenames ):        
        self.window.SetValue( filenames[0] ) # use just the first name
        self.op_panel.on_apply( None )

class npy_source_parameters():
    def __init__( self ):
        self.filepath = ''             # input numpy file
        self.mmap = False              # is source memory mapped?

class npy_source( op_panel ):          # numpy source operator

    def __init__( self, name ):        # initialize op_panel but no graphics
        op_panel.__init__( self, name )
        self.op_id = 'npy_source version 0.0'
        self.params = npy_source_parameters()
        
    def run( self ):                   # override superclass run

        try:
            if self.params.filepath[:7] == 'file://'  or \
               self.params.filepath[:7] == 'http://' :
                
                filep = request( self.params.filepath )[0]
                
                # not sure how this works with http:// or file://
                # TODO: test both on memory map
                if self.params.mmap:
                    print('\nnpy_source: cannot use memory mapping on http files',
                           file=sys.stderr)
                    sys.exit( 1 )
                else:
                    self.sink = np.load( filep, mmap=None, allow_pickle=False )
                    print( '\nnpy_source: using ram memorg', file=sys.stderr) 

            # regular filepath
            else:
                if self.params.mmap:
 
                    self.sink = np.load( self.params.filepath,
                                         mmap_mode='r',
                                         allow_pickle=False )
  
                    print( '\nnpy_source: using memory mapping', file=sys.stderr) 

                else:
                    self.sink = np.load( self.params.filepath,
                                         mmap_mode=None,
                                         allow_pickle=False )
                    print( 'npy_source: using ram memory', file=sys.stderr) 

        except OSError as e:
            print( e, file=sys.stderr )
            print( 'cannot open file: ' + self.params.filepath,
                   file=sys.stderr )
            self.sink = None
            return

        # accept only 2d or 3d  arrays
        if self.sink.ndim < 2 or self.sink.ndim > 3 :
            print( 'npy_source: bad number of dimensions, must be 2 or 3',
                   file=sys.stderr)
            print( '            received dim= ' + data.ndim + ' for file: ' )
            print( '            ' + filepath )
            self.sink = None
            return

        # make 2d buffer into 1 band 3d buffer
        if self.sink.ndim == 2 :
            height,width = self.sink.shape
            self.sink.shape = height,width,1

        self.source_name = self.params.filepath

    ####################################################################
    # gui section
    ####################################################################

    # override on_apply to intercept event
    def on_apply( self, obj ):
        if isinstance(obj, str):             # we've been invoked by
            obj.strip()                      # image_tree or file drop
            self.t_filepath.SetValue( obj )            

        # report to message box
        self.benchtop.messages.append ( '\n\tid:\t\t\t\t' + 
                                        self.op_id + '\n' )
        self.b_apply.Enable( False )
        self.b_cascade.Enable( False )
        self.b_cancel.Enable( True )

        self.c_merge.Enable( False )
        self.b_options.Enable( False )

	# get parameter values from panel
        self.read_params_from_panel()
        self.benchtop.messages.append( '\tingesting:\t\t' + 
                                       self.params.filepath + '\n' )

        # spawn processing thread
        self.app_cancelled = False     
        self.app_thread = apply_thread( self ) 
        self.app_thread.start()

        # spawn another thread to keep track of app thread
        mon_thread = monitor_thread( self )
        mon_thread.start()

    # override since we are a source and need to handle
    # thread slightly different
    def apply_work( self ):
        self.run()          # run the operator

        if not isinstance( self.sink, np.ndarray ):
            print( 'image is NOT type numpy.ndarray', file=sys.stderr )
            return

        # buffer tags are lost
        
    def read_params_from_panel( self ):       # scan panel parameters
        self.params.filepath = self.t_filepath.GetValue()

    def write_params_to_panel( self ):        # write parameters to panel
        self.t_filepath.SetValue( self.params.filepath )

    # initialize graphics
    def init_panel( self, benchtop ):
        op_panel.init_panel( self, benchtop ) # start with basics

        # file input text control
        prompt = wx.StaticText( self.p_client, -1, 'enter numpy filepath:' )

        self.t_filepath = wx.TextCtrl( self.p_client, -1 )
        self.t_filepath.SetToolTip( 'enter image filepath' )
        self.t_filepath.Bind( wx.EVT_KEY_DOWN, self.on_file_key) 
        dt = FileDrop( self.t_filepath, self )   # clean string after drop
        self.t_filepath.SetDropTarget( dt )

        # browse directory button
        b_browse = wx.Button( self.p_client, -1, 'browse', 
                              (232,79), (60,25) )
        b_browse.Bind( wx.EVT_LEFT_UP, self.on_browse )             
        b_browse.SetToolTip( 'browse directory for image file' )

        # implement sizers
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( (1,69) )  # add space

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        h_sizer.Add( (4, 1) ) # spacer from left
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

    # respond to file browse click
    def on_browse( self, event ):
        dlg = wx.FileDialog( self, 'Choose an image to read', 
                             os.getcwd(), "", "*", wx.FD_OPEN )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            path = path.strip()
            self.t_filepath.SetValue( path ) # update filename to gui

        dlg.Destroy()

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        print( 'usage: source.py', file=sys.stderr )
        print( '       -h, --help',file=sys.stderr )
        print( '       -f filepath, --file=filepath',file=sys.stderr )
        print( '       -p paramfile, --params=paramfile', file=sys.stderr )
        print( '       input is filepath, output is stdout',file=sys.stderr )

    def set_params( self, argv ):
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hf:p:', ['help','file=','params='])
        except getopt.GetoptError:           
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                usage()                     
                sys.exit(0)                  
            elif opt in ( '-f', '--file' ):
                self.params.filepath = arg
            elif opt in ( '-p', '--params' ):
                params = arg

        if params == None and self.params.filepath == '':
            print( 'source:set_params: no filename given', file=sys.stderr )
            sys.exit( 2 )

        if params != None:
            ok = self.read_params_from_file( str(params) )
            if not ok:
                print( 'source:set_params: bad params file read',
                       file=sys.stderr )
                sys.exit( 2 )

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':      
    oper = instantiate()                  # source point for pipe
    oper.set_params( sys.argv[1:] )
    oper.run()

    # send downstream  
    np.save( sys.stdout.buffer, oper.sink, allow_pickle=False )  

