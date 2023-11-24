'''
@file logger.py
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
Logger to text ctrl panel and file
'''

logger_copyright = 'logger.py Copyright (c) 2010-2024 Scott L. Williams released under GNU GPL V3.0'

import wx
import sys

class logger( wx.TextCtrl ): 
    def __init__( self, parent ):
        wx.TextCtrl.__init__( self, parent,
                              style=wx.TE_MULTILINE | 
                              wx.TE_READONLY | wx.HSCROLL )
       
    def set_filename( self, name ):
        self.filename = name
        file = open( name, 'w' )    # start fresh
        file.close

    def append( self, text ):
        self.AppendText( text )     # write to panel

        # write text to log file
        try:
            file = open( self.filename, 'a' );
            file.write( text )
            file.close

        except IOError as e:
            print( e, file=sys.stderr )
  
