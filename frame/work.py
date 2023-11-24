#! /usr/bin/env /usr/bin/python3

'''
@file work.py
@author Scott L. Williams
@ package POLI
@ brief initiate the POLI grogram
@ section LICENSE

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
Launch point for POLI (Python On Line Imaging). 
'''

work_copyright = 'work.py Copyright (c) 2010-2024 Scott L. Williams ' + \
                 'released under GNU GPL V3.0'

import os
import wx
import sys

from benchtop import benchtop

class main_frame( wx.Frame ):    # frame container class for poli window
    def __init__(self): 
        if len( sys.argv ) > 1:  # check for project locator argument
            config_file = sys.argv[1]
        else:
            config_file = None
 
        if config_file != None : # check if file exists; exit if not
            if not os.path.isfile( config_file ) :
                print( 'poli: config file: ' + config_file + ' does not exist',
                       file=sys.stderr )
                print( 'exiting...', file=sys.stderr )
                sys.exit(1)

        wx.Frame.__init__( self, None, -1, "" )

        self.SetTitle( 'POLI - Python On Line Imaging' )

        rect = wx.ClientDisplayRect()    # get system screen size
        size_x = int(rect[2]/(3/2))         # 

        self.SetSize( (size_x,rect[3]) ) 
  
        # TODO: get parrot icon
        # self.SetIcon( wx.Icon('poli.ico', wx.BITMAP_TYPE_ICO))
        '''
        # build the menu bar
        file_menu = wx.Menu()   
        item = file_menu.Append( wx.ID_EXIT, text="&Quit" )
        self.Bind( wx.EVT_MENU, self.on_quit, item )

        # TODO: bind to quit X title bar
        menu_bar = wx.MenuBar()     
        menu_bar.Append( file_menu, "&File" )
        self.SetMenuBar( menu_bar )

        # responds to exit symbol x on frame title bar
        self.Bind( wx.EVT_CLOSE, self.on_close )
        '''
        #         self.build_menu()
        
        # setup frame scrolling
        self.scroller = wx.ScrolledWindow( self )
        self.scroller.SetScrollRate(1,1)
        self.scroller.EnableScrolling(True,True)
 
        # bring it all up
        self.benchtop = benchtop( self.scroller, config_file )
        self.benchtop.SetMinSize( (528, 546) )   # refer to benchtop layout
                                                 # for current size
        sizer = wx.BoxSizer()                    # put the panel in a sizer 
        sizer.Add( self.benchtop, 1, wx.EXPAND ) # for the frame to manage
        self.scroller.SetSizer( sizer )
              
        self.Bind( wx.EVT_SIZE, self.on_resize ) # bind resize event

    def on_resize( self, event ):
        size = self.GetClientSize()   # report frame size to benchtop 
        self.benchtop.layout( size )  # to resize itself
        self.scroller.SetSize( size )

        event.Skip()

    def on_close( self, event ):# really exit 

        # clean up before exiting
        #self.benchtop.finalize()
        event.Skip()

    def on_quit( self, event=None ):
        self.Close()         # exit application

if __name__ == '__main__':   # user entry point  
    app = wx.App()

    frame = main_frame()
    frame.Show()

    app.MainLoop()
