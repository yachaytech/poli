'''
@file load_op_module.py
@author Scott L. Williams.
@package POLI
@section LICENSE

#  Copyright (C) 2020-2024 Scott L. Williams.

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
Keystone module for POLI; dynamically loads an operator module from a dirctory or zip file
'''
# TODO: make url compatible
# TODO: more efficient way?

load_op_module_copyright = 'load_op_module.py Copyright (c) 2010-2024 Scott L. Williams released under GNU GPL V3.0'

import os
import sys
import imp
import zipimport

# retrieve starting module for given package
def load_pack_module( package_path ):
    pathlist = [ package_path ] # only one path

    # parse package_path string to get ...
    module_name = os.path.basename( package_path )[:-5] # remove suffix: .pack

    try:
        # find the principal module in package
        f, filename, descrip = imp.find_module( module_name, pathlist )        
        try:
            return imp.load_module( module_name, f, filename, descrip )
        finally:
            if f:
                f.close()

    except Exception as e:  # TODO: find correct error exception
        print( 'load_pack_module: ', e, file=sys.stderr )
        
# retrieve starting module for a zip package
def load_zip_module( package_path ):

    # parse package_path string to get ...
    module_name = os.path.basename( package_path )[:-4]
    package_name = module_name

    try:

        # import zip package first
        importer = zipimport.zipimporter( package_path )
        package = importer.load_module( module_name )

        # import principal module
        return  importer.load_module( package_name + '/' + module_name)

    except zipimport.ZipImportError as e:
        print( e, file=sys.stderr )
