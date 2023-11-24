'''
@file palette.py
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
Panel class that that holds selection trees
'''

palette_copyright = 'palette.py Copyright (c) 2010-2024 Scott L. Williams, released under GNU GPL V3.0'

import wx

class palette( wx.Panel ):
    def __init__( self, parent ):
        wx.Panel.__init__( self, parent )

        # this is our tree
        self.tree = wx.TreeCtrl(self, 
                                style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT )

        # assign icons to tree components

        il = wx.ImageList( 16,16 )
        bitmap = wx.ArtProvider.GetBitmap( wx.ART_FOLDER, 
                                           wx.ART_OTHER, (16,16) )
        self.fldr_idx = il.Add( bitmap )
        bitmap = wx.ArtProvider.GetBitmap( wx.ART_FILE_OPEN, 
                                           wx.ART_OTHER, (16,16) )
        self.fldr_openidx =  il.Add( bitmap )
                           
        bitmap = wx.ArtProvider.GetBitmap( wx.ART_NORMAL_FILE, 
                                           wx.ART_OTHER, (16,16) )
        self.file_idx = il.Add( bitmap )       
        self.tree.AssignImageList( il )

        self.root = self.tree.AddRoot( "" )         # do not show root
        self.tree.SetItemData( self.root, None )  

        sizer = wx.BoxSizer()                  # put the tree in a sizer 
        sizer.Add( self.tree, 1, wx.EXPAND )   # for the panel to manage
        self.SetSizer( sizer )

    def sort_nodes( self ):
        self.tree.SortChildren( self.root )

    def add_tree_node( self, parent_node, item, flag ):
        if flag == "dir":
            new_item = self.tree.AppendItem( parent_node, item )
            self.tree.SetItemData( new_item, None )
            self.tree.SetItemImage( new_item, self.fldr_idx,
                                    wx.TreeItemIcon_Normal )
            self.tree.SetItemImage( new_item, self.fldr_openidx,
                                    wx.TreeItemIcon_Expanded )
        else:
            new_item = self.tree.AppendItem( parent_node, item )
            self.tree.SetItemData( new_item, item )
            self.tree.SetItemImage( new_item, self.file_idx,
                                    wx.TreeItemIcon_Normal )
        return new_item
