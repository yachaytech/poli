'''
@file pan_tools.py
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
Splitter window holding panner and tool windows
'''

pan_tools_copyright = 'pan_tools.py Copyright (c) 2010-2022 Scott L. Williams, released under GNU GPL V3.0'

import wx

from pan_zoom import panner
from tree_page import add_operator_suites
from tree_page import add_image_suites
from navigate import navigate
from settings import settings
from histogram import histogram

class pan_tools( wx.SplitterWindow ):    # create the pan and tools panels
    def __init__( self, benchtop ):
        self.benchtop = benchtop

        wx.SplitterWindow.__init__( self, benchtop )
                                    
        # set up pan_tools split windows
        self.pan = panner( self, benchtop )

        # ... and tools' own split panel
        self.tools = wx.SplitterWindow( self )

        self.SplitHorizontally( self.pan, self.tools )
        self.SetSashPosition( benchtop.UTIL_SIZE_X+1, True )
        self.SetMinimumPaneSize( 1 )

        # TODO: intercept sash changing to peg size of panel

        self.setup_trees()              # create tools split panels

        # populate tree panels with operators and images
        add_operator_suites( benchtop.operator_suites, 
                             self.op_suite_note,
                             benchtop.messages,
                             benchtop.op_note.insert_operator )

        add_image_suites( benchtop.image_suites,
                          self.image_suite_note,
                          benchtop.messages,
                          self.on_image_tree_select )

    # create the tools' split panels; 
    # one for utilities, one for package and image trees
    def setup_trees( self ) :

        # construct tabbed image and tree utilities panels
        self.util_panel = self.make_utilities( self.tools )
        trees = wx.SplitterWindow( self.tools )

        self.tools.SplitHorizontally( self.util_panel, trees )
        self.tools.SetSashPosition( 278, True )

        self.tools.SetMinimumPaneSize( 1 )

        # set up tree panels

        # operator (suite) trees
        op_tree = wx.Panel( trees )
        self.op_suite_note = wx.Notebook( op_tree, 
                                          style=wx.NB_BOTTOM )
        sizer = wx.BoxSizer()             
        sizer.Add( self.op_suite_note, 1, wx.EXPAND ) # for the panel to manage
        op_tree.SetSizer( sizer )

        # image (suite) trees
        image_tree = wx.Panel( trees )
        self.image_suite_note = wx.Notebook( image_tree, style=wx.NB_BOTTOM )
        sizer = wx.BoxSizer()                   
        sizer.Add( self.image_suite_note, 1, wx.EXPAND )
        image_tree.SetSizer( sizer )

        trees.SplitVertically( op_tree, image_tree )
        trees.SetSashPosition( self.benchtop.UTIL_SIZE_X/2, True )

        trees.SetMinimumPaneSize( 1 )

    # create a notebook of display image utilities
    def make_utilities( self, parent ):

        # create panel for goodies
        util_panel = wx.Panel( parent )

        # make the notebook
        utilities = wx.Notebook( util_panel )

        # add tabs

        self.nav = navigate( utilities, self.benchtop )
        utilities.AddPage( self.nav, 'nav' )

        self.hist = histogram( utilities )
        utilities.AddPage( self.hist, 'hist' )
   
        self.settings = settings( utilities, self.benchtop )
        utilities.AddPage( self.settings, 'settings' )

        sizer = wx.BoxSizer()                # put the notebook in a sizer 
        sizer.Add( utilities, 1, wx.EXPAND ) # for the panel to manage
        util_panel.SetSizer( sizer )

        return util_panel

    def on_image_tree_select( self, event ):
        tree = event.GetEventObject()
        item = event.GetItem()
        pathname = tree.GetItemData( item )

        if pathname == None:   # accidental click on branch node
            return

        index = self.benchtop.op_note.GetSelection() # current op        
        if index > -1 :
            self.benchtop.op[index].on_apply( pathname )
   
