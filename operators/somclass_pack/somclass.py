#! /usr/bin/env /usr/bin/python3

'''
@file somclass.py
@author Scott L. Williams
@package POLI
@brief Read SOM weights and classify data.
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

# read som weights and classify data

somclass_copyright = 'somclass.py Copyright (c) 2010-2024 Scott L. Williams, released under GNU GPL V3.0'

import wx
import sys
import getopt
import numpy as np

from op_panel import op_panel

# return an instance of 'somclass' class 
# without having to know its name
def instantiate():	
    return somclass( get_name() )

def get_name(): 
    return 'somclass'

class somclass_parameters():              # hold arguments values here
    def __init__( self ):
        self.weightfile = 'som_weights.label'
        self.nclasses = 16
        
class somclass( op_panel ):
    def __init__( self, name ):      # initialize op_panel but no graphics
        op_panel.__init__( self, name )
        self.op_id = 'somclass version 0.0'
        self.params = somclass_parameters()

    # match image sample to closest map weights
    def classify( self, neurons, image ):
        num_neurons,nnbands = neurons.shape
        height,width,nbands = image.shape

        if nnbands != nbands:
            print('somclass: dimensions do not match',
                  nnbands, nbands, file=sys.stderr )
            return None

        # set up arrays
        min = np.empty( (height,width,1), dtype=np.float32 )
        new = np.empty( (height,width,1), dtype=np.float32 )

        # initialize to the zeroth neuron
        classified = np.zeros( (height,width,1), dtype=np.uint8 )

        diff = image-neurons[0]        # initialize min array
        diff = np.abs( diff )          # using no-square euclid metric
        min = np.sum( diff, axis=2 )   # TODO: determine metric and use

        for i in range( 1,num_neurons ):    # test each neuron.
            diff = image-neurons[i]         # keep track of minimal distances
            diff = np.abs( diff )           # and compare/adjust with each 
            new = np.sum( diff, axis=2 )    # new distance array

            mask = min > new

            np.putmask( min, mask, new )      # use same mask to
            np.putmask( classified, mask, i ) # keep track of class

        return classified

    def run( self ):                        # override superclass run      
        try:                                # read neuron weights

            # get number of classes to read
            nclasses = self.params.nclasses
            wfile = open( self.params.weightfile, 'r' ) 

            # print header and look for flag
            found = False
            for line in wfile:
                if line.find( 'NEURONS' ) != -1:
                    found = True
                    break
                print( line.strip(), file=sys.stderr )
                
            if not found:
                print( 'somclass:run:could not find flag', file=sys.stderr )
                return
                
            nneurons,ndim = wfile.readline().split()
            nneurons = int( nneurons )
            ndim = int( ndim )

            # see if user request for nclasses works
            if nclasses <= 0:
                nclasses = nneurons # read all classes
                warn = '\tsomclass: reading all classes, nclasses= : ' + str(nneurons) + '\n'
            else:
                if nclasses > nneurons:
                    warn = '\tsomclass: nclasses given is greater than available classes.\n\tsomclass: using all available classes. \n\tnclasses= ' + str(nneurons) + '\n'
                    print( warn, file=sys.stderr )
                    nclasses = nneurons
                else:
                    warn = '\tsomclass: using ' + str(nclasses) + ' classes' + '\n'

            print( warn, file=sys.stderr )
            
            # get the neuron weights
            neurons = np.empty( (nclasses,ndim), dtype=np.float32 )

            # retrieve neurons from file
            for i in range( nclasses ):            
                line = wfile.readline().split()    # get line components:
                                                   # label weight[0], weight[1],..., number of pixels
                for j in range( 1, ndim+1 ):       # skip grey level label
                    neurons[i,j-1] = float( line[j] )
            
            wfile.close()

        except IOError:
            self.messages.append( '\tsomclass:run: IOError\n' )
            return

        self.sink = self.classify( neurons, self.source )

        # rebranding band here is more convenient than 
        # overriding apply_work()
        self.band_tags = []
        self.band_tags.append( 'som map' )

    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):  # scan panel parameters
        self.params.weightfile = self.t_weightfile.GetValue()
        self.params.nclasses = int( self.t_nclasses.GetValue() )

    def write_params_to_panel( self ):   # write parameters to panel
        self.t_weightfile.SetValue( self.params.weightfile )
        self.t_nclasses.SetValue( str( self.params.nclasses ) )

    # initialize graphics
    def init_panel( self, benchtop ):
        op_panel.init_panel( self, benchtop ) # start with basics
        
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        v_sizer.Add( (1,30) ) # go down a bit on panel
        
        l_prompt = wx.StaticText( self.p_client, -1,
                                  ' enter number of classes to use (0 for all): ' )
        h_sizer.Add( l_prompt, 0, wx.TOP, 5 )

        self.t_nclasses = wx.TextCtrl( self.p_client, -1, '',
                                       size=(35,25), style=wx.ALIGN_RIGHT )
        self.t_nclasses.SetToolTip( 'Weight file lists classes in descending order of frequency. For example, if you enter 5, then the 5 most frequent classes will be read and used.' )

        h_sizer.Add( self.t_nclasses, 0, wx.TOP )
        v_sizer.Add( h_sizer )
        v_sizer.Add( (1,66) )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( self.p_client, -1, 'enter weight filename:' )
        h_sizer.Add( prompt, 0, wx.TOP, 5 )

        self.t_weightfile = wx.TextCtrl( self.p_client, -1 ) 
        self.t_weightfile.SetToolTip( ' enter filename to read weights from' )
        h_sizer.Add( self.t_weightfile, 1, wx.EXPAND )

        v_sizer.Add( h_sizer, 1, wx.EXPAND )
        self.p_client.SetSizer( v_sizer )
        self.write_params_to_panel()

    ############################################################
    # command line options
    ############################################################

    # TODO: sync up w real parms
    def usage( self ):
        print( 'usage: somclass.py', file=sys.stderr )
        print( '       -h, --help', file=sys.stderr )
        print( '       -f weights, --file=weights', file=sys.stderr )
        print( '       -n num_weights_to_use, --num=num_weights_to_use',
               file=sys.stderr )
        print( '       -p param_file, --params=param_file', file=sys.stderr )
        print( '       input is stdin, output is stdout', file=sys.stderr )

    def set_params( self, argv ):
        params = None

        try:                                
            opts, args = getopt.getopt( argv, 
                                        'hp:f:n:', 
                                        ['help','param=','file=','nclasses='] )
        except getopt.GetoptError:           
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit(0) 
            elif opt in ( '-f', '--file' ):
                self.params.weightfile = arg
            elif opt in ( '-n', '--nclasses' ):
                self.params.nclasses = int(arg)
            elif opt in ('-p', '--params'):
                params = arg  

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                print( "somclass.py: cannot read parameter file", file=sys.stderr)
                sys.exit(2)

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':
    import os
    import tempfile

    oper = instantiate()   
    oper.set_params( sys.argv[1:] )

    # numpy needs to seek on the file to load
    # so read from stdin to temporary file first
    temp_name = next(tempfile._get_candidate_names()) + '.tmp'
    temp = open( temp_name, 'wb' )
    temp.write( sys.stdin.buffer.read() )
    temp.close()

    # load the pickled data
    oper.source = np.load( temp_name, allow_pickle=False )
    os.remove( temp_name )
    oper.run()

    # send downstream
    np.save( sys.stdout.buffer, oper.sink, allow_pickle=False ) 
