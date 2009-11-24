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
            <ul><li class="fm_path"><input type="text" value="/" name="fm_current_path" readonly="readonly" /></li></ul>
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
            <a href="#rm">Delete Folder</a>
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
    
        <form id="upload_form" enctype="multipart/form-data" method="POST" action="textarea.py">
        <fieldset>
            <input type="hidden" name="output_format" value="json"/>
            <input type="hidden" name="MAX_FILE_SIZE" value="100000"/>
            
            <label for="submitmrsl_0">Submit mRSL files (also .mRSL files included in packages):</label>
            <input type="checkbox" checked="" name="submitmrsl_0"/>
            <br />
            
            <label for="remotefilename_0">Optional remote filename (extra useful in windows):</label>
            <input type="input" value="./" size="50" name="remotefilename_0" />
            <br />
            
            <label for="extract_0">Extract package files (.zip, .tar.gz, .tar.bz2)</label>
            <input type="checkbox" name="extract_0"/>
            <br />
            
            <label for="fileupload_0_0_0">File:</label>
            <input type="file" name="fileupload_0_0_0"/>

        </fieldset>
        </form>

        <div id="upload_output"></div>

    </div>
        
    <div id="mkdir_dialog" title="Create New Folder" style="display: none;">
    
      <form id="mkdir_form" action="mkdir.py">
      <fieldset>
        <input type="hidden" name="output_format" value="json" />
        <input type="hidden" name="current_dir" value="./" />
        <label for="path">Enter the new name:</label>
        <input type="text" name="path"/>
        
      </fieldset>
      </form>
      <div id="mkdir_output"></div>
    </div>
    
    <div id="rename_dialog" title="Rename" style="display: none;">
    <form id="rename_form" action="mv.py">
    <fieldset>
    
      <input type="hidden" name="output_format" value="json" />
      <input type="hidden" name="flags" value="r" />
      <input type="hidden" name="src" value="" />
      <input type="hidden" name="dst" value="" />
      
      <label for="name">Enter the new name:</label>
      <input type="text" name="name" value="" />
      
    </fieldset>
    </form>
    <div id="rename_output"></div>
    </div>
    
    <div id="editor_dialog" title="Editor" style="display: none;">
    <form id="editor_form" action="editfile.py">
    <fieldset>

      <input type="hidden" name="output_format" value="json">

      <label for="path">Select file:</label>
      <input type="text" size="80" name="path" value=""><br />
      
      <label for="editarea">Edit contents:</label>
      <textarea cols="80" rows="20" wrap="off" name="editarea"></textarea>
      
      <label for="newline">Newline mode:</label>
      <select name="newline">
        <option selected value="unix">UNIX</option>
        <option value="mac">Mac OS (pre OS X)</option>
        <option value="windows">DOS / Windows</option>
      </select>
      
      <label for="name">Submit file as job after saving </label>
      <input type="checkbox" name="submitjob">
              
    </fieldset>
    </form>
    <div id="editor_output"></div>
    </div>

    """

def js_tmpl(entry_path='/'):
    
    js = """
    <script>
    
    $.ui.dialog.defaults.bgiframe = true;
            
    $(document).ready( function() {
    
      $('#fm_filemanager').filemanager({
                                        root: '/',
                                        connector: 'ls.py',
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
