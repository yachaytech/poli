#! /usr/bin/env /usr/bin/python3

'''
@file cetin.py
@author Scott L. Williams.
@package POLI
@brief# Generate a cetin source image for POLI SOM operators.
@LICENSE
# 
#  Copyright (C) 2010-2024 Scott L. Williams.
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

# generate a cetin image operator for poli 

cetin_copyright = 'cetin.py Copyright (c) 2010-2024 Scott L. Williams released under GNU GPL V3.0'

import wx
import sys
import getopt

import numpy as np

from threads import apply_thread     # our imports
from threads import monitor_thread
from op_panel import op_panel

# return an instance of 'cetin' class 
# without having to know its name
def instantiate():	
    return cetin( get_name() )

def get_name():
    return 'cetin'

class cetin_parameters():
    def __init__( self ):
        pass

class cetin( op_panel ):
    def __init__( self, name ): # initialize op_panel but no graphics
        op_panel.__init__( self, name )
        self.op_id = 'cetin version 0.0'
        self.params = cetin_parameters()
        
    def run( self ):            # override superclass run

        # create a test image for SOM operators
        self.sink = np.empty( (128,128,6), dtype=np.uint8 )

        self.sink[:,0:32,0] = 21
        self.sink[:,32:128,0] = 0

        self.sink[:,0:64,1] = 42
        self.sink[:,64:128,1] = 63

        self.sink[0:32,:,2] = 105
        self.sink[32:128,:,2] = 84

        self.sink[:,0:96,3] = 126
        self.sink[:,96:128,3] = 147

        self.sink[0:96,:,4] = 168
        self.sink[96:128,:,4] = 189

        self.sink[0:64,:,5] = 210
        self.sink[64:128,:,5] = 231
 
    ####################################################################
    # gui section
    ####################################################################

    # override on_apply to intercept event
    def on_apply( self, obj ):

        # report to message box
        self.benchtop.messages.append( '\n\tid:\t\t\t\t' + 
                                       self.op_id + '\n' )
        self.b_apply.Enable( False )
        self.b_cascade.Enable( False )
        self.b_cancel.Enable( True )

        self.c_merge.Enable( False )
        self.b_options.Enable( False )

	# get parameter values from panel
        self.read_params_from_panel()

        # spawn processing thread
        self.app_cancelled = False     
        self.app_thread = apply_thread( self ) 
        self.app_thread.start()

        # spawn another thread to keep track of app thread
        mon_thread = monitor_thread( self )
        mon_thread.start()

    # overide since we are a source and need to handle
    # thread slightly different
    def apply_work( self ):
        self.run()            # run the operator

        #if self.sink == None:         
        if type( self.sink ) is not np.ndarray:
            return

        # generic label
        self.band_tags = ['0','1','2','3', '4', '5']

    # scan panel parameters
    def read_params_from_panel( self ):
        pass

    # write parameters to panel
    def write_params_to_panel( self ):
        pass

    # initialize graphics
    def init_panel( self, benchtop ):
        op_panel.init_panel( self, benchtop ) # start with basics

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        print( 'usage: cetin.py', file=sys.stderr )
        print( '       -h, --help', file=sys.stderr )
        print( '       there are no other parameters', file=sys.stderr )
        print( '       output is stdout', file=sys.stderr )

    def set_params( self, argv ):

        try:                                
            opts, args = getopt.getopt( argv, 'h', ['help'])
        except getopt.GetoptError:           
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                usage()                     
                sys.exit(0)                  

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':             
    oper = instantiate()                  # source point for pipe
    oper.set_params( sys.argv[1:] )
    oper.run()

    # send downstream    
    np.save( sys.stdout.buffer, oper.sink, allow_pickle=False ) 
