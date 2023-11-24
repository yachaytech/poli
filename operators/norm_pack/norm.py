#! /usr/bin/env /usr/bin/python3
'''
@file norm.py
@author Scott L. Williams
@package POLI
@brief Normalize all bands to either -1 to 1 or 0 to 1.
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
# Normalize all bands to either -1 to 1 or 0 to 1.
# Optionally report scaling coefficients to file 
# Optionally consider interlaced buffers for scaling

norm_copyright = 'norm.py Copyright (c) 2010-2024 Scott L. Williams, released under GNU GPL V3.0'

import wx
import sys
import getopt
import numpy as np

from op_panel import op_panel

# return an instance of 'norm' class 
# without having to know its name
def instantiate():	
    return norm( get_name() )

def get_name(): 
    return 'norm'

class norm_parameters():              # hold arguments values here
    def __init__( self ):
        self.ntype = 0                # 0 for 0 to 1; -1 for -1 to 1
        self.write = False
        self.filepath = 'ncoeffs.txt' # coefficient output file
        self.skip = 0                 # interlace skip factor

class norm( op_panel ):
    def __init__( self, name ):       # initialize op_panel but no graphics
        op_panel.__init__( self, name )

        self.cfile = None
        self.op_id = 'norm version 0.0'
        self.params = norm_parameters()

    def calc_coefficients( self, image, floor, ceiling ):

        # workaround for bug in nanmin wrt unsigned ints
        if image.dtype == np.uint8  \
        or image.dtype == np.uint16 \
        or image.dtype == np.uint32:
            min = np.min( image )
            max = np.max( image )
        else:
            min = np.nanmin( image )         # get values to scale by
            max = np.nanmax( image )         # ignoring nan

        if max == min :                # check for constant values
            scale = 0.0 	       # make image a surface plane
            c = 0.0

        elif np.isinf( min ) or np.isinf( max ):
            scale = 0.0 	       # make image a surface plane
            c = 0.0

        else:
            scale = (ceiling-floor)/float((max-min)) 
            c = floor-scale*min

        return scale,c
    
    # convert single band value range from floor to ceiling
    def scale_band( self, band, image, floor, ceiling ):

        scale, c = self.calc_coefficients( image, floor, ceiling )
        
        # write out coeffs if asked to
        if ( self.cfile != None ):
            self.cfile.write( '%d,'%band + '%f,'%scale + '%f\n'%c )
        
        return image*scale + c

    # scale each band independently
    def no_interlace_scale( self ):

        nbands = self.source.shape[2]
        for i in range( nbands ):
            self.sink[:,:,i] = self.scale_band( i, self.source[:,:,i],
                                                self.params.ntype, 1.0 )
    # scale interlaced bands together
    def interlace_scale( self ):

        nbands = self.source.shape[2]
        skip = self.params.skip

        # check if skip factor divides evenly into number of buffers
        remainder = nbands%skip
        if remainder != 0:
            print( 'norm: skip factor does not evenly divide into number of bands', file=sys.stderr )
            return

        # create appended buffers based on skips
        cnum = int(nbands/skip)       # num of buffers to combine
        
        for i in range( skip ):  # skip = number of appended buffers 

            tmp = self.source[:,:,i] # initialize first buffer

            # append remaining buffers
            for j in range( 1, cnum ):
                tmp = np.append( tmp, self.source[:,:,i+(skip*j)] )
         
            scale, c = self.calc_coefficients( tmp, self.params.ntype, 1.0 )
            
            # scale the interlaced buffers
            for j in range( 0, cnum ):
                index = i + (skip*j)
                self.sink[:,:, index] = self.source[:,:,index]*scale + c

                # write out coeffs if asked to
                if ( self.cfile != None ):
                    self.cfile.write( '%d,'%index + '%f,'%scale + '%f\n'%c )

        
    def run( self ):                 # override superclass 

        # create the output buffer to populate with scaled values
        height,width,nbands = self.source.shape
        self.sink = np.empty( (height,width,nbands), dtype=np.float32 )

        # write out band coeffs? open file and set header
        if self.params.write:
            self.cfile = open( self.params.filepath, 'w' )

            # report number of bands
            self.cfile.write( '%d,'%nbands+'%d\n'%self.params.ntype ) 

        if self.params.skip == 0:
            self.no_interlace_scale()
        else:
            self.interlace_scale()
            
        if self.cfile != None:
            self.cfile.close()
            
    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):     # scan panel parameters

        # normalization type
        if self.r_positive.GetValue():
            self.params.ntype = 0
        else:
            self.params.ntype = -1

        # write enable
        if self.c_write.GetValue():
            self.params.write = True
        else:
            self.params.write = False

        # set filename to use
        self.params.filepath = self.t_filepath.GetValue()

        # get interlace skip factor
        self.params.skip = int( self.t_skip.GetValue() )
        
    def write_params_to_panel( self ):       # write parameters to panel
        
        # normalization type
        if self.params.ntype == 0:
            self.r_positive.SetValue( True )
        else:
            self.r_negative.SetValue( True )

        # write enable
        if self.params.write:
            self.c_write.SetValue( True )
            self.t_filepath.Enable( True )
            self.fprompt.Enable( True )
        else:
            self.c_write.SetValue( False )
            self.t_filepath.Enable( False ) 
            self.fprompt.Enable( False )

        # write filepath
        self.t_filepath.SetValue( self.params.filepath )

        # set interlace skip factor
        self.t_skip.SetValue( str( self.params.skip ) )
             
    # initialize graphics
    def init_panel( self, benchtop ):
        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        
        panel = self.type_panel()
        h_sizer.Add( panel, 0, wx.ALL, 1 )

        panel = self.skip_panel()
        h_sizer.Add( panel, 0, wx.ALL, 1 )

        v_sizer.Add( h_sizer, 1, wx.EXPAND )

        panel = self.write_panel()
        h_sizer.Add( panel, 0, wx.ALL, 1 )

        v_sizer.Add( panel, 1, wx.EXPAND )

        self.p_client.SetSizer( v_sizer )
        self.write_params_to_panel()

    def type_panel( self ):
        p_type = wx.Panel( self.p_client, -1, style=wx.SUNKEN_BORDER )

        sizer = wx.GridSizer( 3, 2, 1, 1 )
        prompt = wx.StaticText( p_type, -1, 'normalization type:' )
        sizer.Add( prompt )
        sizer.Add( (1,1) )

        self.r_positive = wx.RadioButton( p_type, -1, '0 to 1', 
                                          style = wx.RB_GROUP )
        sizer.Add( self.r_positive )
        
        self.r_negative = wx.RadioButton( p_type, -1, '-1 to 1' )
        sizer.Add( self.r_negative )

        p_type.SetSizer( sizer )
        
        return p_type
    
    def skip_panel( self ):
        p_skip = wx.Panel( self.p_client, -1, style=wx.SUNKEN_BORDER )

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        
        prompt = wx.StaticText( p_skip, -1, 'interlace buffer skip factor:' )
        v_sizer.Add( prompt )
        v_sizer.Add( (0,10) )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        
        prompt = wx.StaticText( p_skip, -1, 'skip:' )
        h_sizer.Add( prompt )
        h_sizer.Add( (10,0) )

        self.t_skip = wx.TextCtrl( p_skip, -1, '' )
        h_sizer.Add( self.t_skip )

        v_sizer.Add( h_sizer )
        
        p_skip.SetSizer( v_sizer )
        
        return p_skip

    def write_panel( self ):
        p_write = wx.Panel( self.p_client, -1, style=wx.SUNKEN_BORDER )

        #sizer = wx.GridSizer( 2, 3, 1, 1 )
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        prompt = wx.StaticText( p_write, -1, 'write normalization coefficients to file:' )
        v_sizer.Add( prompt )
        v_sizer.Add( (10,20) )
        #v_sizer.Add( (1,1) )
        #v_sizer.Add( (1,1) )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        #self.c_write = wx.CheckBox( p_write, -1, 'coeffs to file', (190,3) )
        self.c_write = wx.CheckBox( p_write, -1, 'coeffs to file')
        self.c_write.Bind( wx.EVT_CHECKBOX, self.on_write )             
        self.c_write.SetToolTip( 'enable writing coefficients to file' )

        h_sizer.Add( self.c_write )
        h_sizer.Add( (50,1) )

        # file input text control
        self.fprompt = wx.StaticText( p_write, -1, 'enter filepath:' )
        h_sizer.Add( self.fprompt )
        
        self.t_filepath = wx.TextCtrl( p_write, -1, '', size=(500,30) )
        self.t_filepath.SetToolTip( 'enter filepath for norm coefficients' )
        h_sizer.Add( self.t_filepath )
        v_sizer.Add( h_sizer )
        
        p_write.SetSizer( v_sizer )
        
        return p_write

    def on_write( self, event ):        # respond to write checkbox
        if self.c_write.GetValue():
            
            # enable file text box
            self.t_filepath.Enable( True )
            self.fprompt.Enable( True )
        else:
            
            # disable file text box
            self.t_filepath.Enable( False )
            self.fprompt.Enable( False )
            
    ############################################################
    # command line options for batch implementation
    ############################################################

    def usage( self ):
        print( 'usage: norm.py', file=sys.stderr )
        print( '       -h, --help', file=sys.stderr )
        print( '       -f coeff_file --file=coeff_file', file=sys.stderr )
        print( '       -t [0,-1], --type=[0,-1]',file=sys.stderr )
        print( '       -s skip_factor, --skip=skip_factor', file=sys.stderr )
        print( '       -p param_file, --params=param_file', file=sys.stderr )
        print( '       input is stdin, output is stdout', file=sys.stderr )

    def set_params( self, argv ):
        params = None
        
        try:                                
            opts, args = getopt.getopt( argv, 'hf:t:p:',
                                        ['help','file=','type=','param='] )
            
        except getopt.GetoptError:           
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit(0)
            elif opt in ( '-f', '--file' ):
                self.params.filepath = arg
                self.params.write = True
            elif opt in ( '-t', '--type' ):
                self.params.ntype = int(arg)
            elif opt in ( '-s', '--skip' ):
                self.params.skip = int(arg)
            elif opt in ('-p', '--params'):
                params = arg  

        # over rides other parameters
        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                print( "norm.py: cannot read parameter file", file=sys.stderr)
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

    # load the data
    oper.source = np.load( temp_name )
    os.remove( temp_name )
    oper.run()

    # send downstream 
    np.save( sys.stdout.buffer, oper.sink, allow_pickle=False ) 
