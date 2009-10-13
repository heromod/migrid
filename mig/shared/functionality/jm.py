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

from shared.parseflags import all, long_list, recursive
from shared.validstring import valid_user_path
from shared.init import initialize_main_variables, find_entry
from shared.functional import validate_input_and_cert
import shared.returnvalues as returnvalues
from shared.settings import load_settings
from shared.useradm import client_id_dir

def html_tmpl():
    
    test =  """    
    <div>
      <div class="toolbar">        
        <div class="pager" id="pager">
        <form style="display: inline;">
          <img class="first" src="/images/icons/arrow_left.png"/>
          <img class="prev" src="/images/icons/arrow_left.png"/>
          <input type="text" class="pagedisplay" />
          <img class="next" src="/images/icons/arrow_right.png"/>
          <img class="last" src="/images/icons/arrow_right.png"/>
          <select class="pagesize">
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="25" selected>25</option>
            <option value="40">40</option>
            <option value="50">50</option>
            <option value="60">60</option>
            <option value="70">70</option>
            <option value="80">80</option>
          </select>
        </form>
        <div id="append"  style="display: inline;"><img src="/images/icons/arrow_refresh.png" /></div>
        </div>
        
      </div>
      <div class="stuff">
        <table id="jm_jobmanager">      
        <thead>
          <tr>
            <th>JobID</th>
            <th>status</th>
            <th>mRSL</th>
            <th>rStatus</th>
            <th>schedule</th>
            <th>date</th>
            <th>cancel</th>
            <th>liveoutput</th>
            <th>resubmit</th>
          </tr>        
        </thead>
        <tbody>
          <tr><td>JobID</td><td>status</td><td>mRSL</td><td>rStatus</td><td>schedule</td><td>date</td><td>cancel</td><td>liveoutput</td><td>resubmit</td></tr>          
        </tbody>
      </table>
      </div>
      
    </div>
        
    <ul id="job_context" class="contextMenu">        
        <li class="Show">
  <a href="#show">Resubmit</a>
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
      
        $(document).ready(
            function() {
              $("table")
              .tablesorter({widgets: ['zebra']})
              .tablesorterPager({container: $("#pager"), size: 300});
              
              $("#append").click(function() { 
                  
                  $('table tbody').html('');
                  
                  // add some html      
                  $.getJSON('jobstatus.py?output_format=json', {}, function(jsonRes, textStatus) {
                  
                    var jobList = new Array();
                    var i =0;
                    
                    // Grab jobs from json response and place them in jobList.
                    for(i=0; i<jsonRes.length; i++) {
            if (jsonRes[i].object_type == 'job_list') {    
              jobList = jobList.concat(jsonRes[i].jobs);
            }
        }
  
        $.each(jobList, function(i, item) {

            $('table tbody').append('<tr>'+
               '<td>'+item.job_id+'</td>'+
               '<td>'+item.status+'</td>'+
               '<td><a href="'+item.mrsllink.destination+'">mRSL</a></td>'+
               '<td><a href="'+item.statuslink.destination+'">status</a></td>'+
               '<td><a href="'+item.jobschedulelink.destination+'">schedule</a></td>'+
               '<td>'+item.received_timestamp+'</td>'+
               '<td><a href="'+item.cancellink.destination+'">cancel</a></td>'+
               '<td><a href="'+item.liveoutputlink.destination+'">liveout</a></td>'+
               '<td><a href="'+item.resubmitlink.destination+'">resubmitlink</a></td>'+
               '</tr>'
               
               );
            
            // Inform tablesorter of new data
            var sorting = [[0,0]]; 
            $("table").trigger("update");       
            $("table").trigger("sorton",[sorting]); 

        });      
        
      });

  }); 

  $("table").trigger("update");       
  var sorting = [[0,0]]; 
  $("table").trigger("sorton",[sorting]);
        }); 

    </script>
    """
    return js

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
    
    status = returnvalues.OK
    
    title_entry = find_entry(output_objects, 'title')
    title_entry['text'] = 'Jobmanager'
    title_entry['javascript'] = js_tmpl()
    
    output_objects.append({'object_type': 'header', 'text': 'Jobmanager' })
    
    output_objects.append({'object_type': 'text', 'text': html_tmpl()})
    
    return (output_objects, status)