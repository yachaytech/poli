'''
@file oper_mess.py
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
Splitter window holding operator notebook and logger messages
'''

oper_mess_copyright = 'oper_mess.py Copyright (c) 2010-2024 Scott L. Williams, released under GNU GPL V3.0'

import wx
import time

from logger import logger
from op_notebook import op_notebook

class oper_mess( wx.SplitterWindow ): 
    def __init__( self, benchtop ):
        
        wx.SplitterWindow.__init__( self, benchtop )
                                    
        # create the operator panel and notebook
        oper_panel = wx.Panel( self )
        self.op_note = op_notebook( oper_panel, benchtop )
 
        sizer = wx.BoxSizer()                   # put the notebook in a sizer 
        sizer.Add( self.op_note, 1, wx.EXPAND ) # for the panel to manage
        oper_panel.SetSizer( sizer )

        # we'll add tabs (panels) dynamically later

        mess_panel = wx.Panel( self )           # create a logger

        self.messages = logger( mess_panel )
        self.messages.set_filename( 'poli.log' )

        # welcome message
        self.messages.append( 'welcome to poli:\t' + benchtop.version + '\n' )
        lt = time.localtime(time.time())
        time_stamp = "\t%04d.%02d.%02d %02d:%02d:%02d" %  \
                     (lt[0], lt[1], lt[2], lt[3], lt[4], lt[5])
        self.messages.append( '\tlocal time: ' + time_stamp + '\n' )

        # set up messages panel sizer
        box = wx.BoxSizer()
        box.Add( self.messages, proportion=1, border=0, flag=wx.EXPAND )
        mess_panel.SetSizer( box )
 
        if benchtop.proj_config == None :
            self.messages.append( '\tno configuration file given\n' )
        else:
            self.messages.append( '\tproject configure file:' )
            self.messages.append( '\t' + benchtop.proj_config + '\n' )

        self.SplitVertically( oper_panel, mess_panel )
        self.SetMinimumPaneSize( 1 )

