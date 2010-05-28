#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# submitjob - Job submission interfaces
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

"""Simple front end to job and file uploads"""

import os

import shared.returnvalues as returnvalues
from shared.defaults import any_vgrid
from shared.functional import validate_input_and_cert
from shared.init import initialize_main_variables, find_entry
from shared.mrslkeywords import get_job_specs
from shared.parser import parse_lines
from shared.refunctions import list_runtime_environments
from shared.settings import load_settings
from shared.useradm import mrsl_template, get_default_mrsl, client_id_dir
from shared.vgrid import user_allowed_vgrids
from shared.vgridaccess import user_allowed_resources
from shared.refunctions import list_0install_res

def signature():
    """Signature of the main function"""

    defaults = {'description': ['False']}
    return ['html_form', defaults]

def available_choices(configuration, client_id, field, spec):
    """Find the available choices for the selectable field.
    Tries to lookup all valid choices from configuration if field is
    specified to be a string variable.
    """
    if 'boolean' == spec['Type']:
        choices = [True, False]
    elif spec['Type'] in ('string', 'multiplestrings'):
        try:
            choices = getattr(configuration, '%ss' % field.lower())
        except AttributeError, exc:
            configuration.logger.error('%s' % exc)
            choices = []
    else:
        choices = []
    if not spec['Required']:
        choices = [''] + choices
    default = spec['Value']
    if default in choices:
        choices = [default] + [i for i in choices if not default == i]
    return choices

# html pieces for the file chooser
fm_layout =  '''
  <div id="debug"></div>
  <div id="fm_filechooser">
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
      <!-- this is a placeholder for contents: do not remove! -->
      </tbody>
      </table>            
    </div>        
    <div class="fm_statusbar">&nbsp;</div>    
  </div>
'''
fm_menus =  '''
<ul id="folder_context" class="contextMenu">
    <li class="select separator">
      <a href="#select">Select</a>
    </li>
    <li class="rename">
      <a href="#rename">Rename...</a>
    </li>
    <li class="mkdir">
      <a href="#mkdir">Create Folder</a>
    </li>
    <li class="upload">
      <a href="#upload">Upload File</a>
    </li>
  </ul>

  <ul id="file_context" class="contextMenu">        
    <li class="select separator">
      <a href="#select">Select</a>
    </li>
    <li class="rename">
      <a href="#rename">Rename...</a>
    </li>
  </ul>
'''
fm_dialogs =  '''
  <div id="cmd_dialog" title="Command output" style="display: none;"></div>

  <div id="upload_dialog" title="Upload File" style="display: none;">
  
    <form id="upload_form" enctype="multipart/form-data" method="post" action="textarea.py">
    <fieldset>
      <input type="hidden" name="output_format" value="json"/>
      <input type="hidden" name="max_file_size" value="100000"/>
      
      <label for="submitmrsl_0">Submit mRSL files (also .mRSL files included in packages):</label>
      <input type="checkbox" checked="" name="submitmrsl_0"/>
      <br />
      
      <label for="remotefilename_0">Optional remote filename (extra useful in windows):</label>
      <input type="text" value="./" size="50" name="remotefilename_0" />
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
'''

def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(client_id, op_header=False)
    client_dir = client_id_dir(client_id)
    status = returnvalues.OK
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

    show_description = accepted['description'][-1].lower() == 'true'

    # Please note that base_dir must end in slash to avoid access to other
    # user dirs when own name is a prefix of another user name

    base_dir = os.path.abspath(os.path.join(configuration.user_home,
                               client_dir)) + os.sep

    template_path = os.path.join(base_dir, mrsl_template)

    title_entry = find_entry(output_objects, 'title')
    title_entry['text'] = 'Submit Job'
    output_objects.append({'object_type': 'header', 'text'
                          : 'Submit Job'})
    default_mrsl = get_default_mrsl(template_path)
    settings_dict = load_settings(client_id, configuration)
    if not settings_dict or not settings_dict.has_key('SUBMITUI'):
        logger.info('Settings dict does not have SUBMITUI key - using default'
                    )
        submit_style = configuration.submitui[0]
    else:
        submit_style = settings_dict['SUBMITUI']

    # We generate all 3 variants of job submission (fields, textarea, files),
    # initially hide them and allow to switch between them using js.

    # could instead extract valid prefixes as in settings.py
    # (means: by "eval" from configuration). We stick to hard-coding.
    submit_options = ['fields_form', 'textarea_form', 'files_form']
    simple_view_fields = ["EXECUTE", "INPUTFILES", "OUTPUTFILES"]
    # read the zero install packages
    zeroinstall_run_envs = list_0install_res(configuration).keys()
    
    title_entry['javascript'] = '''
<link rel="stylesheet" type="text/css" href="/images/css/jquery.managers.css" media="screen"/>
<link rel="stylesheet" type="text/css" href="/images/css/jquery.contextmenu.css" media="screen"/>
<link rel="stylesheet" type="text/css" href="/images/css/jquery-ui-1.7.2.custom.css" media="screen"/>

<script type="text/javascript" src="/images/js/jquery-1.3.2.min.js"></script>
<script type="text/javascript" src="/images/js/jquery-ui-1.7.2.custom.min.js"></script>
<script type="text/javascript" src="/images/js/jquery.form.js"></script>
<script type="text/javascript" src="/images/js/jquery.prettyprint.js"></script>
<script type="text/javascript" src="/images/js/jquery.filemanager.js"></script>
<script type="text/javascript" src="/images/js/jquery.tablesorter.js"></script>
<script type="text/javascript" src="/images/js/jquery.tablesorter.pager.js"></script>
<script type="text/javascript" src="/images/js/jquery.contextmenu.js"></script>

<script type="text/javascript">
  
    $.ui.dialog.defaults.bgiframe = true;

    // global var for opening the dialog
    var open_chooser = function() {alert("Error: no handler installed");}

    // for switching between different submit options:
    var options = %(submit_interfaces)s;
    
    // zero install runtime environments
    var zeroinstall_RTE = %(runtime_environments)s;
    
    // the default submission fields to be shown
    var simple_view = %(default_fields)s;

    function switchTo(name) {

        for (o=0; o < options.length; o++) {
            if (name == options[o]) {
                $( "#" + name ).show();
            } else {
                $( "#" + options[o] ).hide();
            }
        }
    }

    function update_re(jobtype){
        $("select[name=RUNTIMEENVIRONMENT] option").show();
        
        if ("arc"==jobtype){
            $("select[name=RUNTIMEENVIRONMENT] option").filter(
                function(){
                    return (zeroinstall_RTE.indexOf($(this).val())==-1);
                }
            ).hide();
        }
    }
    
    function show_fields(fields){
        $(".job_fields").filter(
            function(){
                return (fields.indexOf($(this).attr("id")) != -1);
            }).show();
    }

    $(document).ready( function() {
         // submit style display
         switchTo("%(selected_style)s");
                
         // file chooser initialisation and bindings:

         open_chooser = mig_filechooser_init(
              "fm_filechooser", function(file) { return; }, true );
         // we add specific callbacks/handlers in more scripts below
          
        // hide all fields at first
        $(".job_fields").hide(); 
        // make sure the default fields are always shown
        show_fields(simple_view); 
    
    // When the job type is changed we update the RE options
     $("select[name=JOBTYPE] option").click(
        function(){
            update_re($(this).val());
        }
     );
     
    $("#advanced").hover(
        function(){
            $(this).css('cursor','pointer');
            //$(this).css({"color":"red"});
            $(this).css({"font-size":"101%%"});
        },
        function(){
            $(this).css('cursor','pointer');
            //$(this).css({"color":"black"});
            $(this).css({"font-size":"100%%"});
        }
    );
    $("#advanced").toggle(
        function () {
            $(this).html("<b><u>Show less options</u></b>");
            $(".job_fields").show();
            //show_fields(simple_view);
            },
        function () {
            $(this).html("<b><u>Show more options</u></b>");
            $(".job_fields").hide();
            show_fields(simple_view);
            }
        );
      
    
     // launch the file chooser                           
    $( ".file_chooser" ).click( function() {
        
        var field = $(this).attr("field");
        // we define the callback function to contain the value of the field we eventually wish to update
        var callback = function(path) {
                                $("textarea#"+field).append(path + "\\n");
                                };
        open_chooser("Select "+$(this).attr("name"),
                             callback, false);
          });
    });      
    
</script>
''' % {"submit_interfaces": submit_options, "runtime_environments":zeroinstall_run_envs, "selected_style":submit_style + "_form", "default_fields":simple_view_fields}

    # file chooser dialog elements, will be hidden by document.ready handler

    output_objects.append({'object_type': 'html_form',
                           'text': fm_layout + fm_menus + fm_dialogs })

    # visible content starts here

    output_objects.append({'object_type': 'text',
                           'text': 'This page is used to submit jobs to the grid.'})

    output_objects.append({'object_type': 'verbatim',
                           'text': '''
There are %s interface styles available that you can choose among:''' % \
                           len(submit_options)})

    links = []
    for opt in submit_options:
        name = opt.split('_',2)[0] 
        links.append({'object_type': 'link', 
                      'destination': "javascript:switchTo('%s')" % opt,
                      'class': 'submit%slink' % name,
                      'title': 'Switch to %s submit interface' % name,
                      'text' : '%s style' % name,
                      })
    output_objects.append({'object_type': 'multilinkline', 'links': links})

    output_objects.append({'object_type': 'text', 'text': '''
Please note that changes to the job description are *not* automatically
transferred if you switch style.'''}) 

    output_objects.append({'object_type': 'html_form', 
                           'text': '<div id="fields_form" style="display:none;">\n'})
    
    # Fields
    output_objects.append({'object_type': 'sectionheader', 'text'
                          : 'Please fill in your job description in the fields below:'
                          })
    output_objects.append({'object_type': 'text', 'text'
                          : """
Please fill in one or more fields below to define your job before hitting
Submit Job at the bottom of the page.
Empty fields will simply result in the default value being used and each field is
accompanied by a help link providing further details about the field."""})
    output_objects.append({'object_type': 'html_form', 'text'
                          : """
<table class="submitjob">
<tr><td class=centertext>
<form method="post" action="submitfields.py" id="miginput">
"""
                          })
    show_fields = get_job_specs(configuration)
    try:
        parsed_mrsl = dict(parse_lines(default_mrsl))
    except:
        parsed_mrsl = {}

    # Find allowed VGrids and Runtimeenvironments and add them to
    # configuration object for automated choice handling
    
    allowed_vgrids = user_allowed_vgrids(configuration, client_id) + [any_vgrid]
    allowed_vgrids.sort()
    configuration.vgrids = allowed_vgrids
    (re_status, allowed_run_envs) = list_runtime_environments(configuration)
        
    allowed_run_envs.sort()
            
    configuration.runtimeenvironments = allowed_run_envs

    user_res = user_allowed_resources(configuration, client_id)
    
    
    # Allow any exe unit on all allowed resources
        
    allowed_resources = ['%s_*' % res for res in user_res.keys()]
    allowed_resources.sort()
    configuration.resources = allowed_resources
    field_size = 30
    area_cols = 80
    area_rows = 5

    for (field, spec) in show_fields:
        title = spec['Title']
        if show_description:
            description = '%s<br />' % spec['Description']
        else:
            description = ''
        field_type = spec['Type']
        # Use saved value and fall back to default if it is missing
        saved = parsed_mrsl.get('::%s::' % field, None)
        if saved:
            if not spec['Type'].startswith('multiple'):
                default = saved[0]
            else:
                default = saved
        else:
            default = spec['Value']
        # Hide sandbox field if sandboxes are disabled
        if field == 'SANDBOX' and not configuration.site_enable_sandboxes:
            continue  
        if 'invisible' == spec['Editor']:
            continue
        if 'custom' == spec['Editor']:
            continue
        output_objects.append({'object_type': 'html_form', 'text'
                                   : """
<div class="job_fields" id='%(field)s'><b>%(title)s:</b>&nbsp;<a class='infolink 'href='docs.py?show=job#%(field)s'>help</a><br />
%(description)s""" % {"title":title, "field": field, "description":description}
                               })
        
        if 'input' == spec['Editor']:

            if -1 != title.find('Files'):
                # create file chooser dialog for it
                # all dialogs: append to textarea, prohibit directories 
                                   
                output_objects.append({'object_type': 'html_form',
                                   'text': '''
<a class="file_chooser" name="%(title)s" field="%(field)s">
   (Browse and select)</a><br/>
''' % {"title": title , "field": field}
                                   })                                   

            if field_type.startswith('multiple'):
                output_objects.append({'object_type': 'html_form', 'text'
                                       : """
<textarea id='%s' name='%s' cols='%d' rows='%d'>%s</textarea><br />
""" % (field, field, area_cols, area_rows, '\n'.join(default))
                               })
            else:
                output_objects.append({'object_type': 'html_form', 'text'
                                       : """
<input type='text' name='%s' size='%d' value='%s' /><br />
""" % (field, field_size, default)
                               })
        elif 'select' == spec['Editor']:
            choices = available_choices(configuration, client_id,
                                        field, spec)
            res_value = default
            if field_type.startswith('multiple'):
                multi_select = 'multiple'
            else:
                multi_select = ''
            value_select = ''
            value_select += "<select %s name='%s'>\n" % (multi_select, field)
            for name in choices:
                selected = ''
                if str(res_value) == str(name) or multi_select and str(name) in res_value:
                    selected = 'selected'
                value_select += """<option %s value='%s'>%s</option>\n""" % (selected, name, name)
            value_select += """</select><br />\n"""    
            output_objects.append({'object_type': 'html_form', 'text'
                                   : value_select
                                   })
        output_objects.append({'object_type': 'html_form', 'text': "<br /> </div>"})
    
    output_objects.append({'object_type': 'html_form', 'text'
                          : """
</td>
</tr>
<tr>
<td class=centertext>
<div id="advanced"><b><u>Show more options</u></b></div>
<br/>
</td>
</tr>
<tr>
<td class=centertext>
<input type="submit" value="Submit Job" />
</td>
</tr>
<tr>
<td class=centertext>
<input type="checkbox" name="save_as_default"> Save as default job template
</td>
</tr>
</form>
</table>
"""
                           })
    output_objects.append({'object_type': 'html_form', 
                           'text': '''
</div><!-- fields_form-->
<div id="textarea_form" style="display:none;">
'''})
    
    # Textarea
    output_objects.append({'object_type': 'sectionheader', 'text'
                          : 'Please enter your mRSL job description below:'
                          })
    output_objects.append({'object_type': 'html_form', 'text'
                          : """
<div class='smallcontent'>
Job descriptions can use a wide range of keywords to specify job requirements
and actions.<br />
Each keyword accepts one or more values of a particular type.<br />
The full list of keywords with their default values and format is available in
the on-demand <a href='docs.py?show=job'>mRSL Documentation</a>.
<p>
Actual examples for inspiration:
<a href=/cpuinfo.mRSL>CPU Info</a>,
<a href=/basic-io.mRSL>Basic I/O</a>,
<a href=/notification.mRSL>Job Notification</a>,
<a href=/povray.mRSL>Povray</a> and
<a href=/vcr.mRSL>VCR</a>
</div>
    """})

    output_objects.append({'object_type': 'html_form', 'text'
                          : """
<!-- 
Please note that textarea.py chokes if no nonempty KEYWORD_X_Y_Z fields 
are supplied: thus we simply send a bogus jobname which does nothing
-->
<table class="submitjob">
<tr><td class=centertext>
<form method="post" action="textarea.py" id="miginput">
<input type=hidden name=jobname_0_0_0 value=" " />
<textarea cols="82" rows="25" name="mrsltextarea_0">
%(default_mrsl)s
</textarea>
</td></tr>
<tr><td>
<center><input type="submit" value="Submit Job" /></center>
<input type="checkbox" name="save_as_default" >Save as default job template
</form>
</td></tr>
</table>
"""
                           % {'default_mrsl': default_mrsl}})

    output_objects.append({'object_type': 'html_form', 
                           'text': '''
</div><!-- textarea_form-->
<div id="files_form" style="display:none;">
'''})
    # Upload form

    output_objects.append({'object_type': 'sectionheader', 'text'
                          : 'Please upload your job file or packaged job files below:'
                          })
    output_objects.append({'object_type': 'html_form', 'text'
                          : """
<table class='files'>
<tr class=title><td class=centertext colspan=4>
Upload file
</td></tr>
<tr><td colspan=4>
Upload file to current directory (%(dest_dir)s)
</td></tr>
<tr><td colspan=2>
<form enctype='multipart/form-data' action='textarea.py' method='post'>
Extract package files (.zip, .tar.gz, .tar.bz2)
</td><td colspan=2>
<input type=checkbox name='extract_0' />
</td></tr>
<tr><td colspan=2>
Submit mRSL files (also .mRSL files included in packages)
</td><td colspan=2>
<input type=checkbox name='submitmrsl_0' checked />
</td></tr>
<tr><td>    
File to upload
</td><td class=righttext colspan=3>
<input name='fileupload_0_0_0' type='file' size='50'/>
</td></tr>
<tr><td>
Optional remote filename (extra useful in windows)
</td><td class=righttext colspan=3>
<input name='default_remotefilename_0' type='hidden' value='%(dest_dir)s'/>
<input name='remotefilename_0' type='text' size='50' value='%(dest_dir)s'/>
<input type='submit' value='Upload' name='sendfile'/>
</form>
</td></tr>
</table>
"""
                           % {'dest_dir': '.' + os.sep}})

    output_objects.append({'object_type': 'html_form', 
                           'text': '\n</div><!-- files_form-->'})
    return (output_objects, status)


