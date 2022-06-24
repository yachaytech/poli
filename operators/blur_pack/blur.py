#! /usr/bin/env /usr/bin/python3

'''
@file blur.py
@author Scott L. Williams.
@package POLI
@brief Gaussian or flat blur operator for POLI.
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
blur_copyright = 'blur.py Copyright (c) 2010-2022 Scott L. Williams, released under GNU GPL V3.0'

import wx
import sys
import getopt
import numpy as np
from scipy import ndimage as nd

from op_panel import op_panel

# return an instance of 'blur' class 
# without having to know its name
def instantiate():
    return blur( get_name() )

def get_name():                
    return 'blur'

class blur_parameters():        # hold arguments values here
    def __init__( self ):
        self.type = 2           # types are 1=flat, 2=gauss
        self.times = 1          # how many times to blur image

class blur( op_panel ):
    def __init__( self, name ): # initialize op_panel but no graphics
        op_panel.__init__( self, name )
        
        self.op_id = 'blur version 0.0'
        self.params = blur_parameters()
        
    def run( self ):            # override superclass run
        height,width,nbands = self.source.shape

        # make output float
        temp = np.empty( (height,width,nbands),
                              dtype=np.float32 )

        if self.params.type == 1:
            kernel = np.array( [1.0, 1.0, 1.0,  # column vectors
                                1.0, 1.0, 1.0,
                                1.0, 1.0, 1.0 ] )
            kernel.shape = 3,3,1
            factor = 9

        elif self.params.type == 2:
            kernel = np.array( [1.0, 1.0, 1.0,  # column vectors
                                1.0, 5.0, 1.0,
                                1.0, 1.0, 1.0 ] )
            kernel.shape = 3,3,1
            factor = 13

        blur = self.source

        for i in range( 0, self.params.times ):
            nd.convolve( blur, kernel, output=temp )
            blur = temp/factor
        self.sink = blur

 
    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):       # scan panel parameters
        if self.r_flat.GetValue():
            self.params.type = 1
        elif self.r_gauss.GetValue():
            self.params.type = 2
        self.params.times = int(self.t_times.GetValue())

    def write_params_to_panel( self ):        # write parameters to panel
        if  self.params.type == 1:
            self.r_flat.SetValue( True )
        if  self.params.type == 2:
            self.r_gauss.SetValue( True )

        self.t_times.SetValue( str( self.params.times ) )

    # initialize graphics
    def init_panel( self, benchtop ):
        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        #  mark the beginning of the group with wx.RB_GROUP
        self.r_flat = wx.RadioButton( self.p_client, -1, 'flat', 
                                      style = wx.RB_GROUP )
        h_sizer.Add( self.r_flat )
        self.r_gauss = wx.RadioButton( self.p_client, -1, 'gauss' )
        h_sizer.Add( self.r_gauss )
        v_sizer.Add( h_sizer )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( self.p_client, -1, 'times:' )
        h_sizer.Add( prompt )
        self.t_times = wx.TextCtrl( self.p_client, -1, '' )
        h_sizer.Add( self.t_times )
        v_sizer.Add( h_sizer )
        self.p_client.SetSizer( v_sizer )
        self.write_params_to_panel()

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        print( 'usage: blur.py', file=sys.stderr )
        print( '       -h, --help', file=sys.stderr )
        print( '       -t <flat,gauss>, --type=<flat,gauss>', file=sys.stderr )
        print( '       -n num of times, --num=num of times>', file=sys.stderr )
        print( '       -p paramfile, --params=paramfile', file=sys.stderr )
        print( '       param file overrides line arguments', file=sys.stderr )
        print( '       input is stdin, output is stdout', file=sys.stderr )

    def set_params( self, argv ):
        params = None

        try:                                
            opts, args = getopt.getopt( argv, 'ht:n:p:',
                                        ['help','type=','num=','params='])
        except getopt.GetoptError:           
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit(0)   

            elif opt in ( '-t', '--type' ):                
                if arg == 'flat':
                    self.params.type = 1
                elif arg == 'gauss':
                    self.params.type = 2 
                else:
                    print('blur: bad type:', arg, file=sys.stderr )
                    sys.exit(2)

            elif opt in ( '-n', '--num' ):
                self.params.times = int( arg )

            elif opt in ( '-p', '--params' ):
                    params = arg

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                print( 'blur:set_params: bad params file read',
                       file=sys.stderr )
                sys.exit( 2 )

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':
    import os
    import tempfile

    oper = instantiate()
    oper.set_params(sys.argv[1:] )

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
