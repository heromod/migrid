#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# dashboard - Dashboard entry page backend
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

# See all_docs dictionary below for information about adding
# documentation topics.

"""Dashboard used as entry page"""

import os

import shared.returnvalues as returnvalues
from shared.functional import validate_input_and_cert
from shared.init import initialize_main_variables, find_entry


def signature():
    """Signature of the main function"""

    defaults = {}
    return ['text', defaults]


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

    title_entry = find_entry(output_objects, 'title')
    title_entry['text'] = 'Dashboard'

    # jquery support for tablesorter and confirmation on "leave":

    title_entry['javascript'] = '''
<link rel="stylesheet" type="text/css" href="/images/css/jquery.managers.css" media="screen"/>

<script type="text/javascript" src="/images/js/jquery-1.3.2.min.js"></script>

<script type="text/javascript" >

$(document).ready(function() {

          function roundNumber(num, dec) {
              var result = Math.round(num*Math.pow(10,dec))/Math.pow(10,dec);
              return result;
          }

          $("#jobs_stats").addClass("spinner").css("padding-left", "20px");
          $("#jobs_stats").html("Loading job stats...");
          $("#res_stats").addClass("spinner").css("padding-left", "20px");
          $("#res_stats").html("Loading resource stats...");
          $("#disk_stats").addClass("spinner").css("padding-left", "20px");
          $("#disk_stats").html("Loading disk stats...");
          $("#cert_stats").addClass("spinner").css("padding-left", "20px");
          $("#cert_stats").html("Loading certificate information...");
          /* Run jobs request in the background and handle as soon as results come in */
          $.getJSON("userstats.py?output_format=json;stats=jobs", {}, function(jsonRes, textStatus) {
            var i = 0;
            var jobs = null;
            // Grab results from json response and place them in job status.
            for(i=0; i<jsonRes.length; i++) {
                if (jsonRes[i].object_type == "user_stats") {    
                    jobs = jsonRes[i].jobs;
                    //alert("inspect stats result: " + jobs);
                    $("#jobs_stats").removeClass("spinner").css("padding-left", "0px");
                    $("#jobs_stats").html("");
                    $("#jobs_stats").append("You have submitted a total of " + jobs.total +
                    " jobs: " + jobs.parse + " parse, " + jobs.queued + " queued, " +
                    jobs.executing + " executing, " + jobs.finished + " finished, " + jobs.retry +
                    " retry, " + jobs.canceled + " canceled, " + jobs.expired + " expired and " +
                    jobs.failed + " failed.");
                    break;
                }
            }   

            });
          /* Run resources request in the background and handle as soon as results come in */
          $.getJSON("userstats.py?output_format=json;stats=resources", {}, function(jsonRes, textStatus) {
            var i = 0;
            var resources = null;
            // Grab results from json response and place them in resource status.
            for(i=0; i<jsonRes.length; i++) {
                if (jsonRes[i].object_type == "user_stats") {    
                    resources = jsonRes[i].resources;
                    //alert("inspect resources stats result: " + resources);
                    $("#res_stats").removeClass("spinner").css("padding-left", "0px");
                    $("#res_stats").html("");
                    $("#res_stats").append(resources.resources + " resources providing " +
                    resources.exes + " execution units in total allow execution of your jobs.");
                    break;
                }
            }
          });
          /* Run disk request in the background and handle as soon as results come in */
          $.getJSON("userstats.py?output_format=json;stats=disk", {}, function(jsonRes, textStatus) {
            var i = 0;
            var disk = null;
            // Grab results from json response and place them in resource status.
            for(i=0; i<jsonRes.length; i++) {
                if (jsonRes[i].object_type == "user_stats") {    
                    disk = jsonRes[i].disk;
                    //alert("inspect disk stats result: " + disk);
                    $("#disk_stats").removeClass("spinner").css("padding-left", "0px");
                    $("#disk_stats").html("");
                    $("#disk_stats").append("Your own " + disk.own_files +" files and " +
                    disk.own_directories + " directories take up " + roundNumber(disk.own_megabytes, 2) +
                    " MB in total and you additionally share " + disk.vgrid_files +
                    " files and " + disk.vgrid_directories + " directories of " +
                    roundNumber(disk.vgrid_megabytes, 2) + " MB in total.");
                    break;
                }
            }
          });
          /* Run certificate request in the background and handle as soon as results come in */
          $.getJSON("userstats.py?output_format=json;stats=certificate", {}, function(jsonRes, textStatus) {
            var i = 0;
            var certificate = null;
            // Grab results from json response and place them in resource status.
            for(i=0; i<jsonRes.length; i++) {
                if (jsonRes[i].object_type == "user_stats") {    
                    certificate = jsonRes[i].certificate;
                    //alert("inspect certificate stats result: " + certificate);
                    $("#cert_stats").removeClass("spinner").css("padding-left", "0px");
                    $("#cert_stats").html("");
                    $("#cert_stats").append("Your user certificate expires on " +
                    certificate.expire + ".");
                    break;
                }
            }
          });
     }
);
</script>
'''

    output_objects.append({'object_type': 'header', 'text': 'Dashboard'})
    output_objects.append({'object_type': 'sectionheader', 'text' :
                           "Welcome to the %s" % \
                           configuration.site_title})
    welcome_line = "Hi %(SSL_CLIENT_S_DN_CN)s" % os.environ
    output_objects.append({'object_type': 'text', 'text': welcome_line})
    dashboard_info = """
This is your private entry page or your dashboard where you can get a
quick status overview and find pointers to help and documentation.
When you are logged in with your user certificate, as you are now,
you can navigate your pages using the menu on the left.
""" % os.environ
    output_objects.append({'object_type': 'text', 'text': dashboard_info})

    output_objects.append({'object_type': 'sectionheader', 'text':
                           "Your Status"})
    output_objects.append({'object_type': 'html_form', 'text': '''
<p>
This is a general status overview for your Grid activities. Please note that some
of the numbers are cached for a while to keep server load down.
</p>
<p>
<div id="jobs_stats"><!-- for jquery --></div>
</p>
<p>
<div id="res_stats"><!-- for jquery --></div>
</p>
<p>
<div id="disk_stats"><!-- for jquery --></div>
</p>
<p>
<div id="cert_stats"><!-- for jquery --></div>
</p>
'''})

    output_objects.append({'object_type': 'sectionheader', 'text' :
                           'Documentation and Help'})
    online_help = """
%s includes some built-in documentation like the
""" % configuration.site_title
    output_objects.append({'object_type': 'text', 'text': online_help})
    output_objects.append({'object_type': 'link', 'destination': 'docs.py',
                           'class': 'infolink', 'title': 'built-in documentation',
                           'text': 'Documentation page'})
    project_info = """
but additional help, background information and tutorials are available in the
"""
    output_objects.append({'object_type': 'text', 'text': project_info})
    output_objects.append({'object_type': 'link', 'destination':
                           configuration.site_external_doc,
                           'class': 'urllink', 'title': 'external documentation',
                           'text': 'external %s documentation' % \
                           configuration.site_title})
    
    output_objects.append({'object_type': 'sectionheader', 'text' :
                           "Personal Settings"})
    settings_info = """
You can customize your personal pages if you like, by opening the Settings
page from the navigation menu and entering personal preferences. In that way you
can ease file and job handling or even completely redecorate your interface.
"""
    output_objects.append({'object_type': 'text', 'text': settings_info})

    #env_info = """Env %s""" % os.environ
    #output_objects.append({'object_type': 'text', 'text': env_info})

    return (output_objects, returnvalues.OK)


