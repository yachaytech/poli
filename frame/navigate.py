'''
@file navigate.py
@author Scott L. Williams.
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
Report navigation values (location and values)
'''

navigate_copyright = 'navigate.py Copyright (c) 2010-2024 Scott L. Williams, released under GNU GPL V3.0'

import wx
import numpy as np
from pan_zoom import areal

# panel for reporting nav values at display and data levels
class navigate( wx.Panel ):
    def __init__( self, parent, benchtop ):
        wx.Panel.__init__( self, parent )
        
        self.benchtop = benchtop
        self.nav_data = None
        self.nav_tags = None
        self.image    = None    # for data values

        self.init_panel()
        
    def init_panel( self ):
        v_box = wx.BoxSizer( wx.VERTICAL )
        h_box = wx.BoxSizer( wx.HORIZONTAL )

        p_scrn = self.make_scrnpos_panel()
        h_box.Add( p_scrn, 0, wx.EXPAND|wx.ALL, 1 )

        p_real = self.make_realpos_panel()
        h_box.Add( p_real, 0, wx.ALL, 1 )

        v_box.Add( h_box, 0, wx.EXPAND|wx.ALL, 1 )

        p_data = self.make_data_panel()
        v_box.Add( p_data, 0, wx.EXPAND|wx.ALL, 2 )

        self.p_overlay = self.make_overlay_panel()
        v_box.Add( self.p_overlay, 0, wx.EXPAND|wx.ALL, 2 )
        self.p_overlay.Disable()

        self.SetSizer( v_box )

    def make_overlay_panel( self ) :
        p_overlay = wx.Panel( self, -1, style=wx.SUNKEN_BORDER) 
        
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        c_setoverlay = wx.CheckBox( p_overlay, -1, 'overlay' )
        c_setoverlay.SetToolTip( 'toggle display overlay' )
        c_setoverlay.SetValue( True )
        c_setoverlay.Bind( wx.EVT_LEFT_UP, self.on_overlay )
        v_sizer.Add( c_setoverlay, 0, wx.ALL, 1 )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( p_overlay, -1, 'transparency' )
        h_sizer.Add( prompt, 1, wx.TOP, 5)
       
        self.t_transfactor = wx.TextCtrl( p_overlay, -1, '1.0', 
                                          size=(40,25),  
                                          style=wx.ALIGN_RIGHT )
        self.t_transfactor.Bind( wx.EVT_KEY_DOWN, self.on_file_key) 
        self.t_transfactor.SetToolTip( 'enter transparency factor 0.0-1.0' )
        h_sizer.Add( self.t_transfactor, 0, wx.ALL, 1 )

        b_apply = wx.Button( p_overlay, -1, 'apply', size=(55,25) )
        b_apply.Bind( wx.EVT_LEFT_UP, self.on_apply )             
        h_sizer.Add( b_apply, 0, wx.ALL, 1 )

        v_sizer.Add( h_sizer, 1, wx.ALL )
        p_overlay.SetSizer( v_sizer )

        return p_overlay

    def on_overlay( self, event ):
        obj = event.GetEventObject()
        value = not obj.IsChecked()
        self.benchtop.display.set_show_overlay( value )
        event.Skip()

    # intercept keystroke; look for CR
    def on_file_key( self, event ):
        keycode = event.GetKeyCode()

        if keycode == wx.WXK_RETURN:
            self.on_apply( None )     # as if pressing 'apply'
        event.Skip()                  # pass along event

    # respond to apply click
    def on_apply( self, event ):
        
        factor = float(self.t_transfactor.GetValue())
        if factor < 0.0 or factor > 1.0:
            print( 'transparency factor must be 0.0-1.0', file=sys.stderr )
        else:
            zoom = self.benchtop.zoom
            zoom.transparency = factor
            zoom.zoom_by( None, len(areal)-1 )

    def make_scrnpos_panel( self ) :
                    
        p_scrn = wx.Panel( self, -1, style=wx.SUNKEN_BORDER) 

        grid = wx.GridSizer( 3, 2, 1, 1 )

        label = wx.StaticText( p_scrn, -1, 'scale', size=(63,20) )
        grid.Add( label, 0, wx.ALL, 1 )
        self.l_scale = wx.StaticText( p_scrn, -1, '', 
                                      size=(63,20), style=wx.ALIGN_RIGHT )
        grid.Add( self.l_scale, 0, wx.ALL, 1 )

        label = wx.StaticText( p_scrn, -1, 'xpos' )
        grid.Add( label, 0, wx.ALL, 1 )
        self.l_sx = wx.StaticText( p_scrn, -1, '',
                                     size=(63,20), style=wx.ALIGN_RIGHT )
        grid.Add( self.l_sx, 0, wx.ALL, 1 )
        
        label = wx.StaticText( p_scrn, -1, 'ypos' )
        grid.Add( label, 0, wx.ALL, 1 )
        self.l_sy = wx.StaticText( p_scrn, -1, '', 
                                     size=(63,20), style=wx.ALIGN_RIGHT )
        grid.Add( self.l_sy, 0, wx.ALL, 1 )

        p_scrn.SetSizer( grid )

        return p_scrn

    def make_realpos_panel( self ): 
        grid = wx.GridSizer( 3, 2, 1, 1 )

        p_real = wx.Panel( self, -1, style=wx.SUNKEN_BORDER )

        label = wx.StaticText( p_real, -1, 'real world:', size=(63,20) )
        #label = wx.StaticText( p_real, -1, 'real world:' )
        grid.Add( label, 0, wx.ALL, 1 )

        label = wx.StaticText( p_real, -1, '', size=(63,20) )
        #label = wx.StaticText( p_real, -1, '' )
        grid.Add( label, 0, wx.ALL, 1 )

        #self.l_tag2 = wx.StaticText( p_real, -1, '', size=(35,20) )
        self.l_tag2 = wx.StaticText( p_real, -1, '' )
        grid.Add( self.l_tag2, 0, wx.ALL, 1 )
        '''
        self.l_dim2 = wx.StaticText( p_real, -1, '', size=(52,20),
                                      style=wx.ALIGN_RIGHT )
        '''
        self.l_dim2 = wx.StaticText( p_real, -1, '', style=wx.ALIGN_RIGHT )
        grid.Add( self.l_dim2, 0, wx.ALL, 1 )
        
        #self.l_tag1 = wx.StaticText( p_real, -1, '', size=(35,20) )
        self.l_tag1 = wx.StaticText( p_real, -1, '')
        grid.Add( self.l_tag1, 0, wx.ALL, 1 )
        '''
        self.l_dim1 = wx.StaticText( p_real, -1, '', size=(52,20),
                                     style=wx.ALIGN_RIGHT )
        '''
        self.l_dim1 = wx.StaticText( p_real, -1, '', style=wx.ALIGN_RIGHT )
        grid.Add( self.l_dim1, 0, wx.ALL, 1 )

        p_real.SetSizer( grid )
        return p_real

    def make_data_panel( self ):
        p_data = wx.Panel( self, -1, style=wx.SUNKEN_BORDER) 

        grid = wx.GridSizer( 5, 3, 1, 1)

        label = wx.StaticText( p_data, -1, 'band', size=(60,20) )
        grid.Add( label, 0, wx.ALL, 1 )
        label = wx.StaticText( p_data, -1, 'pixel', size=(40,20),
                               style=wx.ALIGN_RIGHT )
        grid.Add( label, 0, wx.ALL, 1 )
        label = wx.StaticText( p_data, -1, 'data', size=(60,20),
                               style=wx.ALIGN_RIGHT )
        grid.Add( label, 0, wx.ALL, 1 )

        label = wx.StaticText( p_data, -1, 'grey', size=(60,20) )
        grid.Add( label, 0, wx.ALL, 1 )
        self.l_grey_i = wx.StaticText( p_data, -1, '', size=(40,20), 
                                       style=wx.ALIGN_RIGHT )
        grid.Add( self.l_grey_i, 0, wx.ALL, 1 )

        self.l_grey_d = wx.StaticText( p_data, -1, '', size=(70,20), 
                                       style=wx.ALIGN_RIGHT )
        grid.Add( self.l_grey_d, 0, wx.ALL, 1 )        

        label = wx.StaticText( p_data, -1, 'red', size=(60,20) )
        grid.Add( label, 0,  wx.ALL, 1 )
        self.l_red_i = wx.StaticText( p_data, -1, '', size=(40,20), 
                                      style=wx.ALIGN_RIGHT )
        grid.Add( self.l_red_i, 0, wx.ALL, 1 ) 

        self.l_red_d = wx.StaticText( p_data, -1, '', size=(70,20), 
                                      style=wx.ALIGN_RIGHT )
        grid.Add( self.l_red_d, 0, wx.ALL, 1 )        

        label = wx.StaticText( p_data, -1, 'green',  size=(60,20) )
        grid.Add( label, 0,  wx.ALL, 1 )
        self.l_green_i = wx.StaticText( p_data, -1, '', size=(40,20), 
                                        style=wx.ALIGN_RIGHT )
        grid.Add( self.l_green_i, 0, wx.ALL, 1 ) 

        self.l_green_d = wx.StaticText( p_data, -1, '', size=(70,20), 
                                        style=wx.ALIGN_RIGHT )
        grid.Add( self.l_green_d, 0, wx.ALL, 1 )        

        label = wx.StaticText( p_data, -1, 'blue', size=(60,20) )
        grid.Add( label, 0,  wx.ALL, 1 )
        self.l_blue_i = wx.StaticText( p_data, -1, '', size=(40,20), 
                                       style=wx.ALIGN_RIGHT )
        grid.Add( self.l_blue_i, 0, wx.ALL, 1 ) 

        self.l_blue_d = wx.StaticText( p_data, -1, '', size=(70,20), 
                                       style=wx.ALIGN_RIGHT )
        grid.Add( self.l_blue_d, 0, wx.ALL, 1 )        

        p_data.SetSizer( grid )

        return p_data

    # service display motion event
    def on_motion( self, point, bitmap, dc, index ):
        origin,scale = areal[ index ]
        width  = bitmap.GetWidth()
        height = bitmap.GetHeight()
        
        px,py = point
        ox,oy = origin

        # inside image box ?
        if  not (px >= ox and px < (ox + width ) and \
                 py >= oy and py < (oy + height ) ):
            return

        #red,green,blue = dc.GetPixel( px, py )      # get dc pixel value
        color = dc.GetPixel( px, py )
        red,green,blue = color.Get( includeAlpha=False )
        
        page = self.benchtop.op_note.GetSelection()  
        oper = self.benchtop.op[ page ]

        # check if image is merged or if using LUT (sort of)
        if oper.c_merge.IsChecked() or \
            (red != blue) or           \
            (red != green) or          \
            (blue != green) :                
            self.l_grey_i.SetLabel( 'n/a' )          

            self.l_red_i.SetLabel( '%6d'%red  )
            self.l_green_i.SetLabel( '%6d'%green )
            self.l_blue_i.SetLabel( '%6d'%blue )            
        else:
            # display is rgb even if deemed grey; grab red
            self.l_grey_i.SetLabel( '%6d'%red )

            self.l_red_i.SetLabel( 'n/a' )
            self.l_green_i.SetLabel( 'n/a' )
            self.l_blue_i.SetLabel( 'n/a' )

        self.l_scale.SetLabel( '%6.2f'%scale )

        ix = int((px-ox)/scale)
        iy = int((py-oy)/scale)
               
        self.l_sx.SetLabel( '%6d'%ix )
        self.l_sy.SetLabel( '%6d'%iy )

        # report data values
        if scale < 1 :       # qualifying flag: scale < 1 requires know-how
            ast = '*'        # on pixel mangeling in wx.Image mapping. 
                             # TODO: mesh pixel mangel with data index.
                             # meanwhile, flag indexing as qualified. 
                             # for scale > 1, and powers of 2, indexing 
                             # is correct. for this reason we only zoom 
                             # in powers of 2 in pan_zoom
        else:
            ast = ''

        if oper.c_merge.IsChecked():
            self.l_grey_d.SetLabel( 'n/a' )

            self.l_red_d.SetLabel( ast + '%10.3f'%self.image[iy,ix,0]  )
            self.l_green_d.SetLabel( ast + '%10.3f'%self.image[iy,ix,1] )
            self.l_blue_d.SetLabel( ast + '%10.3f'%self.image[iy,ix,2] )
                
        else:
            band = oper.s_band.GetValue()   # get band num and pixel value
            self.l_grey_d.SetLabel( ast + '%10.3f'%self.image[iy,ix,band] )

            self.l_red_d.SetLabel( 'n/a' )
            self.l_green_d.SetLabel( 'n/a' )
            self.l_blue_d.SetLabel( 'n/a' )

        #if self.nav_data == None :
        if type(self.nav_data) is not np.ndarray:

            self.l_tag1.SetLabel( 'n/a' )
            self.l_tag2.SetLabel( 'n/a' )
        
        else:    
            self.l_tag1.SetLabel( self.nav_tags[0] )
            value = '%10.5f'%self.nav_data[iy,ix,0]
            self.l_dim1.SetLabel( value )

            self.l_tag2.SetLabel( self.nav_tags[1]) 
            value = '%10.5f'%self.nav_data[iy,ix,1]
            self.l_dim2.SetLabel( value )

    #
    def set_nav_data( self, data, tags, image ):
        del self.nav_data
        del self.image

        self.nav_data = data
        self.nav_tags = tags
        self.image = image

        #if self.nav_data == None:
        if type(self.nav_data) is not np.ndarray:
            self.clear()

    def clear( self ):
 
        self.l_scale.SetLabel( '' )       
        self.l_sx.SetLabel( '' )
        self.l_sy.SetLabel( '' )
        self.l_tag1.SetLabel( '' )
        self.l_tag2.SetLabel( '' )
        self.l_dim1.SetLabel( '' )
        self.l_dim2.SetLabel( '' )
        self.l_grey_i.SetLabel( '' )
        self.l_red_i.SetLabel( '' )
        self.l_green_i.SetLabel( '' )
        self.l_blue_i.SetLabel( '' )
        self.l_grey_d.SetLabel( '' )
        self.l_red_d.SetLabel( '' )
        self.l_green_d.SetLabel( '' )
        self.l_blue_d.SetLabel( '' )
