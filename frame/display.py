'''
@file display.py
@author Scott L. Williams
@package POLI
@section LICENSE 

#  Copyright (C) 2010-2024 Scott L. Williams.

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
Manage POLI's display panel
'''

display_copyright = 'display.py Copyright (c) 2010-2024 Scott L. Williams, released under GNU GPL V3.0'

import wx

class display_panel( wx.Panel ):
    def __init__( self, benchtop ):
        self.benchtop = benchtop

        wx.Panel.__init__( self, benchtop,
                           style=wx.SUNKEN_BORDER )

        self.image = None      # bitmapped image to display
        self.overlay = None
        self.show_overlay = True

        self.factor = 1.0      # keep track of zoom factor

        self.bind_mouse()
        self.Bind( wx.EVT_PAINT, self.on_paint )

        self.SetBackgroundColour( wx.NullColour )

        self.origin = None
        self.begin = None
        self.dragging = False

    def set_show_overlay( self, value ):
        self.show_overlay = value
        self.on_paint( None )

    def bind_mouse( self ):
        self.mouse = True

        self.Bind( wx.EVT_MOUSEWHEEL, self.on_wheel )   
        self.Bind( wx.EVT_LEFT_DOWN, self.on_left_down )
        self.Bind( wx.EVT_LEFT_UP, self.on_left_up )
        self.Bind( wx.EVT_MOTION, self.on_motion )            

    def unbind_mouse( self ):
        self.mouse = False

        self.Unbind( wx.EVT_MOUSEWHEEL )   
        self.Unbind( wx.EVT_LEFT_DOWN )
        self.Unbind( wx.EVT_LEFT_UP )
        self.Unbind( wx.EVT_MOTION )            

    def on_left_up( self, event ):   # end mouse drag
        if self.image == None:
            return

        self.begin = None # end mouse deltas
        self.dragging = False
        event.Skip()

    def on_left_down( self, event ): # start mouse drag
        if self.image == None:
            return

        pos = event.GetPosition()  
        page = self.benchtop.op_note.GetSelection() # current op
        index = self.benchtop.op[page].areal_index
        if self.benchtop.zoom.is_inside( pos, index ):
            self.begin = pos       #stash points for mouse deltas
            
        self.dragging = True
        event.Skip()

    def on_motion( self, event ):  # display panning
        if self.image == None:
            return

        index = self.benchtop.op_note.GetSelection() # current op
        areal_index = self.benchtop.op[index].areal_index
        point = event.GetPosition()

        if self.dragging:
            if self.begin == None:
                return

            delta = point - self.begin
            self.benchtop.zoom.move_it( delta, areal_index )
            self.begin = point     # reset begin point

        else:
            nav = self.benchtop.pan_tools.nav
            dc = wx.ClientDC( self )
            nav.on_motion( point, self.image, dc, areal_index )

        event.Skip()

    def on_wheel( self, event ):  # zooming
        if self.image == None:
            return

        # check if inside image
        pos = event.GetPosition()  
        page = self.benchtop.op_note.GetSelection() # current op
        index = self.benchtop.op[page].areal_index
        if not self.benchtop.zoom.is_inside( pos, index ):
            return

        self.Enable( False )

        notches = event.GetWheelRotation()

        if notches > 0 : 
            if self.factor >= 8.0:
                return
            self.factor *= 2.0
        else: 
            if self.factor <= 1/8.0:
                return
            self.factor /= 2.0

        # retrieve areal index to send to zoomer
        index = self.benchtop.op_note.GetSelection() # current op
        areal_index = self.benchtop.op[index].areal_index

        # have zoom center on mouse position
        zoom = self.benchtop.zoom
        zoom.zoom_by( self.factor, areal_index, pos )

    # reset display image with a defined origin
    def set_image( self, image,overlay, point=None ): 
        if image == None:
            return

        #if self.image != None:      # try to free up memory
        #del self.image
        #del self.overlay
        self.image = image
        self.overlay = overlay

        # enable or disable overlay panel
        nav = self.benchtop.pan_tools.nav
        if self.overlay == None:
            nav.p_overlay.Disable()
        else:
            nav.p_overlay.Enable()
            
        i_width = image.GetWidth()
        i_height = image.GetHeight()
        
        if point == None:
            width,height = self.GetClientSize();
            o_x = width/2.0  - i_width/2.0
            o_y = height/2.0 - i_height/2.0
            point = wx.Point( o_x,o_y ) 

        self.set_origin( point )
        return point
        
    def set_origin( self, point ):  # move origin of display image
        
        #if ( streaming ) return;

        self.origin = point
        self.Refresh()

    def clear( self ):              # reset and clear the canvas 
        self.image = None
        self.source = None
        self.overlay = None
        self.origin = None

        self.Refresh()  

    def on_paint( self, event ):
        
        if self.origin == None:
            return
        
        x = self.origin[0]
        y = self.origin[1]
        dc = wx.ClientDC( self )
        dc.DrawBitmap( self.image, self.origin, useMask=False)

        if self.overlay != None and self.show_overlay == True:
            dc.DrawBitmap( self.overlay, x, y, useMask=False)

        # update the view box in panner
        self.benchtop.pan.set_viewbox( self.image.GetSize(),
                                       self.GetClientSize(),
                                       self.origin )

        self.Enable( True )   # allow more mouse events
        if event != None:
            event.Skip()
