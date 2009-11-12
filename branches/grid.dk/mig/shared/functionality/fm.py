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
    
    return  """    
    <div id="fm_filemanager">
        <div class="fm_addressbar">
            <ul><li class="fm_path"><input type="text" value="/" readonly="readonly" /></li></ul>
        </div>
        <div class="fm_folders">
            <ul class="jqueryFileTree">                
                <li class="directory expanded">
                    <a href="#">...</a>
                </li>
            </ul>
        </div>
        <div class="fm_files">
        
            <table id="fm_filelisting" cellspacing="0">
            <thead>
              <tr>
                <th>Name</th>
                <th style="width: 80px;">Size</th>
                <th style="width: 50px;">Type</th>
                <th style="width: 120px;">Date Modified</th>
              </tr>        
            </thead>
            <tbody>
            </tbody>
            </table>            
        
        </div>        
        <div class="fm_statusbar">&nbsp;</div>    
    </div>
    
    <ul id="folder_context" class="contextMenu">
        <li class="mkdir separator">
            <a href="#mkdir">Create Folder</a>
        </li>
        <li class="upload">
            <a href="#upload">Upload file</a>
        </li>
        <li class="copy separator">
            <a href="#copy">Copy</a>
        </li>
        <li class="paste">
            <a href="#paste">Paste</a>
        </li>
        <li class="delete">
            <a href="#rmdir">Delete Folder</a>
        </li>
        <li class="rename separator">
            <a href="#rename">Rename...</a>
        </li>
    </ul>
    
    <ul id="file_context" class="contextMenu">        
        <li class="show">
            <a href="#show">Show / Download</a>
        </li>
        <li class="edit">
            <a href="#edit">Edit</a>
        </li>
        <li class="copy separator">
            <a href="#copy">Copy</a>
        </li>
        <li class="paste">
            <a href="#paste">Paste</a>
        </li>
        <li class="delete">
            <a href="#rm">Delete</a>
        </li>
        <li class="rename separator">
            <a href="#rename">Rename...</a>
        </li>
        <li class="cat separator">
            <a href="#cat">cat</a>
        </li>
        <li class="head">
            <a href="#head">head</a>
        </li>
        <li class="tail">
            <a href="#tail">tail</a>
        </li>
        <li class="submit separator">
            <a href="#submit">submit</a>
        </li>        
    </ul>

    <div id="cmd_dialog" title="Command output" style="display: none;"></div>

    <div id="upload_dialog" title="Upload File" style="display: none;">
      <p>Please upload a file</p>      
      <form id="myForm">
      <fieldset>
        <label for="file">Password</label>
        <input type="file" name="file" id="file" value="" class="text ui-widget-content ui-corner-all" />
        <input type="submit" />
      </fieldset>
      </form>

    </div>
        
    <div id="mkdir_dialog" title="Create New Folder" style="display: none;">
    
      <form>
      <fieldset>
        <label for="name">Enter the new name:</label>
        <input type="text" name="name" id="mk_name" class="text ui-widget-content ui-corner-all" />
        
      </fieldset>
      </form>
    </div>
    
    <div id="rename_dialog" title="Rename" style="display: none;">
      <form>
      <fieldset>
        <label for="name">Enter the new name:</label>
        <input type="text" name="name" id="rn_name" class="text ui-widget-content ui-corner-all" />
        
      </fieldset>
      </form>
    </div>

    """

def js_tmpl(entry_path='/'):
    
    js = """
    <script>
        $.ui.dialog.defaults.bgiframe = true;
        $("#mkdir_dialog").dialog({ closeOnEscape: true, modal: true });
                
        $(document).ready( function() {
            $('#fm_filemanager').filemanager({
                                        root: '/',
                                        connector: 'ls.py?flags=f;output_format=json',
                                        params: 'path',
                                        expandSpeed: 0,
                                        collapseSpeed: 0,
                                        multiFolder: false
                                        },
                                        function(file) { alert(file); }
                                    );

                                });
                                
        $('#myForm').ajaxForm(function() { 
                alert("Thank you for your comment!"); 
            }); 
  
    </script>
    """
    return js
    
def signature():
    """Signature of the main function"""

    defaults = {'path' : ['']}
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
    
    status = returnvalues.OK
    
    entry_path = ''.join(accepted['path'])
    title_entry = find_entry(output_objects, 'title')
    title_entry['text'] = 'Filemanager'
    title_entry['javascript'] = js_tmpl(entry_path)        
    
    output_objects.append({'object_type': 'header', 'text': 'Filemanager' })
    
    output_objects.append({'object_type': 'html_form', 'text': html_tmpl()})
        
    return (output_objects, status)
