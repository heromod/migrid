#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# showvgridprivatefile - View VGrid private files for owners and members
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

"""Show the requested file located in a given vgrids private_base dir if the
client is an owner or a member of the vgrid. Members are allowed to read private
files but not write them, therefore they don't have a private_base link where
they can access them like owners do.
"""

import os
import time

import shared.returnvalues as returnvalues
from shared.functional import validate_input_and_cert, REJECT_UNSET
from shared.init import initialize_main_variables, find_entry
import shared.magic as magic
from shared.validstring import valid_user_path
from shared.vgrid import vgrid_is_owner_or_member


def signature():
    """Signature of the main function"""

    defaults = {'vgrid_name': REJECT_UNSET, 'path': REJECT_UNSET}
    return ['file_output', defaults]

# helpers for directory listing
def scale_bytes(bytes):

    """Scale bytes to an appropriate size, returning the scaled number
       and an appropriate suffix as one string for pretty printing"""

    # factors/letters have to be descending.

    factors = zip( [30,20,10], ['G','M','K'])

    for (k,s) in factors:

        x = bytes*1.0 / pow(2,k)
        if x > 1:

            return ( ("%.3f" % x) + ' ' + s+'B')

    # if not successful, we reach here. Return Bytes.

    return (str(bytes) + ' B')


# javascript to include for sorting
dir_js = '''
<script type="text/javascript" src="/images/js/jquery-1.3.2.min.js"></script>
<script type="text/javascript" src="/images/js/jquery.tablesorter.js"></script>

<style type="text/css">
table {
  background: #eef;
  color: #000;
  margin-right: auto;
  margin-left: auto;
  text-align: left;
  border: 1px solid #000;
}
// tablesorter...
#filetable .header { 
    background-image: url('/images/icons/small.gif'); 
    cursor: pointer; 
    font-weight: bold; 
    background-repeat: no-repeat; 
    background-position: center left; 
    padding-left: 20px; 
    border-right: 1px solid #dad9c7; 
    margin-left: -1px; 		
} 
#filetable .headerSortDown{ 
    background-image: url('/images/icons/asc.gif'); 
    background-repeat: no-repeat; 
    background-color: #3399FF; 
}
#filetable .headerSortUp { 
    background-image: url('/images/icons/desc.gif'); 
    background-repeat: no-repeat; 
    background-color: #3399FF; 
}
.odd {
  background-color: white;
}
.even {
  background-color: #ccc;
}
.sortkey { display:none; }
</style>

<script type="text/javascript" >

$(document).ready(function() {
          var getsortkey = function(contents) {
              var key = $(contents).find(".sortkey").text();
              if (key == null) {
                   key = $(contents).html();
              }
              return key;
          }
          $("#filetable").tablesorter({widgets: ["zebra"],
                                        sortList: [[0,0],[1,0]],
                                        textExtraction: getsortkey
                                       });
});
</script>
'''
    
def list_dir(filename, vgrid_name, rel_path):
    """ generate html table with directory listing"""

    if not os.path.isdir(filename):
        return ('Internal error: %s not a directory' % filename)

    html = '''
  <div style="text-align:center">
  <h3>%s: directory index of %s</h3>
  </div>
  <div style="text-align:center;margin-left:100px;margin-right:100px">
    <table id="filetable">
     <thead>
      <th style="text-align:left"><!-- symbol --></th>
      <th style="text-align:left">Name</th>
      <th style="width:120px; text-align:right">Size</th>
      <th style="width:200px; text-align:left">Last Modified</th>
     </thead>
     <tbody>
''' % (vgrid_name,rel_path)

    # always there: link to upper level
    html +='''
      <tr><td><img src="/images/icons/arrow_redo.png">
          <td><a href="/vgrid/%s/path/%s">
                 Up to higher level directory</a>
          <td><td></tr><tr/>
''' % (vgrid_name,os.path.dirname(rel_path.rstrip('/')) + '/')


    # read and sort file names
    contents = os.listdir(filename)
    contents.sort()

    for f in contents:
        # for file in dir: get info, print it...
        f_path = os.path.join(filename, f)
        link = "/vgrid/%s/path/%s" % \
               (vgrid_name, os.path.join(rel_path,f))
        info = os.stat(f_path)
        size = scale_bytes(info.st_size)
        #size = str(info.st_size)
        key  = 'file:' + f
        date = time.strftime("%Y-%m-%d %H:%M:%S",
                             time.localtime(info.st_mtime))
        type = magic.file(f_path)
        if os.path.isdir(f_path):
            type = 'directory'
            key  = 'dir:' + f
            size = '-'

        elif type.startswith('image/'):
            type = 'picture'
        elif type == 'text/html':
            type = 'html'
        elif type.startswith('text/') or type.startswith('message/'):
            type = 'txt'
        elif type.startswith('application/p'):
            type = 'pdf'
        elif type.endswith('zip') or type.endswith('zip2'):
            type = 'compress'
        elif type.startswith('application/octet'):
            type = 'computer'
        elif type.startswith('audio/') or type.startswith('video/'):
            type = 'music'
        else:
            type = 'file'

        html += '''
      <tr><td><img src="/images/icons/%s.png">
              <div class="sortkey">%s</div>
          <td><div class="sortkey">%s</div><a href="%s">%s</a>
      <td style="text-align:right"><div class="sortkey">%s</div>%s
      <td><div class="sortkey">%s</div>%s</tr>
''' % (type, key, f, link, f, size[-2:] + size, size, date, date)

    html += '''
     </tbody>
    </table>
</div>
'''
    return html

def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(client_id, op_header=False)
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

    vgrid_name = accepted['vgrid_name'][-1]
    path = accepted['path'][-1]
        
    if not vgrid_is_owner_or_member(vgrid_name, client_id,
                                    configuration):
        output_objects.append({'object_type': 'error_text', 'text':
                               '''You must be an owner or member of %s vgrid to
access the private files.''' % vgrid_name})
        return (output_objects, returnvalues.CLIENT_ERROR)

    # Please note that base_dir must end in slash to avoid access to other
    # user dirs when own name is a prefix of another user name

    base_dir = os.path.abspath(os.path.join(configuration.vgrid_private_base,
                                            vgrid_name)) + os.sep

    # Strip leading slashes to avoid join() throwing away prefix 

    rel_path = path.lstrip(os.sep)
    real_path = os.path.abspath(os.path.join(base_dir, rel_path))

    if not valid_user_path(real_path, base_dir, True):
        output_objects.append({'object_type': 'error_text', 'text':
                               '''You are not allowed to use paths outside vgrid
private files dir.'''})
        return (output_objects, returnvalues.CLIENT_ERROR)

    try:
        # analyse file contents using python-magic (own customised module)
        mime_type = magic.file(real_path)
    except Exception, exc:
        # default to plain text
        mime_type = 'text/plain'
    
    if mime_type == 'directory':

        # generate directory listing, include menu in page
        title = find_entry(output_objects, 'title')
        title['javascript'] = dir_js

        output_objects.append({'object_type': 'html_form',
                               'text': list_dir(real_path,vgrid_name,rel_path)
                               })
        return (output_objects, returnvalues.OK)

    # otherwise, normal file: serve the raw file with suitable mime type

    try:
        private_fd = open(real_path, 'rb')
        entry = {'object_type': 'binary',
                 'data': private_fd.read()}
        # Cut away all the usual web page formatting to show only contents
        output_objects = [{'object_type': 'start',
                           'headers': [('Content-Type',mime_type)]},
                          entry,
                          {'object_type': 'script_status'},
                          {'object_type': 'end'}]
        private_fd.close()
    except Exception, exc:
        output_objects.append({'object_type': 'error_text', 'text'
                              : 'Error reading VGrid private file (%s)'
                               % exc})
        return (output_objects, returnvalues.SYSTEM_ERROR)

    return (output_objects, returnvalues.OK)
