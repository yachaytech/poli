'''
@file pan_zoom.py
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
Manage panning and zooming the image
'''

pan_zoom_copyright = 'pan_zoom.py Copyright (c) 2010-2022 Scott L. Williams, released under GNU GPL V3.0'

import wx
import sys

areal = []       # position and scale list for operator sink image display.
                 # using the list allows implicit forward propagation
                 # for operator display position and scale. 
                 # forward propagation is clumsier if each op_panel carried
                 # the areal = (ox,oy),scale variable

class zoomer():  # control for geometric scaling of display image
    def __init__( self, benchtop ):
        self.benchtop = benchtop
        self.source = None
        self.overlay = None
        self.transparency = 1.0

    # scale the display image equally in both dimensions
    def zoom_by( self, scale, index, point=None ):
        
        # scale == None means to redraw with existing values
        # used when switching bands and adjusting transparency 
        if scale == None:
            scale = areal[index][1]

        width,height = self.source.GetSize() 
        
        if scale == 1.0:
            scaled_image = self.source
            scaled_overlay_image = self.overlay
        else:
            # scale the source image by some factor
            image = self.source.ConvertToImage()
            image = image.Scale( width*scale, height*scale) 
            #scaled_image = wx.BitmapFromImage( image )
            scaled_image = wx.Bitmap( image )

            if self.overlay != None:
                overlay = self.overlay.ConvertToImage()
                overlay = overlay.Scale( width*scale, height*scale) 
                scaled_overlay_image = wx.Bitmap( overlay )
            else:
                scaled_overlay_image = None

        # determine origin placement

        # start with where we were
        x_origin, y_origin = areal[index][0]
        o_scale = areal[index][1]

        if point == None:

            # place new image display center at 
            # same location as previous image

            # get center of old image in display view space
            # this is where new image's center is placed
            width = int(width*o_scale)
            height = int(height*o_scale)
    
            point = wx.Point( int(x_origin + width/2 ),
                              int(y_origin + height/2) )

        # place zoomed image at same
        # pixel location as given point

        # gives position in image
        px = (point.x - x_origin)/o_scale
        py = (point.y - y_origin)/o_scale

        ox = point.x - int(px*scale+0.5)   # apply new scale to get origin
        oy = point.y - int(py*scale+0.5)

        areal[index] = (ox,oy), scale      # replace values
        self.send_image( scaled_image, scaled_overlay_image, (ox,oy) )

    # set image source for display and
    # return registered display offset and scale.
    # registering areal features allows operators 
    # to reshape images and remember location and scale
    def set_source( self, source, overlay, index=None ): 
        if source == None:
            return

        if overlay != None and (source.GetSize() != overlay.GetSize()):
            print( 'pan_zoom:zoomer:set_source: overlay shape != source.shape',
                   file=sys.stderr )
            return

        '''
        del self.source     # try to free up memory
        del self.overlay
        '''

        self.source = source
        self.overlay = overlay

        if index != None:   # check if operator is using
                            # registered origin and scale

            # apply pre-assigned origin and scale
            self.zoom_by( None, index )
            return index # return same index

        # initiate a new origin and scale

        # scale to fit display view
        display = self.benchtop.display
        v_width, v_height = display.GetClientSize()
        i_width, i_height = self.source.GetSize()

        # check if image fits in view
        if  (i_width < v_width) and (i_height < v_height): 

            # noscaling; send as is
            origin = self.send_image( self.source, 
                                      self.overlay ) # create registry
            areal.append( (origin,1.0) )       # clean this up in send_image
            return len( areal ) - 1

        # scale to smallest dimension of view
        if v_width < v_height :
            scale = float(v_width)/i_width
        else:
            scale = float(v_height)/i_height

	# apply scale to source image
        width = i_width*scale
        height = i_height*scale

        image = self.source.ConvertToImage()
        image = image.Scale(width, height)
        #scaled_image = wx.BitmapFromImage( image )
        scaled_image = wx.Bitmap( image )

        if self.overlay != None:
            image_overlay = self.overlay.ConvertToImage()
            image_overlay = image_overlay.Scale(width, height)
            #scaled_image_overlay = wx.BitmapFromImage( image_overlay )
            scaled_image_overlay = wx.Bitmap( image_overlay )
        else:
            scaled_image_overlay = None

        origin = self.send_image( scaled_image,
                                  scaled_image_overlay ) # create registry
        areal.append( (origin,scale) )   

        return len( areal ) - 1 # return operator areal index 
        
    def send_image( self, image, overlay, origin=None ):
        display = self.benchtop.display
        
        if self.transparency == 1.0:
            return display.set_image( image, overlay, origin )

        if overlay != None:
            image_overlay = overlay.ConvertToImage()
            new_overlay = image_overlay.AdjustChannels( 1.0, 1.0, 1.0,
                                                        self.transparency )
            #new_overlay = wx.BitmapFromImage( new_overlay )
            new_overlay = wx.Bitmap( new_overlay )
        else:
            new_overlay = None

        return display.set_image( image, new_overlay, origin )

    # check if point is in view image
    def is_inside( self, point, index ):
        width,height = self.source.GetSize()
        (tlx,tly), scale = areal[index]
          
        brx = tlx + width*scale
        bry = tly + height*scale

        if point.x >= tlx and point.x <= brx :
            if point.y >= tly and point.y <= bry:
                return True

        return False

    # move the current image in display
    def move_it( self, delta, index ):
        (ox,oy),scale = areal[index]
        
        # calculate new image origin 
        ox += delta.x
        oy += delta.y
        
        origin = ox, oy
        display = self.benchtop.display
        display.set_origin( origin );
        
        areal[index] = origin, scale

class panner( wx.Panel ):
    def __init__( self, parent, benchtop ):
        self.benchtop = benchtop

        wx.Panel.__init__( self, parent, style=wx.SUNKEN_BORDER )
        
        self.source = None     # thumb image
        self.origin = None     # top left position of thumb image

        self.bx = None
        self.by = None

        #self.box_width = None
        #self.box_height = None

        #self.SetToolTipString(
        #    'pan image by pressing mouse button and dragging')

        self.Bind( wx.EVT_PAINT, self.on_paint )
        self.Bind( wx.EVT_LEFT_DOWN, self.on_left_down )
        self.Bind( wx.EVT_LEFT_UP, self.on_left_up )
        self.Bind( wx.EVT_MOTION, self.on_motion )            

        self.SetBackgroundColour( wx.NullColour )

        self.begin = None

    def on_left_up( self, event ):     # end mouse deltas
        if self.source == None:
            return

        self.begin = None           
        event.Skip()

    def on_left_down( self, event ):   # begin mouse pos
        if self.source == None:
            return

        self.begin =  event.GetPosition()  
        event.Skip()

    def on_motion( self, event ):      # display panning
        if self.begin == None:
            return

        point = event.GetPosition()
        dx,dy = point - self.begin

        index = self.benchtop.op_note.GetSelection() # current op
        a_index = self.benchtop.op[index].areal_index

        # calculate image origin 
        (dox,doy) = areal[a_index][0]  # get current position

        # calculate scale
        image = self.benchtop.display.image
        i_width,i_height = image.GetSize()
        t_width,t_height = self.GetClientSize()
        scale = float(i_width)/t_width 

        sx = dox - dx*scale
        sy = doy - dy*scale

        # move display image
        self.benchtop.display.set_origin( (sx,sy) )
        self.begin = point   # reset begin point

        # update areal entry; otherwise display pan skips
        origin,scale = areal[a_index]
        areal[a_index] = (sx,sy),scale

    def set_source( self, source ):
        if source == None: 
            return

        del self.source # try to free up memory

        # calculate position of thumb image
        s_width, s_height = source.GetSize()
        b_width, b_height = self.get_inner_size()

        self.origin = wx.Point( b_width/2.0  - s_width/2.0, 
                                b_height/2.0 - s_height/2.0  )
        self.source = source
        self.Refresh()

    def on_paint( self, event ):
        if  self.source == None:
            return

        if self.bx == None:
            return

        x = self.origin[0]
        y = self.origin[1]
 
        dc = wx.PaintDC( self )
        dc.DrawBitmap( self.source, x, y,
                            useMask=False)

        # draw box
        dc.SetPen( wx.Pen('blue', 2) )      # TODO: get frame top bar color
        #dc.SetLogicalFunction( wx.XOR )
        trx = self.bx+self.bwidth-1
        bry = self.by+self.bheight-1
        dc.DrawLine( self.bx, self.by, trx, self.by)
        dc.DrawLine( trx, self.by, trx, bry )
        dc.DrawLine( trx, bry, self.bx, bry )
        dc.DrawLine( self.bx, bry, self.bx, self.by )

    # return interior size of panel
    def get_inner_size( self ):
        
        # alert: UTIL_SIZE_X - 2 is used instead of getSize
        #        since panel may be (partially) closed
        
        return self.benchtop.UTIL_SIZE_X - 2, \
               self.benchtop.UTIL_SIZE_X - 2

    # remove image and clear the canvas 
    def clear( self ):
        self.source = None;
        self.Refresh()

    def set_viewbox( self, i_size, d_size, d_origin ):
 
        # calculate scale of thumb to source
	# can be derived from either dimension of image

        i_width,i_height = i_size
        t_width,i_height = self.source.GetSize()
        scale = float(i_width)/t_width 

        # get top left origin of interior of box
        dox,doy = d_origin
        ox,oy = self.origin

        self.bx = ox - dox/scale - 1     # make box circumscribe
        self.by = oy - doy/scale - 1     # view with -1 origin

        width,height = d_size
        self.bwidth  = width/scale  + 2  # and with +2 width
        self.bheight = height/scale + 2

        # draw the box
        self.Refresh()
