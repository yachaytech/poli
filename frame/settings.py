'''
@file settings.py
@author Scott L. Williams.
@package POLI
@section LICENSE
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

@section DESCRIPTION
Invoke display settings for poli
'''

settings_copyright = 'settings.py Copyright (c) 2010-2022 Scott L. Williams, released under GNU GPL V3.0'

import wx
import numpy as np

# TODO: replace buttons with pull down menu of luts

class settings( wx.Panel ):         # panel for setting display options
    def __init__( self, parent, benchtop ):
        wx.Panel.__init__( self, parent )
        
        self.benchtop = benchtop
        self.init_panel()
        
    def init_panel( self ):
        v_box = wx.BoxSizer( wx.VERTICAL )
        h_box = wx.BoxSizer( wx.HORIZONTAL )

        p_stretch = self.make_stretch_panel()
        h_box.Add( p_stretch, 0, wx.EXPAND|wx.ALL, 1 )

        p_color = self.make_color_panel()
        h_box.Add( p_color, 1, wx.ALL, 1 )

        v_box.Add( h_box, 0, wx.EXPAND|wx.ALL, 1 )

        self.SetSizer( v_box )
        self.Enable( False )

    def make_stretch_panel( self ) :
        p_stretch = wx.Panel( self, -1 )

        static_box = wx.StaticBox( p_stretch, -1, 'stretch' )
        sizer = wx.StaticBoxSizer( static_box, orient=wx.VERTICAL )

        self.b_gauss = wx.Button( p_stretch, -1, 'gaussian' )
        sizer.Add( self.b_gauss, 0, wx.ALL, 1 )
        self.b_gauss.Enable( False )
        #self.b_gauss.Bind( wx.EVT_LEFT_UP, self.on_wedge )

        self.b_equal = wx.Button( p_stretch, -1, 'equalhist' )
        self.b_equal.Bind( wx.EVT_LEFT_UP, self.on_equal )
        sizer.Add( self.b_equal, 0, wx.ALL, 1 )

        p_stretch.SetSizer( sizer )
        return p_stretch

    def make_color_panel( self ): 
        p_color = wx.Panel( self, -1 )

        static_box =wx.StaticBox(p_color, -1, 'color')
        sizer = wx.StaticBoxSizer( static_box, orient=wx.VERTICAL)

        self.b_wedge = wx.Button( p_color, -1, 'wedge' )
        self.b_wedge.Bind( wx.EVT_LEFT_UP, self.on_wedge )              
        sizer.Add( self.b_wedge, 0, wx.ALL, 1 )

        self.b_rainbow = wx.Button( p_color, -1, 'rainbow' )
        self.b_rainbow.Bind( wx.EVT_LEFT_UP, self.on_rainbow )              
        sizer.Add( self.b_rainbow, 0, wx.ALL, 1 )

        self.b_spect = wx.Button( p_color, -1, 'spect' )
        self.b_spect.Bind( wx.EVT_LEFT_UP, self.on_spect )              
        sizer.Add( self.b_spect, 0, wx.ALL, 1 )

        self.b_inverse = wx.Button( p_color, -1, 'inverse' )
        self.b_inverse.Bind( wx.EVT_LEFT_UP, self.on_inverse )              
        sizer.Add( self.b_inverse, 0, wx.ALL, 1 )

        self.b_ndvi = wx.Button( p_color, -1, 'ndvi' )
        self.b_ndvi.Bind( wx.EVT_LEFT_UP, self.on_ndvi )              
        sizer.Add( self.b_ndvi, 0, wx.ALL, 1 )

        p_color.SetSizer( sizer )
        return p_color

    # tell current operator to re-display processed image
    # with different lut

    # equalize histogrm and implement as a lut transform
    def on_equal( self, event ):
        if len( self.benchtop.op ) == 0 :
            return

        index = self.benchtop.op_note.GetSelection()
        op = self.benchtop.op[ index ]

        # grab histogram and make a cumulative one
        hist = self.benchtop.pan_tools.hist.hist
        if hist.shape[0] != 1:   # work on single bands
            return

        # we exclude 0th bin (nan) as does hist
        chist = np.empty( 255, dtype=np.float32 ) 
        chist[0] = hist[0,0]
        for i in range(1,255):
            chist[i] = chist[i-1] + hist[0,i]
        
        cmin = chist[0]     # min value. TODO: search for non-zero?
        npix = chist[254]   # number of pixels excluding nan values

        lut = np.empty( (256,3), dtype=np.int8 )
        lut[0,:] = 0
        for i in range(1,256):
            lut[i,:] = int(((chist[i-1]-cmin)/(npix-cmin))*254)

        op.lut = lut
        op.show_image()
        event.Skip()

    def on_wedge( self, event ):
        if len( self.benchtop.op ) == 0 :
            return

        index = self.benchtop.op_note.GetSelection()
        op = self.benchtop.op[ index ]
        op.lut = None
        op.show_image()
        event.Skip()

    def on_rainbow( self, event ):
        if len( self.benchtop.op ) == 0 :
            return

        index = self.benchtop.op_note.GetSelection()
        op = self.benchtop.op[ index ]
        op.lut = self.make_halfbow()
        op.show_image()
        event.Skip()

    def on_spect( self, event ):
        if len( self.benchtop.op ) == 0 :
            return

        index = self.benchtop.op_note.GetSelection()
        op = self.benchtop.op[ index ]
        op.lut = self.make_spect()
        op.show_image()
        event.Skip()

    def on_ndvi( self, event ):
        if len( self.benchtop.op ) == 0 :
            return

        index = self.benchtop.op_note.GetSelection()
        op = self.benchtop.op[ index ]
        op.lut = self.make_ndvi1()
        op.show_image()
        event.Skip()

    def on_inverse( self, event ):
        if len( self.benchtop.op ) == 0 :
            return

        # get current lut and invert
        index = self.benchtop.op_note.GetSelection()
        op = self.benchtop.op[ index ]
        
        #if op.lut == None:
        if type( op.lut ) is not np.ndarray:
            op.lut = self.make_ramp()
            
        op.lut = np.invert( op.lut )
        op.show_image()
        event.Skip()

    def make_ramp( self ):

        # TODO: find better way w/range....
        ramp = np.empty( (256,3), dtype=np.uint8 )
        lut = np.arange( 0,256 )
        for i in range(0,3):
            ramp[:,i] = lut

        return ramp

    # ramped spectrum
    def make_spect( self ):

        lut  = np.empty( (256,3), dtype=np.uint8 )

        '''
   	// load red map
	for ( int i=0; i<128; i++ ) red[i] = (byte)128;
	for ( int i=0; i<128; i++ ) red[i+128] = (byte)(128-i);
  
	// load green map 
	for ( int i=0; i<64; i++ )  green[i] = (byte)(i*2);
	for ( int i=0; i<128; i++ ) green[i+64] = (byte)128;
	for ( int i=0; i<64; i++ )  green[i+192] = (byte)(128-i*2);

	// load blue map 
	for ( int i=0; i<192; i++ ) blue[i] = (byte)(i*(128.0/192.0)+0.5);
	for ( int i=0; i<64; i++ )  blue[i+192] = (byte)128;
        '''

        for i in range(0,128):   # load red map
            lut[i,0] = 255
        for i in range(0,128):
            lut[i+128,0] = 255-i*2

        for i in range(0,64):     # load green map 
            lut[i,1] = i*4
        for i in range(0,128):
            lut[i+64,1] = 255
        for i in range(0,64):
            lut[i+192,1] = 255-i*4
  
        for i in range(0,128):   # load blue map
            lut[i,2] = i*2
        for i in range(0,128): 
            lut[i+128,2] = 255
  
        return lut
        
    def make_rainbow( self ):
        rb = np.empty( (256,3), dtype=np.int8 )
        rb[:,0] = np.array( [  0,255,255,255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,255,255,255, 
                             255,255,255,255,255,255,255,255,255,255,252,
                             248,244,240,235,231,227,222,218,213,209,204,
                             199,195,190,185,180,175,170,165,160,155,150,
                             145,139,134,128,123,117,111,105, 99, 92, 86,  
                              79, 72, 64, 57, 48, 39, 30, 18,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,   
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,   
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,   
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,   
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,   
                               0,  0,  0,  0,  0,  0, 18, 30, 39, 48, 57,  
                              64, 72, 79, 86, 92, 99,105,111,117,123,128, 
                             134,139,145,150,155,160,165,170,175,180,185,
                             190,195,199,204,209,213,218,222,227,231,235, 
                             240,244,248,252,255,255,255,255,255,255,255, 
                             255,255,255,255,255,255,255,255,255,255,255, 
                             255,255,255,255,255,255,255,255,255,255,255, 
                             255,255,255,255,255,255,255,255,255,255,255, 
                             255,255,255 ] )
                          
        rb[:,1] = np.array( [  0, 18, 30, 39, 48, 57, 64, 72, 79, 86, 92, 
                              99,105,111,117,123,128,134,139,145,150,155,
                             160,165,170,175,180,185,190,195,199,204,209,
                             213,218,222,227,231,235,240,244,248,252,255, 
                             255,255,255,255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,252,248,244,240,
                             235,231,227,222,218,213,209,204,199,195,190,
                             185,180,175,170,165,160,155,150,145,139,134,
                             128,123,117,111,105, 99, 92, 86, 79, 72, 64,
                              57, 48, 39, 30, 18,  0,  0,  0,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                               0,  0,255 ] )

                            
        rb[:,2 ]= np.array( [  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  0, 18, 30,
                              39, 48, 57, 64, 72, 79, 86, 92, 99,105,111,
                             117,123,128,134,139,145,150,155,160,165,170,
                             175,180,185,190,195,199,204,209,213,218,222,
                             227,231,235,240,244,248,252,255,255,255,255,
                             255,255,255,255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,255,255,255,
                             255,255,255,255,252,248,244,240,235,231,227,
                             222,218,213,209,204,199,195,190,185,180,175,
                             170,165,160,155,150,145,139,134,128,123,117,
                             111,105, 99, 92, 86, 79, 72, 64, 57, 48, 39,  
                              30, 18,255 ] )
        return rb

    def make_halfbow( self ):
        rb = np.empty( (256,3), dtype=np.int8 )
                          
        rb[:,0] = np.array( [    0,255,255,255,255,255,255,255,
                               255,255,255,255,255,255,255,255,
                               255,255,255,255,255,255,248,240,
                               231,222,213,204,195,185,175,165,
                               155,145,134,123,111, 99, 86, 72, 
                                57, 39, 18,  0,  0,  0,  0,  0,  
                                 0,  0,  0,  0,  0,  0,  0,  0,  
                                 0,  0,  0,  0,  0,  0,  0,  0,  
                                 0,  0,  0,  0,  0,  0,  0,  0,  
                                 0,  0,  0,  0,  0,  0,  0,  0,  
                                 0,  0,  0,  0,  0,  0, 30, 48,  
                                64, 79, 92,105,117,128,139,150,
                               160,170,180,190,199,209,218,227,
                               235,244,252,255,255,255,255,255,
                               255,255,255,255,255,255,255,255,
                               255,255,255,255,255,255,255,255,
                                 0,255,255,255,255,255,255,255,
                               255,255,255,255,255,255,255,255,
                               255,255,255,255,255,255,248,240,
                               231,222,213,204,195,185,175,165,
                               155,145,134,123,111, 99, 86, 72, 
                                57, 39, 18,  0,  0,  0,  0,  0,  
                                 0,  0,  0,  0,  0,  0,  0,  0,  
                                 0,  0,  0,  0,  0,  0,  0,  0,  
                                 0,  0,  0,  0,  0,  0,  0,  0,  
                                 0,  0,  0,  0,  0,  0,  0,  0,  
                                 0,  0,  0,  0,  0,  0, 30, 48,  
                                64, 79, 92,105,117,128,139,150,
                               160,170,180,190,199,209,218,227,
                               235,244,252,255,255,255,255,255,
                               255,255,255,255,255,255,255,255,
                               255,255,255,255,255,255,255,255 ] )

        rb[:,1] = np.array( [  0, 30, 48, 64, 79, 92,105,117,
                             128,139,150,160,170,180,190,199,
                             209,218,227,235,244,252,255,255,
                             255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,
                             252,244,235,227,218,209,199,190,
                             180,170,160,150,139,128,117,105, 
                              92, 79, 64, 48, 30,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  
                               0,  0,  0,  0,  0,  0,  0,  0,  
                               0,  0,  0,  0,  0,  0,  0,  0,  
                               0,  0,  0,  0,  0,  0,  0,  0,  
                               0,  0,  0,  0,  0,  0,  0,  0,
                               0, 30, 48, 64, 79, 92,105,117,
                             128,139,150,160,170,180,190,199,
                             209,218,227,235,244,252,255,255,
                             255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,
                             252,244,235,227,218,209,199,190,
                             180,170,160,150,139,128,117,105, 
                              92, 79, 64, 48, 30,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  
                               0,  0,  0,  0,  0,  0,  0,  0,  
                               0,  0,  0,  0,  0,  0,  0,  0,  
                               0,  0,  0,  0,  0,  0,  0,  0,  
                               0,  0,  0,  0,  0,  0,  0,  0 ] )

                            
        rb[:,2] = np.array( [  0,  0,  0,  0,  0,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  
                               0,  0,  0,  0,  0,  0,  0,  0,  
                               0,  0,  0,  0,  0,  0,  0,  0, 
                               0,  0,  0,  0,  0,  0,  0,  0,  
                               0,  0,  0, 18, 39, 57, 72, 92, 
                              99,111,123,134,145,155,165,180,
                             185,195,204,213,222,231,240,252,
                             255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,
                             255,255,255,248,240,231,222,209,
                             204,195,185,175,165,155,145,128,
                             123,111, 99, 86, 72, 57, 39,255,
                               0,  0,  0,  0,  0,  0,  0,  0,
                               0,  0,  0,  0,  0,  0,  0,  0,  
                               0,  0,  0,  0,  0,  0,  0,  0,  
                               0,  0,  0,  0,  0,  0,  0,  0, 
                               0,  0,  0,  0,  0,  0,  0,  0,  
                               0,  0,  0, 18, 39, 57, 72, 92, 
                              99,111,123,134,145,155,165,180,
                             185,195,204,213,222,231,240,252,
                             255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,
                             255,255,255,255,255,255,255,255,
                             255,255,255,248,240,231,222,209,
                             204,195,185,175,165,155,145,128,
                             123,111, 99, 86, 72, 57, 39,255 ] )
        return rb

    def make_ndvi0( self ):
        rb = np.empty( (256,3), dtype=np.int8 )

        rb[:,0] = np.array( [ 235,235,235,235,235,235,235,235,
                              235,235,235,235,235,235,235,235,
                              202,203,204,206,207,209,210,211,
                              213,214,215,217,218,219,221,222,
                              223,224,226,227,228,229,230,231,
                              233,234,235,236,237,238,239,240,
                              241,242,242,243,244,245,246,246,
                              247,248,248,249,250,250,251,251,
                              252,252,253,253,253,254,254,254,
                              255,255,255,126,126,126,126,126,
                              126,126,126,126,126,126,126,126,
                              126,126,150,150,150,150,150,150,
                              150,150,150,150,150,150,150,150,
                              150,117,117,117,117,117,117,117,
                              117,117,117,117,117,117,117,117,
                              103,103,103,103,103,103,103,103,
                              103,103,103,103,103,103,103, 82,
                               82, 82, 82, 82, 82, 82, 82, 82,
                               82, 82, 82, 82, 82, 82, 61, 61,
                               61, 61, 61, 61, 61, 61, 61, 61,
                               61, 61, 61, 61, 61, 28, 28, 28,
                               28, 28, 28, 28, 28, 28, 28, 28, 
                               28, 28, 28, 28,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0, 
                                0,  0,  0,  0,  0,  0,  0,  0, 
                                0,  0,  0,  0,  0,  0,  0,  0, 
                                0,  0,  2,  2,  2,  2,  2,  2, 
                                2,  2,  2,  2,  2,  2,  2,  2, 
                                2,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0, 
                                1,  1,  1,  1,  1,  1,  1,  1, 
                                1,  1,  1,  1,  1,  1,235,  0 ] )

        rb[:,1] = np.array( [ 235,235,235,235,235,235,235,235,
                              235,235,235,235,235,235,235,235,
                              108,110,113,115,118,120,123,125,
                              128,130,133,135,137,140,142,144,
                              147,149,151,154,156,158,160,162,
                              165,167,169,171,173,175,177,179,
                              181,183,185,187,189,191,192,194,
                              196,198,199,201,203,204,206,208,
                              209,210,212,213,215,216,217,219,
                              220,221,222,156,156,156,156,156,
                              156,156,156,156,156,156,156,156,
                              156,156,182,182,182,182,182,182,
                              182,182,182,182,182,182,182,182,
                              182,170,170,170,170,170,170,170,
                              170,170,170,170,170,170,170,170,
                              161,161,161,161,161,161,161,161,
                              161,161,161,161,161,161,161,148,
                              148,148,148,148,148,148,148,148,
                              148,148,148,148,148,148,134,134,
                              134,134,134,134,134,134,134,134,
                              134,134,134,134,134,115,115,115,
                              115,115,115,115,115,115,115,115,
                              115,115,115,115, 95, 95, 95, 95,
                              95, 95, 95, 95, 95, 95, 95, 95,
                              95, 95, 95, 72, 72, 72, 72, 72,
                              72, 72, 72, 72, 72, 72, 72, 72,
                              72, 72, 55, 55, 55, 55, 55, 55,
                              55, 55, 55, 55, 55, 55, 55, 55,
                              55, 41, 41, 41, 41, 41, 41, 41,
                              41, 41, 41, 41, 41, 41, 41, 41,
                              19, 19, 19, 19, 19, 19, 19, 19,
                              19, 19, 19, 19, 19, 19,235,  0 ] )

        rb[:,2] = np.array( [ 235,235,235,235,235,235,235,235,
                              235,235,235,235,235,235,235,235,
                              32, 34, 36, 38, 39, 41, 43, 45,
                              47, 49, 50, 52, 54, 56, 58, 59,
                              61, 63, 64, 66, 67, 69, 71, 72,
                              74, 75, 76, 78, 79, 81, 82, 83,
                              85, 86, 87, 88, 89, 90, 91, 92,
                              93, 94, 95, 96, 97, 98, 99, 99,
                              100,101,101,102,102,103,103,103,
                              104,104,104, 44, 44, 44, 44, 44,
                              44, 44, 44, 44, 44, 44, 44, 44,
                              44, 44, 19, 19, 19, 19, 19, 19,
                              19, 19, 19, 19, 19, 19, 19, 19,
                              19,  0,  0,  0,  0,  0,  0,  0,
                              0,  0,  0,  0,  0,  0,  0,  0,
                              0,  0,  0,  0,  0,  0,  0,  0,
                              0,  0,  0,  0,  0,  0,  0,  0,
                              0,  0,  0,  0,  0,  0,  0,  0,
                              0,  0,  0,  0,  0,  0,  1,  1,
                              1,  1,  1,  1,  1,  1,  1,  1,
                              1,  1,  1,  1,  1,  1,  1,  1,
                              1,  1,  1,  1,  1,  1,  1,  1,
                              1,  1,  1,  1,  1,  1,  1,  1,
                              1,  1,  1,  1,  1,  1,  1,  1,
                              1,  1,  1,  0,  0,  0,  0,  0,
                              0,  0,  0,  0,  0,  0,  0,  0,
                              0,  0,  1,  1,  1,  1,  1,  1,
                              1,  1,  1,  1,  1,  1,  1,  1,
                              1,  1,  1,  1,  1,  1,  1,  1,
                              1,  1,  1,  1,  1,  1,  1,  1,
                              1,  1,  1,  1,  1,  1,  1,  1,
                              1,  1,  1,  1,  1,  1,235,  0 ] )

        return rb

    def make_ndvi1( self ):
        rb = np.empty( (256,3), dtype=np.int8 )
        rb[:,0] = np.array( [ 235,235,235,235,235,235,235,235, 
                              235,235,235,235,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                               16, 32, 48, 64, 80, 96,128,144,
                              160,202,204,207,210,213,215,218,
                              221,223,226,228,230,233,235,237,
                              239,126,126,126,126,126,126,126,
                              126,126,126,126,126,126,126,126,
                              150,150,150,150,150,150,150,150,
                              150,150,150,150,150,150,150,117,
                              117,117,117,117,117,117,117,117,
                              117,117,117,117,117,117,103,103,
                              103,103,103,103,103,103,103,103,
                              103,103,103,103,103, 82, 82, 82,
                               82, 82, 82, 82, 82, 82, 82, 82,
                               82, 82, 82, 82, 61, 61, 61, 61,
                               61, 61, 61, 61, 61, 61, 61, 61,
                               61, 61, 61, 61, 50, 50, 50, 50,
                               50, 50, 50, 50, 50, 50, 50,  0 ] )
                             
        rb[:,1] = np.array( [ 235,235,235,235,235,235,235,235,
                              235,235,235,235,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,108,113,118,123,128,133,137,
                              142,147,151,156,160,165,169,173,
                              177,156,156,156,156,156,156,156,
                              156,156,156,156,156,156,156,156,
                              182,182,182,182,182,182,182,182,
                              182,182,182,182,182,182,182,170,
                              170,170,170,170,170,170,170,170,
                              170,170,170,170,170,170,161,161,
                              161,161,161,161,161,161,161,161,
                              161,161,161,161,161,148,148,148,
                              148,148,148,148,148,148,148,148,
                              148,148,148,148,134,134,134,134,
                              134,134,134,134,134,134,134,134,
                              134,134,134,134,150,150,150,150,
                              150,150,150,150,150,150,150,  0 ] )

        rb[:,2] = np.array( [ 235,235,235,235,235,235,235,235,
                              235,235,235,235, 13, 14, 15, 16,
                               17, 18, 19, 20, 21, 22, 23, 24,
                               25, 26, 27, 28, 29, 30, 31, 32,
                               33, 34, 35, 36, 37, 38, 39, 40,
                               41, 42, 43, 44, 45, 46, 47, 48,
                               49, 50, 51, 52, 53, 54, 55, 56,
                               57, 58, 59, 60, 61, 62, 63, 64,
                               65, 66, 67, 68, 69, 70, 71, 72,
                               73, 74, 75, 76, 77, 78, 79, 80,
                               81, 82, 83, 84, 85, 86, 87, 88,
                               89, 90, 91, 92, 93, 94, 95, 96,
                               97, 98, 99,100,101,102,103,104,
                              105,106,107,108,109,110,111,112,
                              113,114,115,116,117,118,119,120,
                              121,122,123,124,125,126,127,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0, 32, 36, 39, 43, 47, 50, 54,
                               58, 61, 64, 67, 71, 74, 76, 79,
                               82, 44, 44, 44, 44, 44, 44, 44,
                               44, 44, 44, 44, 44, 44, 44, 44,
                               19, 19, 19, 19, 19, 19, 19, 19,
                               19, 19, 19, 19, 19, 19, 19,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  0,  0,  0,  0,
                                0,  0,  0,  0,  1,  1,  1,  1,
                                1,  1,  1,  1,  1,  1,  1,  1,
                                1,  1,  1,  1,  2,  2,  2,  2,
                                2,  2,  2,  2,  2,  2,  2,  0 ] )
        return rb
