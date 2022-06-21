#! /usr/bin/env /usr/bin/python3
'''
@file render.py
@author Scott L. Williams
@package POLI
@brief Writes a numpy data array into an image file.
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

# poli sink operator that renders data array into an image format
# TODO: make an op_panel version

render_copyright = 'render.py Copyright (c) 2010-2022 Scott L. Williams, released under GNU GPL V3.0'

import sys
import getopt
import numpy as np

from op_panel import op_panel
from PIL import Image	

# return an instance of 'render' class 
# without having to know its name
def instantiate():	
    return render( get_name() )

def get_name(): 
    return 'render'

class render_parameters():       # hold arguments values here
    def __init__( self ):
        self.filepath = ''
        self.grey = None
        self.red = None
        self.grn = None
        self.blu = None
        self.lut = None          

# render data into an image format of 3-bands
class render( op_panel ):
    def __init__( self, name ):
        self.source = None
        self.sink = None

        self.op_id = 'render version 0.0'
        self.name = name
        self.params = render_parameters()

    # convert single-banded image to byte datatype for display
    def recast_band( self, image ):

        # check for constant values
        min = np.nanmin(image)         # get values to scale
        max = np.nanmax(image)         # ignoring nan

        if max == min : 
            scale = 0.0 	       # make blank image
            c = 0.0
        else:
            scale = 255.0/(max-min)    # stretch to 8-bit range
            c = -scale*min

        # supply our own resultant array of byte type
        height,width = image.shape
        b_image = np.empty( (height,width), dtype=np.uint8 )

        b_image = (image*scale + c).astype(np.uint8)
        return b_image

    def prep( self ):
        nbands = self.source.shape[2]    

        if nbands == 1:
            self.render_band( 0  )
            return
            
        if self.params.grey != None :
            if self.params.grey >= nbands :
                print( 'render: grey band outside range', file=sys.stderr )
                sys.exit( 1 )

            self.render_band( self.params.grey )
            return
    
        if nbands >= 3 :                  # merge if at least 3 bands
      
            # check if rgb bands ok
            if self.params.red >= nbands or \
               self.params.grn >= nbands or \
               self.params.blu >= nbands:
                print( 'render: color band outside range', file=sys.stderr )
                return
            self.render_merged( self.params.red, 
                                self.params.grn, 
                                self.params.blu )
            return

        print( 'render: unknown format', file=sys.stderr )
        sys.exit( 1 )

    def render_band( self, index ):
        
        if self.source.dtype == np.uint8:   # check if source data is byte
            image = self.source[:,:,index]  # use directly
        else:
            image = self.recast_band( self.source[:,:,index] ) # make byte

        if type( self.params.lut ) is not np.ndarray:
            for i in range(0,3):
                self.sink[:,:,i] = image    # copy grey values into RGB buffers
        else:
            self.sink = self.params.lut[image] # run through lut filter
            
    # merge three bands into a color display
    def render_merged( self, r, g, b ):
        
        # check if data type is byte
        if self.source.dtype == np.uint8:

            # use view directly
            self.sink[:,:,0] = self.source[:,:,r]
            self.sink[:,:,1] = self.source[:,:,g]
            self.sink[:,:,2] = self.source[:,:,b]
        else:
            self.sink[:,:,0] = self.recast_band( self.source[:,:,r] )
            self.sink[:,:,1] = self.recast_band( self.source[:,:,g] )
            self.sink[:,:,2] = self.recast_band( self.source[:,:,b] )
            
    def run( self ):
        
        height,width,nbands = self.source.shape
        self.sink = np.empty( (height,width,3), dtype=np.uint8 )

        self.prep()

        pil = Image.new('RGB', (width, height) )
        pil.frombytes( self.sink.tostring())
        pil.save( self.params.filepath )
        
    def readlut( self, filename ):
        
        lutfile = open( filename, 'r' )
        self.params.lut  = np.empty( (256,3), 
                                     dtype=np.uint8 ) # TODO:check lengths
        i = 0
        for line in lutfile:
            r,g,b = line.split(',')
            self.params.lut[i,0] = int(r.strip())
            self.params.lut[i,1] = int(g.strip())
            self.params.lut[i,2] = int(b.strip())
            i += 1

    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):  # scan panel parameters
        pass

    def write_params_to_panel( self ):   # write parameters to panel
        pass

    # initialize graphics
    def init_panel( self, benchtop ):
        op_panel.init_panel( self, benchtop ) # start with basics
        
    ############################################################
    # command line options
    ############################################################

    # TODO: put eprint in op_panel class
    def usage( self ):
        print( 'usage: render.py', file=sys.stderr )
        print( '       -h, --help', file=sys.stderr )
        print( '       -g band, --grey=band', file=sys.stderr )
        print( '       -c b1,b2,b3, --color=b1,b2,b3', file=sys.stderr )
        print( '       -f filepath, --file=filepath', file=sys.stderr )
        print( '       -l lutfile, --lut=lutfile', file=sys.stderr )
        print( '       -p paramfile, --params=paramfile', file=sys.stderr )
        print( '       param file overrides line arguments', file=sys.stderr )
        print( '       input is stdin', 'output is filename', file=sys.stderr )

    def set_params( self, argv ):
        params = None

        try:                                
            opts, args = getopt.getopt( argv, 'hg:c:f:l:', 
                                        ['help','grey=','color=','file=',
                                         'lut='])
        except getopt.GetoptError:           
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     

                sys.exit(0)   
            elif opt in ( '-l', '--lut' ):                
                self.readlut( arg )

            elif opt in ( '-g', '--grey' ):                
                self.params.grey = int(arg)
                if self.params.grey < 0:
                    print( 'render: band cannot be less than zero',
                           file=sys.stderr )
                    sys.exit(2)  

            elif opt in ( '-c', '--color' ):
                list = arg.split(',')
                self.params.red = int(list[0])
                self.params.grn = int(list[1])
                self.params.blu = int(list[2])
                if self.params.red < 0 or \
                   self.params.grn < 0 or \
                   self.params.blu < 0:
                    print( 'render: band cannot be less than zero',
                           file=sys.stderr )
                    sys.exit(2)  
                self.params.grey = None

            elif opt in ( '-f', '--file' ):
                oper.params.filepath = arg
            
            elif opt in ( '-p', '--params' ):
                params = arg  

        '''
        if self.params.filepath == '' and params == None :
          print( 'render:set_params: no filename given', file=sys.stderr )
          sys.exit( 2 )

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                print( 'render:set_params: bad params file read',
                       file=sys.stderr )
                sys.exit( 2 )
        '''
####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':
    import os
    import tempfile
    
    oper = instantiate()      
    oper.set_params( sys.argv[1:] )

    # numpy needs to 'seek' on the file to load
    # so read from stdin to temporary file first
    temp_name = next(tempfile._get_candidate_names()) + '.tmp'
    temp = open( temp_name, 'wb' )
    temp.write( sys.stdin.buffer.read() )
    temp.close()

    # load the pickled data
    oper.source = np.load( temp_name, allow_pickle=True,fix_imports=False)
    os.remove( temp_name )
    oper.run()                  
