#! /usr/bin/env /usr/bin/python3

'''
@file eto.py
@author Scott L. Williams
@package POLI
@brief Calculates standard evaporation (ETo).
@LICENSE
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

# calculate standard reference evapotranspiration
# and attach lat and long buffers

eto_copyright = 'eto.py Copyright (c) 2016-2024 Scott L. Williams ' + \
                 'released under GNU GPL V3.0'

import wx
import os
import sys
import math
import getopt

import numpy as np

from threads import apply_thread
from threads import monitor_thread
from op_panel import op_panel

# return an instance of 'preeto' class 
# without having to know its name
def instantiate():	
    return eto( get_name() )

def get_name(): 
    return 'eto'

class eto_parameters():
    def __init__( self ):
        pass

class eto( op_panel ):                 # calculate_eto operator

    def __init__( self, name ):        # initialize op_panel but no graphics
        self.op_id = 'eto version 0.0'
        self.params = eto_parameters()
        op_panel.__init__( self, name )

    # implement eq. 53 from FAO #56 hourly example
    def calc_et_ref( self,
                     Rn,      # net radiation, MJ/(m**2*hr) eq.40
                     G,       # soil flux,MJ/(m**2*hr) eq.45,46
                     Thc,     # mean hourly air temperature, C
                     D,       # saturation slope vapour pressure curve 
                              # at Th, kPa/C, eq. 13
                     g,       # psychrometric, kPa/C, eq.8
                     es,      # saturation vapor pressure at Th,kPa,eq.11
                     ea,      # average hourly actual vapor pressure, kPa, eq.54
                     w2 ):    # average hourly wind speed at 2m, m/s


        # calculate numerator from eq.53
        num_a = 0.408*D*(Rn-G)
        num_b = g*(37.0/(Thc+273.16))
        num_c = w2*(es-ea)

        num = num_a + num_b*num_c

        # calculate denominator from eq.53
        denom = D + g*(1 + 0.34*w2)

        return num/denom

    # end calc_et_ref

    def run( self ):                   # override superclass run

        # make some preliminary checks
        # TODO: implement graceful error exits

        # data type
        if self.source.dtype != np.float32:
            print >> sys.stderr, 'wrong data type, should be float32'
            return

        numy,numx,nbands = self.source.shape # get dimensions

        # input bands:
        # Rn     hourly averaged net radiation,            MJ/(m**2*hr)
        # G      hourly averaged ground heat flux,         MJ/(m**2*hr)
        # Thk    hourly averaged temperature,              C
        # D      saturation slope vapor pressure curve,    kPa/C
        # g      psychrometric from mean surface pressure, kPa/C
        # es,    saturation vapor pressure at Thc,         kPa
        # ea,    actual vapor pressure,                    kPa
        # w2,    wind speed,                               m/s

        if nbands != 8:  
            print( 'eto: wrong band size, should be 8, got:',
                   nbands, ' exiting...' )
            return

        # allocate output space; include lat and long
        self.sink = np.empty( (numy,numx,3), dtype=np.float32 )

        self.sink[:,:,0 ] = self.calc_et_ref( self.source[:,:,0],
                                              self.source[:,:,1],
                                              self.source[:,:,2],
                                              self.source[:,:,3],
                                              self.source[:,:,4],
                                              self.source[:,:,5],
                                              self.source[:,:,6],
                                              self.source[:,:,7] )

        self.band_tags = ['ETo mm/hr']

    ####################################################################
    # gui section
    ####################################################################
    def read_params_from_panel( self ):       # scan panel parameters
        pass

    def write_params_to_panel( self ):        # write parameters to panel
        pass

    # initialize graphics
    def init_panel( self, benchtop ):
        op_panel.init_panel( self, benchtop ) # start with basics


    ############################################################
    # command line options
    ############################################################

    # TODO: implement direct numpy file read
    
    def usage( self ):

        print('usage: eto.py', file=sys.stderr )
        print( '       -h, --help', file=sys.stderr )
        print( '       input is stdin, output is stdout', file=sys.stderr )

    def set_params( self, argv ):
    
        try:                                
            opts, args = getopt.getopt( argv,
                                        'h', 
                                        ['help'] )
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
    oper.set_params( sys.argv[1:] )

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
