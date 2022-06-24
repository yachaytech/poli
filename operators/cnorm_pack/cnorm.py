#! /usr/bin/env /usr/bin/python3
'''
@file cnorm.py
@author Scott L. Williams
@package POLI
@brief Normalize all bands using predefined normalization coefficients.
@LICENSE
# 
#  Copyright (C) 2010-2022 Scott L. Williams.
# 
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
# Normalize all bands according to predefined normalization coefficients
# ie. y = mx + c

cnorm_copyright = 'norm.py Copyright (c) 2010-2022 Scott L. Williams, released under GNU GPL V3.0'

import wx
import sys
import getopt
import numpy as np

from op_panel import op_panel

# return an instance of 'norm' class 
# without having to know its name
def instantiate():	
    return cnorm( get_name() )

def get_name(): 
    return 'cnorm'

class FileDrop( wx.FileDropTarget ):         # clean up text after drop
    def __init__( self, window, op_panel ):
        wx.FileDropTarget.__init__(self)
        self.window = window
        self.op_panel = op_panel

    # url prefixes get removed as do trailing non-printables
    # just by running throughg this method; if not intercepted
    # url prefixes and non-printable characters appear
    def OnDropFiles( self, x, y, filenames ):
        try:
            self.window.SetValue( filenames[0] ) # use just the first name
            self.op_panel.on_apply( None )
        except:
            return False
        
        return True

class cnorm_parameters():             # hold arguments values here
    def __init__( self ):
        self.ntype = 0                # 0 for 0 to 1; -1 for -1 to 1
        self.clip = True              # clip to bounds
                                      # TODO: implement checkbox in GUI
        self.filepath = 'ncoeffs.txt' 

class cnorm( op_panel ):
    def __init__( self, name ):      # initialize op_panel but no graphics
        op_panel.__init__( self, name )

        self.cfile = None
        self.op_id = 'cnorm version 0.0'
        self.params = cnorm_parameters()

    # convert band range to floor to ceiling
    def scale_band( self, image, scale, offset, ntype ):

        norm = image*scale + offset

        # clip to bounds
        if self.params.clip:
            norm = np.clip( norm, ntype, 1 )
            
        return norm

    def run( self ):                 # override superclass 

        # read the number of bands and normalization type from file
        try:
            cfile = open( self.params.filepath, 'r' )
        except:
            print( 'cnorm: could not open file: ', self.params.filepath,
                   file=sys.stderr)
            return

        items = cfile.readline().split(',')
        numbands = int( items[0].strip() )
        ntype = int( items[1].strip() )
                       
        height,width,nbands = self.source.shape
        if numbands != nbands:
            print( 'cnorm: number of bands to not match', file=sys.stderr )
            return
        
        # create output buffer
        self.sink = np.empty( (height,width,nbands), dtype=np.float32 )

        # normalize each band according to coefficients
        for i in range( nbands ):
            
            line = cfile.readline()
            items = line.split(',')

            band = int( items[0].strip() )
            scale = float( items[1].strip() )
            offset = float( items[2].strip() )

            self.sink[:,:,band] = self.scale_band( self.source[:,:,band],
                                                   scale, offset, ntype )

    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):     # scan panel parameters
        
        # set filename to use
        self.params.filepath = self.t_filepath.GetValue()
 
    def write_params_to_panel( self ):       # write parameters to panel
        
        # write filepath
        self.t_filepath.SetValue( self.params.filepath )
            
    # initialize graphics
    def init_panel( self, benchtop ):
        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        prompt = wx.StaticText( self.p_client, -1, '  read normalization coefficients file:' )
        v_sizer.Add( prompt )
        v_sizer.Add( (10,20) )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        # file input text control
        self.fprompt = wx.StaticText( self.p_client, -1, '  enter filepath:' )
        h_sizer.Add( self.fprompt )
        
        self.t_filepath = wx.TextCtrl( self.p_client, -1, '', size=(500,30) )
        self.t_filepath.SetToolTip( 'enter filepath for norm coefficients' )
        dt = FileDrop( self.t_filepath, self )   # clean string after drop
        self.t_filepath.SetDropTarget( dt )

        dt = FileDrop( self.t_filepath, self )   # clean string after drop
        self.t_filepath.SetDropTarget( dt )

        h_sizer.Add( self.t_filepath )
        v_sizer.Add( h_sizer )
        
        self.p_client.SetSizer( v_sizer )
        
        self.write_params_to_panel()

    # intercept keystroke; look for CR
    def on_file_key( self, event ):
        keycode = event.GetKeyCode()

        if keycode == wx.WXK_RETURN:   
            self.on_apply( None )     # as if pressing 'apply'
        event.Skip()                  # pass along event

    ############################################################
    # command line options for batch implementation
    ############################################################

    def usage( self ):
        print( 'usage: cnorm.py', file=sys.stderr )
        print( '       -h, --help', file=sys.stderr )
        print( '       -f coeff_file', file=sys.stderr )
        print( '       -p param_file, --params=param_file', file=sys.stderr )
        print( '       input is stdin, output is stdout', file=sys.stderr )

    def set_params( self, argv ):
        params = None
        file_given = False
        
        try:                                
            opts, args = getopt.getopt( argv, 'h:',['help'])
            
        except getopt.GetoptError:           
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit(0)
            elif opt in ( '-f', '--file' ):
                self.params.filepath = arg
                file_given = True
            elif opt in ('-p', '--params'):
                params = arg  

        if not file_given and params == None:
            print( "cnorm.py: no filename given...exiting", file=sys.stderr)
            sys.exit(2)

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                print( "cnorm.py: cannot read parameter file", file=sys.stderr)
                sys.exit(2)


####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':
    import os
    import tempfile

    oper = instantiate()   
    oper.set_params( sys.argv[1:] )

    # numpy needs to 'seek' in the file to load
    # so read from stdin to temporary file first
    temp_name = next(tempfile._get_candidate_names()) + '.tmp'
    temp = open( temp_name, 'wb' )
    temp.write( sys.stdin.buffer.read() )
    temp.close()

    # load the pickled data
    oper.source = np.load( temp_name, allow_pickle=True,fix_imports=False)
    os.remove( temp_name )

    oper.run()                  
    oper.sink.dump( sys.stdout.buffer )          # send downstream    
