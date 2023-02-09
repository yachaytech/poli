#! /usr/bin/env /usr/bin/python3

'''
@file wrf_source.py
@author Scott L. Williams
@package POLI
@brief A netCDF wrf data source POLI operator.
@LICENSE
#
#  Copyright (C) 2016-2022 Scott L. Williams.
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

# create a netCDF wrf data source
# XLAT and XLONG are automatically read into nav buffers
# NOTE: 4-D data not implemented, eg. T

wrf_source_copyright = 'wrf_source.py Copyright (c) 2016-2022 Scott L. Williams, released under GNU GPL V3.0'

import wx
import os
import sys
import getopt

import numpy as np
from osgeo import gdal

from threads import apply_thread
from threads import monitor_thread
from op_panel import op_panel

# return an instance of 'wrf_source' class 
# without having to know its name
def instantiate():	
    return wrf_source( get_name() )

def get_name(): 
    return 'wrf_source'

# clean up text after drop in filepath textctrl
class FileDrop( wx.FileDropTarget ):
    def __init__( self, window, op_panel ):
        wx.FileDropTarget.__init__(self)
        self.window = window
        self.op_panel = op_panel
        
    # url prefixes get removed as do trailing non-printables
    # just by running through this method; if not intercepted
    # url prefixes and non-printable characters appear
    def OnDropFiles( self, x, y, filenames ):
        try:
            self.window.SetValue( filenames[0] ) # use just the first name
            self.op_panel.on_apply( None )
        except:
            return False
        return True

class wrf_source_parameters():
    def __init__( self ):
        self.filepath = ''      # input netcdf file
        self.bandstr = ''       # bands to read in given as string
        self.tslice_band = -1.0 # if > -1.0 add band with that constant values.
                                # workaround for time input in SOM mplementation
                                # FIXME: hidden feature as it does not have a
                                # gui or command line parameter. consider making
                                # just a constant band, with negative values
                                
class wrf_source( op_panel ):          # image source operator

    def __init__( self, name ):        # initialize op_panel but no graphics
        op_panel.__init__( self, name )
        self.op_id = 'wrf_source version 0.0'
        self.params = wrf_source_parameters()
        gdal.PushErrorHandler( 'CPLQuietErrorHandler' ) # suppress warning
        
    def str2list( self, s ): 

        self.bufs = []
        self.tbands = []               # time bands
        self.lbands = []               # level bands
        items = s.split(',')          

        ''' Python 2.7
        t = [x.encode('ascii') for x in items]
        u = [x.replace(' ', '') for x in t] # clean up spaces
        '''
        
        u = [x.replace(' ', '') for x in items] # clean up spaces
        
        self.numbufs = len( u )
        for x in u:
            items = x.split(':')
            self.bufs.append( items[0] )
            self.tbands.append( int(items[1]) )
            try:
                self.lbands.append( int(items[2]) )
            except:
                self.lbands.append( 0 )
      
    def run( self ):                   # override superclass run

        # FIXME: gracefully return if error encountered
        #        and log to messages

        # FIXME: implement URL source

        self.source_name = self.params.filepath  # set op_panel's source name
        self.str2list( self.params.bandstr )

        # get number of time steps
        bufstr = 'NETCDF:"' + self.params.filepath + '":Times'
        try:
            gdal.PushErrorHandler( 'CPLQuietErrorHandler' ) # suppress warnings
            ds = gdal.Open( bufstr )
        except:
            print( 'cannot get dataset: Times', file=sys.stderr )
            return
        
        # does gdal return ds == None?
        if ds == None:
            print( 'cannot get dataset: Times', file=sys.stderr )
            return

        time_steps = ds.RasterYSize

        # grab data from wrf output
        self.band_tags = []
        for i in range(0,self.numbufs):

            bufstr = 'NETCDF:"' + self.params.filepath + '":' + self.bufs[i]
            try:
                ds = gdal.Open( bufstr )
            except:
                print( 'cannot get WRF dataset:', self.bufs[i],
                       file=sys.stderr )
                return

            # does gdal return ds == None?
            if ds == None:
                print( 'cannot get WRF dataset: '+ self.bufs[i],
                       file=sys.stderr )
                return


            # 4D arrays are represented as timesteps*3D arrays
            # because netcdf doesn't know how to handle
            # 4D arrays (x,y,z,t) where z represents height levels
            stride = ds.RasterCount/time_steps # will be 1 for 2D arrays

            if self.tbands[i] < 0 or self.tbands[i] >= time_steps:
                print( 'bad time index:', self.tbands[i], file=sys.stderr )
                return

            if self.lbands[i] < 0 or self.lbands[i] >= stride:
                print( 'bad height level index:', self.lbands[i], file=sys.stderr )
                return

            index = int( self.tbands[i]*stride + self.lbands[i] )
            data = ds.ReadAsArray()[ index ]

            # include vertical level, if available
            self.band_tags.append( self.bufs[i] + ':' + str(self.tbands[i]) )
            #                                   ':' + str(self.lbands[i]) ) # no levels implemented

            if i == 0:
                # save to compare later
                numy = data.shape[0]
                numx = data.shape[1]
                dtype = data.dtype 

                if self.params.tslice_band > -1.0:
                    self.sink = np.empty( (numy,numx,self.numbufs+1), dtype=dtype )
                else:
                    self.sink = np.empty( (numy,numx,self.numbufs), dtype=dtype )
            else:
                if numy != data.shape[0] or numx != data.shape[1]:
                    print( 'data shapes do not match:', file=sys.stderr )
                    return

                if dtype != data.dtype:
                    print( 'data type do not match', self.bufs[0], self.bufs[i],
                           file=sys.stderr )
                    return

            self.sink[:,:,i] = data

        if self.params.tslice_band > -1.0:
            # populate the buffer with a constant >= 0
            self.sink[:,:,self.numbufs] = self.params.tslice_band
            
            self.band_tags.append( 'time slice') # could be any constant
        
    ####################################################################
    # gui section
    ####################################################################

    # override on_apply to intercept event
    def on_apply( self, obj ):
        if isinstance(obj, str):             # we've been invoked by
            obj.strip()                      # image_tree
            self.t_filepath.SetValue( obj )            


        # report to message box
        self.benchtop.messages.append ( '\n\tid:\t\t\t\t' + 
                                        self.op_id + '\n' )
        self.b_apply.Enable( False )
        self.b_cascade.Enable( False )
        self.b_cancel.Enable( True )

        self.c_merge.Enable( False )
        self.b_options.Enable( False )

	# get parameter values from panel
        self.read_params_from_panel()
        self.benchtop.messages.append( '\tingesting:\t\t' + 
                                       self.params.filepath + '\n' )

        # spawn processing thread
        self.app_cancelled = False     
        self.app_thread = apply_thread( self ) 
        self.app_thread.start()

        # spawn another thread to keep track of app thread
        mon_thread = monitor_thread( self )
        mon_thread.start()

    # override since we are a source and need to handle
    # thread slightly different
    def apply_work( self ):
        self.run()          # run the operator

        #if self.sink == None:
        if type( self.sink ) is not np.ndarray:
            return

        # automatically read nav data
        bufstr = 'NETCDF:"' + self.params.filepath + '":XLAT'
        try:
            ds = gdal.Open( bufstr )
        except:
            print( 'cannot get dataset: XLAT', file=sys.stderr )
            return

        # determine XLAT has multiple buffers (orginal WRF output)
        # or if just one (filtered WRF output)
        data = ds.ReadAsArray()
        if len( data.shape ) == 3:
            data = data[0]
            
        numy, numx = data.shape
        dtype = data.dtype

        # we have shape, dtype make nav data buffer
        self.nav_data = np.empty( (numy,numx,2), dtype=dtype )
        self.nav_data[:,:,0] = data # load latitudes

        bufstr = 'NETCDF:"' + self.params.filepath + '":XLONG'
        try:
            ds = gdal.Open( bufstr )
        except:
            print( 'cannot get dataset: XLONG', file=sys.stderr )
            return
        
        # determine XLONG has multiple buffers (orginal WRF output)
        # or if just one (filtered WRF output). should be same as XLAT
        data = ds.ReadAsArray()
        if len( data.shape ) == 3:
            data = data[0]
 
        self.nav_data[:,:,1] = data # load longitudes
        self.nav_tags = ['lat', 'lon']

        self.center = True  # center image

    def read_params_from_panel( self ):       # scan panel parameters
        self.params.bandstr = self.t_bandstr.GetValue()
        self.params.filepath = self.t_filepath.GetValue()

    def write_params_to_panel( self ):        # write parameters to panel
        self.t_bandstr.SetValue( self.params.bandstr )
        self.t_filepath.SetValue( self.params.filepath )

    # initialize graphics
    def init_panel( self, benchtop ):
        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )

        #h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( self.p_client, -1, ' enter bands to read:   (0-index)' )
        v_sizer.Add( prompt ) 

        self.t_bandstr = wx.TextCtrl( self.p_client, -1 )
        self.t_bandstr.SetToolTip( 'comma delimited string for buffers; semi-colon delimited for time and level indices. eg POTEVP:20 gives 20th time PET band eg. P:4:20 gives pressure at 4th time-step and 20th height level. REMEMBER:0th indexed' )
        self.t_bandstr.Bind( wx.EVT_KEY_DOWN, self.on_file_key) 
        v_sizer.Add( self.t_bandstr, 1, wx.EXPAND )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        # file input text control
        prompt = wx.StaticText( self.p_client, -1, 
                                ' enter image filepath:' )
        h_sizer.Add( prompt )  # lower prompt
        v_sizer.Add( h_sizer )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.t_filepath = wx.TextCtrl( self.p_client, -1 )       
        self.t_filepath.SetToolTip( 'enter image filepath' )
        self.t_filepath.Bind( wx.EVT_KEY_DOWN, self.on_file_key ) 
        dt = FileDrop( self.t_filepath, self )
        self.t_filepath.SetDropTarget( dt )

        h_sizer.Add( self.t_filepath, 1, wx.EXPAND )

        # browse directory button
        b_browse = wx.Button( self.p_client, -1, 'browse', size=(60,25) )
        b_browse.Bind( wx.EVT_LEFT_UP, self.on_browse )             
        b_browse.SetToolTip( 'browse directory for image file' )

        h_sizer.Add( b_browse, 0 )

        v_sizer.Add( h_sizer, 1, wx.EXPAND )
        self.p_client.SetSizer( v_sizer )

        self.write_params_to_panel()
        
    # intercept keystroke; look for CR
    def on_file_key( self, event ):
        keycode = event.GetKeyCode()

        if keycode == wx.WXK_RETURN:   
            self.on_apply( None )    # as if pressing 'apply' button
        event.Skip()                 # pass along event

    # respond to file browse click
    def on_browse( self, event ):
        dlg = wx.FileDialog( self, 'Choose an image to read', 
                             os.getcwd(), "", "*", wx.OPEN )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            path = path.strip()
            self.t_filepath.SetValue( path ) # update filename to gui

        dlg.Destroy()

    ############################################################
    # command line options
    ############################################################

    def usage( self ):

        print( 'usage: projmod_source.py', file=sys.stderr )
        print( '       -h, --help', file=sys.stderr )
        print( '       -b bands, --bands=bands w/bands as string',
               file=sys.stderr )
        print( '       -f wrf_file, --file=wrf_file',
               file=sys.stderr )
        print( '       -p paramfile, --params=paramfile', file=sys.stderr )
        print( '       param file overrides line arguments', file=sys.stderr )

        print( '       input is filepath, output is stdout',
               file=sys.stderr )

    def set_params( self, argv ):
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hb:f:p:', 
                                        ['help','bands=', 'file=', 'params='])
        except getopt.GetoptError:           
            self.usage()              
            sys.exit(2)  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit(0)                  
            elif opt in ( '-f', '--file' ):
                self.params.filepath = arg    
            elif opt in ( '-b', '--bands' ):
                self.params.bandstr = arg
            elif opt in ( '-p', '--params' ):
                params = arg  

        if self.params.bandstr == '' and params == None:
            print( 'wrf_source:set_params: no band string given',
                   file=sys.stderr )
            self.usage()
            sys.exit(2 )
            
        if self.params.filepath == '' and params == None:    
            print( 'wrf_source:set_params: no filename given',
                   file=sys.stderr )
            self.usage()
            sys.exit( 2 )

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                print( 'wrf_source:set_params: bad params file read',
                       file=sys.stderr )
                sys.exit( 2 )

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':      
    oper = instantiate()                  # source point for pipe
    oper.set_params( sys.argv[1:] )
    oper.run()            
    oper.sink.dump( sys.stdout.buffer )   # send downstream    

