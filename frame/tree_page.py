'''
@file tree_page.py
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
Configure tree pages (operators and images)
'''

tree_page_copyright = 'Copyright (c) 2010-2022 Scott L. Williams, released under GNU GPL V3.0'

import os
import wx
import sys
import urllib.request, urllib.parse, urllib.error

from palette import palette

# construct the operator suite tree
def add_operator_suites( suites, notebook, messages, event_func ):        
    if suites == None:
        return
        
    for suite in suites:      # read the suites

        name, locator = suite
        tree = op_page( name, locator, notebook )

        if tree != None:
            tree.Bind( wx.EVT_TREE_ITEM_ACTIVATED, 
                       event_func )             

            messages.append( '\toperator suite locator:\t' +
                             locator + '\tnamed\t' + name + '\n'  )

# create a page for an operator suite and populate
def op_page( name, suite, notebook ):

    # if it is networked it must be zipped
    if suite[:4] == 'http':

        if not suite.endswith( '.zip' ):
                
            print( 'networked file must be zipped: ' + suite, file=sys.stderr )
            return None

        # TODO: grab file and make local zip file in cache dir
        # call op_page again with local dir path and return tree instead of pass
        pass

    elif suite[:4] == 'file': # local file
        suite = suite[7:]
        return op_page( name, suite, notebook )   # try again

    if suite.endswith( '.zip' ):
        # TODO: unzip in cache dir and call ourselves
        pass

    page = palette( notebook )  # create a page for this suite
    populate_tree( page, suite, page.root )
    notebook.AddPage( page, name  )                 

    return page.tree  # return for event usage
        
# construct the image suite tree and populate
def add_image_suites( suites, notebook, messages, event_func ):        
    if suites == None:
        return
        
    for suite in suites:      # read the suites file
        
        name, locator = suite
        tree = image_page( name, locator, notebook )

        if tree != None:
            tree.Bind( wx.EVT_TREE_ITEM_ACTIVATED, 
                       event_func )        
    
            messages.append( '\timage suites locator:\t' +
                                  locator + '\tnamed\t' + name + '\n' )

# create a page for an image suite
def image_page( name, suite, notebook ):
    page = palette( notebook )  # create a page for this suite
    notebook.AddPage( page, name  )
  
    # check if networked
    if suite[:4] == 'http':
 
        # treat as dir only
        try:
            suite_dir = urllib.request.urlopen( suite + '/Publish' )
                        
        except IOError as e:
            print( 'add_suites error: ', file=sys.stderr )
            print( e, file=sys.stderr )
            return

        # set up dir node
        base = os.path.basename( suite )
        dir = page.add_tree_node( page.root, base, 'dir' )  
 
        for line in suite_dir:
            line = line.strip()
            path = suite + '/' + line
            put_node( page, dir, line, path )

    elif suite[:4] == 'file':
        populate_tree( page, suite[7:], page.root )

    else:
        populate_tree( page, suite, page.root )

    return page.tree  # return for event usage
        
def populate_tree( page, full_name, node ):
    node_name = full_name

    # intercept python packages
    if node_name.endswith( '_pack') or \
       node_name.endswith( '.zip') :             

        # send directly to node
        put_node( page, node, node_name, full_name )
          
    elif os.path.isdir( node_name ):

        base = os.path.basename( node_name )          # set up dir node
        dir = page.add_tree_node( node, base, 'dir' )
                        
        for file in os.listdir( node_name ):          # read dir files

            # reconstruct full path
            name = full_name + '/' + file    

            # check if this is another dir
            path = node_name + '/' + file   

            if os.path.isdir( path ):                   
                populate_tree( page, name, dir ) # tricky recursion
            else: 
                put_node( page, dir, file, name )

            page.tree.SortChildren( dir )

    else :
        put_node( page, node, node_name, full_name )

def put_node( page, dir, node_name, full_name ):
    node_name = os.path.basename( node_name )

    '''
    index = node_name.rfind( '.' )           # trim suffix for node display
    if index > 0:
        node_name = node_name[:index]
    '''

    if node_name.endswith( '_pack' ):
        node_name = node_name[:-5]
    if node_name.endswith( '.zip' ):
        node_name = node_name[:-4]

    item = page.add_tree_node( dir, node_name, "item" )
    page.tree.SetItemData( item, full_name )   # associate pathname with icon
