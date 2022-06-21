'''
@file op_notebook.py
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
Operator notebook; holds the operator panels
'''

op_notebook_copyright = 'op_notebook.py Copyright (c) 2010-2022 Scott L. Williams, released under GNU GPL V3.0'

import wx
import sys
import wx.aui

from load_op_module import load_zip_module
from load_op_module import load_pack_module

class op_notebook( wx.aui.AuiNotebook ): 
    def __init__( self, parent, benchtop ):
        self.benchtop = benchtop

        wx.aui.AuiNotebook.__init__( self, parent,
                                     style=wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB )

        self.Bind( wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, 
                   self.on_active )

        self.Bind( wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSED, 
                   self.on_remove )

    def on_active( self, event ):           # notebook page changed
        index= event.GetSelection()
  
        if len(self.benchtop.op) == index:  # active event has been called 
            event.Skip()                    # before operator has been made
            return
  
        if self.benchtop.op[index].display_image == None: 
            self.benchtop.clear()           # remove vestige display
        else:
            # show the image and thumb
            self.benchtop.set_images( self.benchtop.op[index],
                                      self.benchtop.op[index].areal_index )
        event.Skip()

    def on_remove( self, event ):    # remove op page in notebook
        op = self.benchtop.op
        index = event.GetSelection() # op to remove
        #op[index].finalize()        # clean up before removing
                                     # FIX: why is op removed now?
                                     #      want to clean up before removing
        del op[index]                # delete operator from list
        index = self.GetSelection()  # new current op

        if index == -1:              
            self.benchtop.clear()    # remove vestige display 
            self.benchtop.pan_tools.settings.Enable( False )
        else:
            # show the image and thumb
            self.benchtop.set_images( op[index],
                                      op[index].areal_index )
        event.Skip()

    # dynamically load operator from path
    def insert_operator( self, event ):
        tree = event.GetEventObject()
        item = event.GetItem()
        pathname = tree.GetItemData( item )

        if pathname == None:    # accidental click on branch node
            return

        messages = self.benchtop.messages
        messages.append( '\noperator:\t\t' + pathname + '\n' )

        if pathname.endswith( '.zip'):
            op_module = load_zip_module( pathname )   

        elif pathname.endswith( '_pack'):
            op_module = load_pack_module( pathname )   

        else :
            messages.append( 
                '  wrong type of operator: must be "_pack" or ".zip"')
            return

        if op_module == None:
            print( 'could not load module ' + pathname, file=sys.stderr )
            return

        # instantiate the operator class 
        op_class = op_module.instantiate()
        op_class.init_panel( self.benchtop ) # initialize graphics

        # add page to notebook ...

        tabname = op_module.get_name()

        if len( self.benchtop.op ) == 0:     # check if first page
            self.AddPage( op_class, tabname )
            self.benchtop.op.append( op_class )
            return

        index = self.GetSelection()          # get current selection
        if index == -1 :                     # none selected; append
            self.AddPage( op_class, tabname )
            self.benchtop.op.append( op_class )
            return

        self.InsertPage( index+1, op_class, tabname )
        self.SetSelection( index+1 )
        self.benchtop.op.insert( index+1, op_class )

        self.benchtop.clear()

    # finalize is needed because when exiting poli the PAGE_CHANGED event
    # is fired, wanting to redraw images for each op_panel as they
    # terminated...and while doing this it also gives a c object removed
    # error when more than one operator is loaded
    def finalize( self ):

        # couldn't get Unbind or Disconnect to work
        # use heavy hammer
        #self.Destroy()
        pass
