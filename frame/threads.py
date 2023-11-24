'''
@file threads.py
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
Provide thread classes for POLI
'''

threads_copyright = 'Copyright (c) 2010-2024 Scott L. Williams, released under GNU GPL V3.0'

import time
import wx
from threading import Thread

# event id
myEVT_PROCESS_DONE_EVENT = wx.NewEventType()
EVT_PROCESS_DONE_EVENT = wx.PyEventBinder(myEVT_PROCESS_DONE_EVENT, 1)

class process_done_event( wx.PyEvent ) :
    def __init__( self, event_type, id ):
        wx.PyEvent.__init__( self, id, event_type )

        self.duration = 0.0

    def set_duration( self, duration ):
        self.duration = duration

class apply_thread( Thread ):
    def __init__ ( self, op_panel ):
        Thread.__init__( self )

        self.op_panel = op_panel
        self.benchtop = op_panel.benchtop

    def run ( self ):
        start =  time.time()             # start the clock
        self.op_panel.apply_work()       # process data
        duration = time.time()-start     # measure processing time, 
                                         # not display rendering time
        
        # send event to main loop that we're done.
        evt = process_done_event( myEVT_PROCESS_DONE_EVENT, 
                                  self.op_panel.GetId() )

        evt.set_duration( duration )
        wx.PostEvent( self.op_panel, evt )

class monitor_thread( Thread ):
    def __init__ ( self, op_panel ):
        Thread.__init__( self )
        self.op_panel = op_panel

    def run ( self ):

        report = self.op_panel.benchtop.report # report label
        thread = self.op_panel.app_thread      # processing thread

        counter = 21
        while thread.isAlive():


            if  counter > 20:
                text =  'processing ' + self.op_panel.name
                counter = 0

            # thread safe access to wx
            wx.CallAfter( report.SetLabel, text )

            counter += 1
            text = text + '.'
            time.sleep( 0.1 ); # refresh every tenth of a second
