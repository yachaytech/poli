'''
@file histogram.py
@author Scott L. Williams
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
Render data histogram values on screen
'''

histogram_copyright = 'histogram.py Copyright (c) 2010-2022 Scott L. Williams, released under GNU GPL V3.0'

import wx
import numpy as np

# container panel for histogram rendering of display image
class histogram( wx.Panel ):
    def __init__( self, parent ):
        wx.Panel.__init__( self, parent )

    def set_histogram( self, hist ): # hist => 2d array [band,distribution]

        #if hist == None:
        if type(hist) is not np.ndarray:
            return

        self.DestroyChildren()

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        
        nbands = hist.shape[0]
        for i in range(0,nbands):
            panel = hist_panel( self, hist[i] )
            h_sizer.Add( panel, 1, wx.EXPAND|wx.ALL, 1 )
  
        v_sizer.Add( h_sizer, 1, wx.EXPAND|wx.ALL, 1 )      
        self.SetSizer( v_sizer )
        self.Layout()

        self.hist = hist

    def clear( self ):
        self.DestroyChildren()

class hist_panel( wx.Panel ):
    def __init__( self, parent, hist ):
        wx.Panel.__init__( self, parent )
        sizer = wx.BoxSizer( wx.VERTICAL )
        self.l_bin = wx.StaticText( self, -1, '', size=(40,20) )
        sizer.Add( self.l_bin, 0, wx.ALL, 1 ) 

        self.l_num = wx.StaticText( self, -1, '', size=(40,20) )
        sizer.Add( self.l_num, 0, wx.ALL, 1) 

        canvas = hist_canvas( self, hist )
        sizer.Add( canvas, 1, wx.EXPAND|wx.ALL, 1 )                

        self.SetSizer( sizer )

class hist_canvas( wx.Panel ):
    def __init__( self, parent, hist ):
        wx.Panel.__init__( self, parent,
                           style=wx.FULL_REPAINT_ON_RESIZE )
        self.l_bin = parent.l_bin    # report labels 
        self.l_num = parent.l_num
        self.hist = hist             # 1-d array
        self.num = self.hist.size    # TODO: option to exclude bin 0 (for nan)
        self.max = self.hist.max()
        self.bin_pos = int(self.num/2.0)

        self.SetBackgroundColour( wx.NullColour )
        self.Bind( wx.EVT_PAINT, self.on_paint )
        self.Bind( wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind( wx.EVT_LEFT_DOWN, self.on_left_down )
        self.Bind( wx.EVT_MOTION, self.on_motion )

        self.dragging = False

    def on_paint( self, event ):    # render histogram

        # if self.hist == None:

        if type(self.hist) is not np.ndarray:
            return

        dc = wx.PaintDC( self )
        width,height = dc.GetSize()
        
        if self.max == 0:
            return
        scale_h = float(width)/self.max      # calculate dimension scales
        scale_v = float(self.num)/height

        dc.SetPen( wx.Pen('black', 1) )
        for i in range(0,height):            # fill entire panel
            j = int(scale_v*i)
            dc.DrawLine( 0, i, 
                         int(self.hist[j]*scale_h), i )
      
        dc.SetPen( wx.Pen('red', 1) )        # set indicator
        #dc.SetLogicalFunction( wx.XOR )

        self.ypos = int(self.bin_pos/scale_v)
        dc.DrawLine( 0, self.ypos, width-1, self.ypos )

        self.report()

    def on_left_down( self, event ):
        self.dragging = True
        self.on_motion( event )

    def on_left_up( self, event ):
        self.dragging = False

    def on_motion( self, event ):
        if not self.dragging:
            return

        width,height = self.GetClientSize()
        xpos,ypos = event.GetPosition()

        if ypos < 0 or ypos >= height:
            return

        dc = wx.ClientDC( self )

        #color = wx.Colour( 255,0,0 )            # red
        #dc.SetPen( wx.Pen( 'blue', 1) )          # set indicator
        #dc.SetLogicalFunction( wx.XOR )

        dc.DrawLine( 0, self.ypos, width-1, self.ypos )# erase old line
        dc.DrawLine( 0, ypos, width-1, ypos )  # draw new line
        
        self.ypos = ypos

        scale_v = float(self.num)/height
        self.bin_pos = int(ypos*scale_v)
        
        self.report()

    def report( self ):
        value = 'bin:'+'%6d'%(self.bin_pos) 
        self.l_bin.SetLabel( value )           # offset by one to compensate 
                                               # for nan exclusion
        value = str(self.hist[self.bin_pos])
        self.l_num.SetLabel( value )
