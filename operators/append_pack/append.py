#! /usr/bin/env /usr/bin/python3

'''
@file append.py
@author Scott L. Williams.
@package POLI
@brief Append the source buffer to current buffer.
@LICENSE
# 
#  Copyright (C) 2020-2024 Scott L. Williams.
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
append_copyright = 'append.py Copyright (c) 2020-2024 Scott L. Williams, released under GNU GPL V3.0'

import wx
import sys
import getopt
import numpy as np

from op_panel import op_panel

# return an instance of 'append' class 
# without having to know its name
def instantiate():
    return append( get_name() )

def get_name():                
    return 'append'

class append_parameters():        # hold arguments values here
    def __init__( self ):
        pass

class append( op_panel ):
    def __init__( self, name ): # initialize op_panel but no graphics
        op_panel.__init__( self, name )
        
        self.op_id = 'append version 0.0'
        self.params = append_parameters()

        self.empty = True
        self.height = None
        self.width = None
        self.nbands = None
        
    def run( self ):            # override superclass run

        if self.empty:
            
            # use source buffer as initial buffer
            self.sink = self.source

            # save shape for later checks
            self.height,self.width,self.nbands = self.source.shape

            self.empty = False
            return
        
        # get new image shape to check old width and nbands
        height,width,nbands = self.source.shape
        if self.width != width:
            print( 'append:run: widths do not match: ', self.width, width,
                   file=sys.stderr )
            return
        
        if self.nbands != nbands:
            print( 'append:run: nbands do not match: ', self.nbands, nbands,
                   file=sys.stderr )
            return
        
        self.sink = np.append( self.sink, self.source, axis=0 )
        
    ####################################################################
    # gui section
    ####################################################################

    # set up processing; called from app over-rides op_panel apply_work
    def apply_work( self ):           

        # get input image from a neighbor operator
        self.source = self.get_source( 1 )
        
        # is neighbor sink image set?
        if type( self.source ) is not np.ndarray:

            print( 'op_panel:apply_work: ' + \
                   'neighbor sink (output) image not set',
                   file=sys.stderr )
            return

        if self.empty:
            self.set_areal_tags( 1 )        # inherit nav and band tags
            self.run()                      # run the operator

        else:
            self.run()

            # append nav data if any
            # FIXME: if current image has nav data but but appending does not
            #        then fill nav data with Nones or Nans
            try: 
                if type(self.nav_data) is np.ndarray:
                    src_op = self.get_source_op( 1 )
                    if type(src_op.nav_data) is np.ndarray:
                        self.nav_data = np.append( self.nav_data,
                                                   src_op.nav_data,
                                                   axis=0 )
            except:
                pass

            self.areal_index = None # centers and scales new image

    def read_params_from_panel( self ):
        pass

    def write_params_to_panel( self ):
        pass

    # initialize graphics
    def init_panel( self, benchtop ):
        op_panel.init_panel( self, benchtop ) # start with basics

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        print( 'usage: append.py', file=sys.stderr )
        print( '       -h, --help', file=sys.stderr )
        print( '       input is stdin, output is stdout', file=sys.stderr )

    def set_params( self, argv ):

        try:                                
            opts, args = getopt.getopt( argv, 'h', ['help'])
        except getopt.GetoptError:           
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit(0)
                
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

    # load the data
    oper.source = np.load( temp_name, allow_pickle=False )
    os.remove( temp_name )
    oper.run()
    
     # send downstream
    np.save( sys.stdout.buffer, oper.sink, allow_pickle=False )    
