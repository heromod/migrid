#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# fm - Filemanager UI for browsing and manipulating files and folders.
#
# Copyright (C) 2003-2009  The MiG Project lead by Brian Vinter
#
# This file is part of MiG.
#
# MiG is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# MiG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# -- END_HEADER ---
#

"""Script to provide users with a means of listing files and directories in
their home directories.
"""

import os
import time
import glob
import stat
import simplejson as json

from shared.parseflags import all, long_list, recursive
from shared.validstring import valid_user_path
from shared.init import initialize_main_variables, find_entry
from shared.functional import validate_input_and_cert
import shared.returnvalues as returnvalues
from shared.settings import load_settings
from shared.useradm import client_id_dir

def html_tmpl():
    
    test =  """    
    <div id="fm_filemanager">
        <div class="fm_addressbar">
            <ul><li class="fm_path"><input type="text" value="/" readonly="readonly" /></li></ul>
        </div>
        <div class="fm_folders">		
        </div>
      
        <div class="fm_toolbar">
          <ul>
            <li>Bulk:&nbsp;</li>
            <li class="bulk cat"><a href="#">cat</a></li>
            <li class="bulk cat"><a href="#">head</a></li>
            <li class="bulk cat"><a href="#">tail</a></li>
            <li class="bulk cat"><a href="#">wc</a></li>
            <li class="bulk cat"><a href="#">stat</a></li>
            <li class="bulk cat"><a href="#">touch</a></li>
            <li class="bulk cat"><a href="#">truncate</a></li>
            <li class="bulk cat"><a href="#">rm</a></li>
            <li class="bulk cat"><a href="#">rmdir</a></li>
            <li class="bulk cat"><a href="#">submit</a></li>              
          </ul>
        </div>
        <div class="fm_files">&nbsp;</div>
        <div class="fm_statusbar">&nbsp;</div>    
    </div>
    
    <ul id="folder_context" class="contextMenu">
        <li class="mkdir separator">
            <a href="#mkdir">Make dir</a>
        </li>
        <li class="upload">
            <a href="#upload">Upload file</a>
        </li>
    </ul>
    
    <ul id="file_context" class="contextMenu">        
        <li class="Show">
            <a href="#show">Show</a>
        </li>
        <li class="edit">
            <a href="#edit">Edit</a>
        </li>
        <li class="delete separator">
            <a href="#delete">Delete</a>
        </li>
    </ul>
    
    """
    
    return test

def js_tmpl():
    
    js = """
    <script>

        $(document).ready( function() {
            $('#fm_filemanager').filemanager({  root: '/',
                                        connector: 'ls.py?flags=l;output_format=json',
                                        params: 'path',
                                        expandSpeed: 0,
                                        collapseSpeed: 0,
                                        multiFolder: false
                                        },
                                        function(file) { alert(file); }
                                    );

                                });
                                    
            
    
    </script>
    """
    return js

# Handler for ajax-call, this is a quick-and-very-dirty-simplejson hack    
def list(base, location):
    
    prefix_count    = len(base)
    relative_root   = location
    
    if location[:prefix_count] != base:
        location = base+location
    folders =[]
    files   =[]

    try:
        
        for f in os.listdir(location):            
            ff=os.path.join(location,f)
            
            if os.path.isdir(ff):
            
                folders.append({'name':f,
                        'size' : os.path.getsize(ff),
                        'ext' : os.path.splitext(ff)[1].replace('.',''),
                        'is_dir' : os.path.isdir(ff),
                        'parent': relative_root+f,
                        'create_time' : os.path.getctime(ff)})
            else:
                
                files.append({'name':f,
                        'size' : os.path.getsize(ff),
                        'ext' : os.path.splitext(ff)[1].replace('.',''),
                        'is_dir' : os.path.isdir(ff),
                        'parent': ff,
                        'create_time' : os.path.getctime(ff)})
        
    except Exception,e:
        folders.append({'name': 'Could not load directory: %s' % str(e),
                        'size':0,
                        'ext' : '',
                        'is_dir': True,
                        'parent': '/',
                        'create_time': 0});
        
    folders.sort()
    files.sort()
    return json.dumps(folders + files)
    

def signature():
    """Signature of the main function"""

    defaults = {'dir' : ['']}
    return ['', defaults]

def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(op_header=False)
    client_dir = client_id_dir(client_id)
    defaults = signature()[1]
    (validate_status, accepted) = validate_input_and_cert(
        user_arguments_dict,
        defaults,
        output_objects,
        client_id,
        configuration,
        allow_rejects=False,
        )
    if not validate_status:
        return (accepted, returnvalues.CLIENT_ERROR)
    
    # Please note that base_dir must end in slash to avoid access to other
    # user dirs when own name is a prefix of another user name

    base_dir = os.path.abspath(os.path.join(configuration.user_home,
                               client_dir)) + os.sep
    status = returnvalues.OK
    
    # Grab the POSTed parameter
    ajax_location = ''.join(accepted['dir'])
            
    if ajax_location == '':
        title_entry = find_entry(output_objects, 'title')
        title_entry['text'] = 'Filemanager'
        title_entry['javascript'] = js_tmpl()
        
        output_objects.append({'object_type': 'header', 'text': 'Filemanager' })
        
        output_objects.append({'object_type': 'html_form', 'text': html_tmpl()})
            
        return (output_objects, status)
    else:
        return ([{'object_type': 'html_form', 'text': list(base_dir, ajax_location)}], status)