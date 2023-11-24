'''
@file op_panel.py
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

@section DESCRIPTION
Super (base) class for POLI operators. This is an  abstract class, don't call directly. 
'''
op_panel_copyright = 'op_panel.py Copyright (c) 2010-2024 Scott L. Williams, released under GNU GPL V3.0'

import os
import wx
import sys
import time
import pickle

import numpy as np
from PIL import Image	

from threads import apply_thread
from threads import monitor_thread
from threads import EVT_PROCESS_DONE_EVENT

# Reminder: numpy array dimensions are typically indexed Y,X,Z
#           To add further confusion screen, the top left corner is the
#           origin (0,0) while the program "ncview" uses the bottom left
#           corner as the origin.

# coastwatch hdf satellite attributes
class attr():   
    def __init__( self ):
        self.satellite = None
        self.sensor = None
        self.origin = None
        self.history = None
        self.cwhdf_version = None
        self.pass_date = None          # nominally from 01/01/1970, day.xxx
        self.start_time = None
        self.projection_type = None
        self.projection = None
        self.gctp_sys = None
        self.gctp_zone = None
        self.gctp_parm = None
        self.gctp_datum = None
        self.et_affine = None
        self.rows = None
        self.cols = None
        self.polygon_latitude = None
        self.polygon_longitude = None
        self.pass_type = None          # day, night or day/night
        self.composite = None

# sets up panels graphics, provides operators with source data and 
# formats images and navigation to dispay panel
# initiates operator processing thread
class op_panel( wx.Panel ):

    # initialize but no graphics 
    def __init__( self, name ):         
        self.name = name        # operator name

        self.source = None      # 3d areal source image to process
        self.sink = None        # 3d areal output image
        self.band_tags = None   # band names

        self.nav_data = None    # 2 band image (lat,long); can be any measure
        self.nav_tags = None    # list unit label for nav measure

        self.angles = None      # sat and sun angles
        self.overlay = None     # 2-d image uint8 layer 
                                # political, cil, etc. 
                                # keep raw image for hdf writing

        self.hist = None        # histogram array of sink data
        self.attr = attr()      # satellite attributes

        self.source_name = None # source file name
        self.params = None      # parameter object
        
        self.display_overlay_image = None
    # override this method in subclass
    def run( self ):
        print( 'op_panel:run: this method should not be called directly',
               file=sys.stderr )

    # unpickel this operator's parameters from file 
    def read_params_from_file( self, filename ):

        try:
            file = open( filename, 'rb' ) # read the array from file
            array = file.read()
            file.close()

        except IOError as e:
            print( e, file=sys.stderr )
            return False

        self.params = pickle.loads( array )
        return True

    # pickle and store parameter values
    def write_params_to_file( self, filename ):
        params_array = pickle.dumps( self.params )

        try:
            file = open( filename, 'wb' ) # write the array to file
            file.write( params_array )
            file.close()

        except IOError as e:
            print( e, file=sys.stderr )
            return

    def get_source_op( self, offset ):
        index = self.benchtop.op.index( self )    # discover our index 
        if  offset > index or offset <= 0:        # check for invalid offset
            print( 'op_panel:get_source: invalid offset value',
                   file=sys.stderr )
            print( 'op_panel:get_source: no source operator?', file=sys.stderr )
            return None
        
        neighbor = index-offset                   # get neighbor index
        return self.benchtop.op[neighbor]
    
    # get the sink (output) data from an operator neighbor
    def get_source( self, offset ):

        src_op = self.get_source_op( offset )
        if src_op == None:
            return None
        
        self.attr = src_op.attr   # get sat info 
        self.source_name = src_op.source_name
        return src_op.sink        # return neighbor sink

    ####################################################################
    # gui section
    ####################################################################

    # get the areal and band/nav tags from a neighbor
    # operator and set as ours
    def set_areal_tags( self, offset ):
        index = self.benchtop.op.index( self )    # discover our index 
        if  offset > index or offset <= 0:        # check for invalid offset
            print( 'op_panel:set_areal_tags: invalid offset value',
                   file=sys.stderr )
            print( 'op_panel:set_areal_tags: no source operator?',
                   file=sys.stderr )
            return

        neighbor = index-offset                   # get neighbor index 

        # inherit source info
        source_op = self.benchtop.op[neighbor]    # get neighbor operator 

        self.areal_index = source_op.areal_index  # follow display format
        self.band_tags = source_op.band_tags      # from source. overide values
        self.nav_data = source_op.nav_data        # in sub operator, if needed.
        self.nav_tags = source_op.nav_tags        # eg. ops that change shape 
                                                  #     or navigation
        self.angles = source_op.angles

        self.overlay = source_op.overlay
        self.overlay_image = source_op.overlay_image

    # initialize graphics 
    def init_panel( self, benchtop ):
        wx.Panel.__init__( self, benchtop.op_note )

        self.benchtop = benchtop          #shorthand
        self.messages = benchtop.messages
        self.report = benchtop.report

        self.setup_items()                # base gui
        self.display_image = None
        self.overlay_image = None
        self.thumb_image = None

        self.lut = None 
        benchtop.pan_tools.settings.Enable( True )

        # areal_index keeps track of origin and scale for ops.
        # create a new areal_index in subclass by setting
        # areal_index = None in subclass; image will be centered
        # and a new index assigned. if changing shape don't forget 
        # to adjust nav_data, etc.
        self.areal_index = None           
        self.Bind( EVT_PROCESS_DONE_EVENT, 
                   self.on_process_done )

    def on_process_done( self, event ):
        self.app_thread.join()            # wait for app thread to finish
  
        self.report.SetLabel( ' ' )
        self.report.SetLabel( self.name + ' processing done.' )

        # report process duration
        process_time = '%.3f' % event.duration
        self.messages.append('\tprocessing time:\t' +
                              process_time + ' s'  + '\n' )

        #if self.sink == None:
        if type(self.sink) is not np.ndarray:
            self.report.SetLabel( 'no output image' )
            self.messages.append( '\tno output image\n' )
            self.benchtop.clear()
            self.finalize()
            return

        self.report.SetLabel( 'rendering image...' )
        start = time.time()

        self.show_image() 

        duration = time.time()-start      # measure display rendering time
        self.report.SetLabel( 'rendering done.' )

        # show tag label
        if self.band_tags != None:

            band = self.s_band.GetValue()
            self.l_tag.SetLabel( self.band_tags[band] )

        process_time = '%.3f' % duration       
        self.messages.append('\trendering time:\t' +  
                              process_time + ' s'  + '\n' )
        self.finalize()
        self.report_image( self.sink )

    def setup_items( self ):
       
        # this panel consists of three sub-panels:
        # two panels (command, and color band merge) are managed by this
        # super class while the third panel is managed by the sub class

        # create command panel ( start, cascade, cancel, options )
        p_command = wx.Panel( self, -1)

        # command buttons
        self.b_apply = wx.Button( p_command, -1, 'apply' )
        self.b_apply.Bind( wx.EVT_LEFT_UP, self.on_apply )             
        self.b_apply.SetToolTip( 'run this operator' )

        self.b_cascade = wx.Button( p_command, -1, 'cascade' )
        self.b_cascade.Bind( wx.EVT_LEFT_UP, self.on_cascade )             
        self.b_cascade.SetToolTip( 'run this and forward operators' )
        self.b_cascade.Enable( True )

        self.b_cancel = wx.Button( p_command, -1, 'cancel' )
        self.b_cancel.Bind( wx.EVT_LEFT_UP, self.on_cancel )             
        self.b_cancel.SetToolTip( 'cancel processing' )
        self.b_cancel.Enable( False )

        self.b_options = wx.Button( p_command, -1, 'options' )
        self.b_options.Bind( wx.EVT_LEFT_UP, self.on_options )             
        self.b_options.SetToolTip( 'operator option menu' )
        self.b_options.Enable( True )

        v_box = wx.BoxSizer( wx.VERTICAL )
        v_box.Add( self.b_apply, 0 )
        v_box.Add( self.b_cascade, 0 )
        v_box.Add( self.b_cancel, 0 )
        v_box.Add( self.b_options, 0 )
        p_command.SetSizer( v_box )

        # band view and merger panel
        p_bandview = wx.Panel( self, -1, style=wx.SUNKEN_BORDER )
 
        # spinner; band to view
        self.s_band = wx.SpinCtrl(p_bandview, -1, "",
                                  (1,4), (90,20),
                                  style=wx.SP_WRAP|wx.SP_ARROW_KEYS )
        self.s_band.SetRange( 0, 0 )
        self.s_band.SetValue( 0 )
        self.s_band.SetToolTip( 'select an image band to view' )
        self.s_band.Bind( wx.EVT_SPINCTRL, self.on_spin )             

	# tag label
        self.l_tag = wx.StaticText( p_bandview, -1, '', (95,6),(95,20) )
        self.l_tag.SetToolTip( 'band tag' )

        self.c_merge = wx.CheckBox( p_bandview, -1, 'merge', (200,3) )
        self.c_merge.Bind( wx.EVT_CHECKBOX, self.on_merge )             
        self.c_merge.SetToolTip( 'view image as color band merge' )

        # red 
        self.l_red = wx.StaticText( p_bandview, -1, 'r=', (280,5),(15,20) )
        self.t_red = wx.TextCtrl( p_bandview, -1, '0', (297,3), (25,20) )
        self.t_red.SetToolTip( 'enter band number for red' )

        # green 
        self.l_green = wx.StaticText( p_bandview, -1, 'g=', (330,5),(15,20) )
        self.t_green = wx.TextCtrl( p_bandview, -1, '1', (349,3), (25,20) )
        self.t_green.SetToolTip( 'enter band number for green' )

        # blue
        self.l_blue = wx.StaticText( p_bandview, -1, 'b=', (380,5),(15,25) )
        self.t_blue = wx.TextCtrl( p_bandview, -1, '2', (399,3), (25,20) )
        self.t_blue.SetToolTip( 'enter band number for blue' )

        # merge apply
        self.b_apply_merge = wx.Button( p_bandview, -1, 'apply', 
                                        (432,3), (50,20) )
        self.b_apply_merge.Bind( wx.EVT_LEFT_UP, self.on_merge_apply)

        # client panel for subclass
        self.p_client = wx.Panel( self, -1, style=wx.SUNKEN_BORDER )

        #  implement sizers
        v_sizer = wx.BoxSizer( wx.VERTICAL )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL ) # go left to right
        h_sizer.Add( p_command, 0 )
        h_sizer.Add( self.p_client, 1 )
        v_sizer.Add( h_sizer, 0, wx.EXPAND |   # add top side
                                 wx.ALL, 1 )
        
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        h_sizer.Add( p_bandview, 0 )
        v_sizer.Add( h_sizer, 0, wx.EXPAND| wx.ALL, 1 ) #add bottom side

        self.SetSizer( v_sizer )
    
        # disable band components
        self.enable_color( False )
        self.s_band.Enable( False )
        self.l_tag.Enable( False )
        self.c_merge.Enable( False )
    
    def on_options( self, event ):   # pop up options menu
        menu = wx.Menu()

        item = menu.Append( -1, 'read parameters...' )
        self.Bind( wx.EVT_MENU, self.on_read_params, item )
        menu.AppendSeparator()

        item = menu.Append( -1, 'write parameters as...')
        self.Bind( wx.EVT_MENU, self.on_write_params_as, item )
        menu.AppendSeparator()

        item = menu.Append( -1, 'save image as...' )
        self.Bind( wx.EVT_MENU, self.on_save_image_as, item )
        menu.AppendSeparator()

        # grey out menu item if no sink buffer
        if type( self.sink ) is not np.ndarray:
            item.Enable( False )
            
        item = menu.Append( -1, 'save numpy buffer as...' )
        self.Bind( wx.EVT_MENU, self.on_save_numpy_buffer_as, item )
        menu.AppendSeparator()

        if type( self.sink ) is not np.ndarray:
            item.Enable( False )

        self.PopupMenu( menu, (87,0) )
        menu.Destroy() 

    def on_read_params( self, event ):
        dlg = wx.FileDialog( self, "Choose a file to read", 
                            os.getcwd(), "", "*", wx.FD_OPEN )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.read_params_from_file( path )   
            self.write_params_to_panel()  # update params to gui

        dlg.Destroy()

    def on_write_params_as( self, event ):
        dlg = wx.FileDialog( self, "Choose a file to write", 
                             os.getcwd(), "", "*", 
                             wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.read_params_from_panel()        # update params from gui
            self.write_params_to_file( path )

        dlg.Destroy()

    # override in subclass
    def read_params_from_panel( self ):
        print( 'op_panel: read_params_from_panel: do not call directly',
               file=sys.stderr )

    def save_image( self, path ):
        
        wximage =  self.display_image.ConvertToImage()
        pil = Image.new('RGB', (wximage.GetWidth(), 
                                wximage.GetHeight()))
        pil.frombytes( bytes(wximage.GetData()))
        pil.save( path )
        
    def on_save_image_as( self, event ):        
        dlg = wx.FileDialog( self, "Save image as...", 
                             os.getcwd(), "", "*", 
                             wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT )

        if dlg.ShowModal() == wx.ID_OK:
            self.save_image( dlg.GetPath() )            
        dlg.Destroy()

    def on_save_numpy_buffer_as( self, event ):        
        dlg = wx.FileDialog( self, "Save numpy buffer as...", 
                             os.getcwd(), "", "*", 
                             wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT )

        if dlg.ShowModal() == wx.ID_OK:
            self.sink.dump( dlg.GetPath() )            
        dlg.Destroy()

    def on_apply( self, event ):   # respond to apply click

        # report to message box
        self.messages.append ( '\n\tid:\t\t\t\t' + self.op_id + '\n' )

        self.b_apply.Enable( False )
        self.b_cascade.Enable( False )
        self.b_cancel.Enable( True )

        self.c_merge.Enable( False )
        self.b_options.Enable( False )

	# get parameter values from panel
        self.read_params_from_panel()

        '''
        # non-thread version
        self.apply_work()

        if ( self.sink.ndim == 2 ) :
            self.show_band( self.sink )
        else :
            self.show_band( self.sink[0] )

        self.finalize()
        '''

        text =  'processing ' + self.name
        self.report.SetLabel( text )

        # spawn processing thread
        self.app_cancelled = False     
        self.app_thread = apply_thread( self ) 
        self.app_thread.start()

        # spawn another thread to keep track of processing thread
        mon_thread = monitor_thread( self )
        mon_thread.start()

    def finalize( self ):               # clean up after a run
        self.b_apply.Enable( True )     # restore buttons
        self.b_cascade.Enable( True )
        self.b_cancel.Enable( False )
        self.b_options.Enable( True )

    # set up processing; called from app thread
    def apply_work( self ):           
        
        # get input image from a neighbor operator
        self.source = self.get_source( 1 )
        
        #if self.source == None:  # is neighbor sink image set?
        if type( self.source ) is not np.ndarray:

            print( 'op_panel:apply_work: ' + \
                   'neighbor sink (output) image not set',
                   file=sys.stderr )
            return

        self.set_areal_tags( 1 )        # inherit nav and band tags
        self.run()                      # run the operator
        
    def on_cascade( self, event ):      # respond to cascade click
        index = self.benchtop.op.index( self )    # discover our index 
        size = len(self.benchtop.op)    # how many ops are there?
        for i in range(index+1,size):
            self.benchtop.op[i].on_apply( None )
            
            # wait for thread to clean up
            while self.benchtop.op[i].app_thread.isAlive():
                time.sleep( 0.2 )

    def on_cancel( self, event ):       # kill processing

        # set internal flag to cancel
        self.app_cancelled = True       # app has to check this
                                        # for cancel to work
        self.messages.append( self.name + 
                              ' processing cancelled\n' )
        # wait for thread to clean up
        while self.app_thread.isAlive():
            time.sleep( 0.1)

    # trigger merging of three bands for color display
    def on_merge( self, event ):        # respond to merge checkbox
        if self.c_merge.GetValue():
            self.enable_color( True )
            self.s_band.Enable( False )
            self.l_tag.Enable( False )
            self.benchtop.pan_tools.settings.Enable( False )
            self.show_merged()
        else:
            self.enable_color( False )
            self.s_band.Enable( True )
            self.l_tag.Enable( True )
            self.benchtop.pan_tools.settings.Enable( True )
            self.show_band()

    def on_merge_apply( self, event ):  # respond to merge checkbox
        self.show_merged()

    def enable_color( self, toggle ):
        self.b_apply_merge.Enable( toggle );
        self.l_red.Enable( toggle )
        self.t_red.Enable( toggle )
        self.l_green.Enable( toggle )
        self.t_green.Enable( toggle )
        self.l_blue.Enable( toggle )
        self.t_blue.Enable( toggle )

    def on_spin( self, event ):         # band spinner

        if self.band_tags != None:
            index = self.s_band.GetValue()
            self.l_tag.SetLabel( self.band_tags[index] )

        self.show_band()
        event.Skip()

    # this gets called when processing is done
    # or when redisplay is requested
    def show_image( self ):

        #if self.sink == None:
        if type(self.sink) is not np.ndarray:
            return

        # easiest first
        
        #if self.overlay_image == None:
        if type(self.overlay_image) is not np.ndarray:
            self.display_overlay_image = None
        else:
            self.display_overlay_image = self.render_overlay_bmp(self.overlay_image)

        nbands = self.sink.shape[2]           # set spinner maximum
        current_band = self.s_band.GetValue() # get band value from spinner

        # check if spinner band is out of bounds (in case of new image)
        if current_band > (nbands-1):
            self.s_band.SetValue( 0 )

            if self.band_tags != None:
                self.l_tag.SetLabel( self.band_tags[0] )

        self.s_band.SetRange( 0, nbands-1 )
         
        if nbands > 2 :        # enable merge if at least 3 bands
              
            # enable checkbox
            self.c_merge.Enable( True )
            if not self.c_merge.GetValue():
                self.s_band.Enable( True )
                self.l_tag.Enable( True )
              
            # check if rgb bands ok
            value = self.t_red.GetValue()
            if int(value)  >= nbands:
                self.t_red.SetValue( '0' )

            value = self.t_red.GetValue()
            if int(value)  >= nbands:
                self.t_red.SetValue( '1' )

            value = self.t_red.GetValue()
            if int(value)  >= nbands:
                self.t_red.SetValue( '2' )    
        else:
            self.enable_color( False )
            self.c_merge.SetValue( False )
            self.c_merge.Enable( False )
            if nbands == 2:
                self.s_band.Enable( True )
                self.l_tag.Enable( True )
            else:
                self.s_band.Enable( False )            
                self.l_tag.Enable( False )
        
	# display image according to merge check box
        if self.c_merge.GetValue():
            self.show_merged()     # merge three bands for color
        else:
            self.show_band();      # display just one band
	
    # show the specified band in spinner
    def show_band( self ):

        # create display image
        height,width,nbands = self.sink.shape
        image = np.empty( (height,width,1), dtype=np.uint8 )

        # get current band value from spinner
        index = self.s_band.GetValue()

        # check if source data type is byte
        if self.sink.dtype == np.uint8:
            image[:,:,0] = self.sink[:,:,index]  # use view directly
        else:
            image[:,:,0] = self.recast_band( self.sink[:,:,index] )

        self.hist,edges = np.histogram( image, 256, (0.0,255.0) ) 
        self.hist.shape = 1, len(self.hist) # reshape to 1-band, 255

        # make it a bmp
        self.display_image = self.render_bmp( image )
        self.set_thumb_image()         # construct the thumb (pan) image
        
        # let benchtop distribute data
        # start new registry index if areal_index = None
        self.benchtop.set_images( self, self.areal_index )  

    # convert single-banded image to byte datatype for display
    def recast_band( self, image ):
        min = np.nanmin(image)         # get values to scale by
        max = np.nanmax(image)         # ignoring nan

        if max == min :                # check for constant values
            scale = 0.0 	       # make image a surface plane
            c = 0.0
        else:
            # TODO: handle min=-inf,max=inf
            if np.isinf( min ):
                print( min, file=sys.stderr )

            if np.isinf( max ):
                print( max, file=sys.stderr )

            scale = 255.0/(max-min)    # plain stretch to 8-bit range
            c = -scale*min

        # supply our own resultant array of byte type
        height,width = image.shape
        b_image = np.empty( (height,width), dtype=np.uint8 )

        '''
        b_image = (image*scale).astype( np.uint8 )
        b_image = (b_image + c).astype( np.uint8 )
        '''

        # FIXME: this returns float32 type but still works
        b_image = image*scale
        b_image = b_image + c

        return b_image

    # end recast_band

    # merge three bands into a color display
    def show_merged( self ):

        # get band values from band view panel
        r = int( self.t_red.GetValue() )
        g = int( self.t_green.GetValue() )
        b = int( self.t_blue.GetValue() )

        # check band bounds
        height,width,nbands = self.sink.shape
        if  r >= nbands or r < 0 or \
            g >= nbands or g < 0 or \
            b >= nbands or b < 0 :
            print( 'op_panel:show_merge: image band is out of bounds',
                   file=sys.stderr )
            return

        # setup output
        sorted_image = np.empty( (height,width,3),  dtype=np.uint8 )
        
        # check if data type is byte
        if self.sink.dtype == np.uint8:

            # use view directly
            sorted_image[:,:,0] = self.sink[:,:,r]
            sorted_image[:,:,1] = self.sink[:,:,g]
            sorted_image[:,:,2] = self.sink[:,:,b]
        else:
            sorted_image[:,:,0] = self.recast_band( self.sink[:,:,r] )
            sorted_image[:,:,1] = self.recast_band( self.sink[:,:,g] )
            sorted_image[:,:,2] = self.recast_band( self.sink[:,:,b] )
            
        # make it a wx bmp
        self.display_image = self.render_bmp( sorted_image )
        self.set_thumb_image()   # construct the thumb (pan) image

        # 3-band histogram
        self.hist = np.empty( (3,256), dtype=np.int32 )
        for i in range(0,3):
            hist, edges = np.histogram( sorted_image[:,:,i], 256, (0.0,255.0))
            self.hist[i] = hist

        # let benchtop distribute images;  start new registry index        
        self.benchtop.set_images( self, self.areal_index )  

    # create a thumb panner image
    def set_thumb_image( self ):
        if self.display_image == None:
            return

        # get thumb (panner) panel dimensions
        p_width, p_height = self.benchtop.pan.get_inner_size()
        max_size = float( p_width )   # make it float for factor 

        # calculate scale for thumb image
        width,height = self.display_image.GetSize()

        if  width >= height:
            factor = max_size/width;
        else:
            factor = max_size/height;

        # calculate size of thumb image
        height = int(height*factor)
        width = int(width*factor)
        
        image = self.display_image.ConvertToImage()
        image = image.Scale(width, height)
        #self.thumb_image = wx.BitmapFromImage( image )
        self.thumb_image = wx.Bitmap( image )

    # render into bmp format
    def render_bmp( self, image ):
        height,width,nbands = image.shape
        #bmp = wx.EmptyBitmap( width, height, 24 )
        bmp = wx.Bitmap( width, height, 24 )

        if nbands == 1:
            #if self.lut == None: # enlarge ~1s faster than wedge lut
            if type( self.lut ) is not np.ndarray:
                rgb = self.enlarge( image, 3, 1 )
            else:
                # run image through lut 
                rgb = self.lut[ image ]  # just indexing
 
            bmp.CopyFromBuffer( rgb.tostring() )
        else:
            bmp.CopyFromBuffer( image.tostring() ) # true color

        return bmp

    # render overlay image into bmp format
    def render_overlay_bmp( self, image ):
        height,width,nbands = image.shape
        #bmp = wx.EmptyBitmap( width, height, 32 )
        bmp = wx.Bitmap( width, height, 32 )

        if nbands != 4:
            print( 'render_overlay_bmp: image must be RGBA', file=sys.stderr )
            return

        bmp.CopyFromBuffer( image.tostring(),format=wx.BitmapBufferFormat_RGBA )
        return bmp

    def enlarge( self, a, x=2, y=None ):     # replicate bands
        if y == None:
            y=x                              # do same for y dimension

        return a.repeat(y, axis=0).repeat(x, axis=1)

    def report_image( self, image ):        
        height,width,nbands = image.shape
        self.messages.append( '\tnum bands:\t\t' + str(nbands) + '\n' )
        self.messages.append( '\tdimensions:\t' )
        self.messages.append( str(width) + ' x ' + str(height) + ' pixels\n' )
        self.messages.append( '\tdata type:\t\t' + str(image.dtype) + '\n' )
