#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# submitjob - Job submission interfaces
# Copyright (C) 2003-2014  The MiG Project lead by Brian Vinter
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
from shared.base import client_id_dir
from shared.defaults import any_vgrid, default_mrsl_filename
from shared.functional import validate_input_and_cert
from shared.init import initialize_main_variables, find_entry
from shared.mrslkeywords import get_job_specs
from shared.parser import parse_lines
from shared.refunctions import list_runtime_environments
from shared.settings import load_settings
from shared.useradm import get_default_mrsl
from shared.vgrid import user_allowed_vgrids
from shared.vgridaccess import user_allowed_res_exes


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

    template_path = os.path.join(base_dir, default_mrsl_filename)

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

    title_entry['javascript'] = '''
<link rel="stylesheet" type="text/css"
      href="/images/css/jquery.managers.css" media="screen"/>
<link rel="stylesheet" type="text/css"
      href="/images/css/jquery-ui.css" media="screen"/>
<link rel="stylesheet" type="text/css"
      href="/images/css/jquery.fileupload-ui.custom.css" media="screen"/>

<script type="text/javascript" src="/images/js/jquery.js"></script>
<script type="text/javascript" src="/images/js/jquery-ui.js"></script>
<script type="text/javascript" src="/images/js/jquery.iframe-transport.js">
</script>
<script type="text/javascript" src="/images/js/jquery.fileupload.js"></script>

<script type="text/javascript" >

    var url = "uploadchunked.py?output_format=json";
    var sequential = false;         
    var active_upload = false;
    var upload_paused = false;
    var resume_data = false;
    var move_dest = "";
    
    options = %s;

    function setDisplay(this_id,new_d) {
        el = document.getElementById(this_id)
        if ( el == undefined || el.style == undefined ) {
            return; // avoid js null ref errors
        }
        el.style.display=new_d;
    }

    function switchTo(name) {
        for (o=0; o < options.length; o++) {
            if (name == options[o]) {
                setDisplay(options[o],"block");
            } else {
                setDisplay(options[o],"none");
            }
        }
    }

    function toggleActions(ref) {
        active_upload = ref;
        if (ref == false) {
            disabled = true;
        } else {
            disabled = false;            
        }
        //console.log("toggling action buttons: "+disabled+" : "+active_upload);
        $("#actionbuttons").children("button").prop("disabled", disabled);
    }

    function pauseUpload() {
        /* fileupload does not include explicit pause/resume but we can abort
         and use the resume trick from:
         https://github.com/blueimp/jQuery-File-Upload/wiki/Chunked-file-uploads
         */
         /* TODO: implement properly */
        console.log("pause upload: "+active_upload+" "+upload_paused);
        if (active_upload == false) {
            console.log("no active upload to pause");
        } else if (upload_paused && resume_data) {
            console.log("resume active upload");
            upload_paused = false;
            console.log("TODO: resume from existing instead of restarting");
            resume_data.uploadedBytes = 0;
            resume_data.data = null;
            //console.log("resume data: "+resume_data.toSource());
            resume_data.submit();
            $("#pauseupload").text("Pause");
        } else {
            console.log("TODO: pause active upload");
            upload_paused = true;
            active_upload.abort();
            $("#pauseupload").text("Resume");
        }
    }

    function cancelUpload() {
        console.log("cancel upload: "+active_upload);
        if (active_upload == false) {
            console.log("no active upload to cancel");
        } else {
            active_upload.abort();
            console.log("cancel sent");
            upload_paused = false;
            resume_data = false;
            $("#pauseupload").text("Pause");
            toggleActions(false);
        }
    }

    function deleteUpload(name, dest_dir) {
        console.log("delete upload: "+name+" "+dest_dir);
        var deleted = false;
        $.ajax({
            url: url+";action=delete",
            dataType: "json",
            data: {"files[]filename": name, "files[]": "dummy",
                   "current_dir": dest_dir},
            type: "POST",
            async: false,
            success: function(data, textStatus, jqXHR) {
                console.log("delete success handler: "+name);
                console.log("data: "+data.toSource());
                $.each(data, function (index, obj) {
                    //console.log("delete result obj: "+index+" "+obj.toSource());
                    if (obj.object_type == "uploadfiles") {
                        //console.log("found files in obj "+index);
                        var files = obj.files;
                        $.each(files, function (index, file) {
                            console.log("found file entry in results: "+index);
                            if (file.error != undefined) {
                                console.log("found file error: "+file.error);
                            } else if (file[name]) {
                                console.log("found success marker: "+file[name]);
                                deleted = true;
                            }
                            return false;
                        });
                    }
                });
            }
        });
        //console.log("removing from uploadedfiles");
        $("#uploadedfiles > div:contains(\'(upload-cache)/"+name+"\')").remove();
        console.log("removed any matching entries from uploadedfiles");
        return deleted;
    }

    function moveUpload(name, dest_dir) {
        console.log("move upload: "+name+" to "+dest_dir);
        var moved = false;
        $.ajax({
            url: url+";action=move",
            dataType: "json",
            data: {"files[]filename": name, "files[]": "dummy",
                   "current_dir": dest_dir},
            type: "POST",
            async: false,
            success: function(data, textStatus, jqXHR) {
                console.log("move success handler: "+name);
                console.log("data: "+data.toSource());
                $.each(data, function (index, obj) {
                    //console.log("move result obj: "+index+" "+obj.toSource());
                    if (obj.object_type == "uploadfiles") {
                        //console.log("found files in obj "+index);
                        var files = obj.files;
                        $.each(files, function (index, file) {
                            console.log("found file entry in results: "+index);
                            if (file.error != undefined) {
                                console.log("found file error: "+file.error);
                            } else if (file[name]) {
                                console.log("found success marker: "+file[name]);
                                moved = true;
                            }
                            return false;
                        });
                    }
                });
            }
        });
        console.log("move status: "+moved);
        return moved;
    }

    function clearUploads() {
        console.log("clear uploads list");
        $("#uploadedfiles").empty();
        $("#recentupload").hide();        
    }

    function clearFailed() {
        console.log("clear failed uploads list");
        $("#failedfiles").empty();
        $("#recentfail").hide();
    }
    
    $(document).ready( function() {
         switchTo("%s");

         $("#globalprogress").progressbar({value: 0});
         $("#globalprogress > div").html("<span class=\'ui-progressbar-text\'>0%%</span>");
         toggleActions(false);
         $("#recentupload").hide();
         $("#recentfail").hide();
         $("#pauseupload").click(pauseUpload);
         $("#cancelupload").click(cancelUpload);
         $("#clearuploads").click(clearUploads);
         $("#clearfailed").click(clearFailed);

         $("#basicfileupload").fileupload({
             url: url+";action=put",
             dataType: "json",
             maxChunkSize: 8000000, // 8 MB
             sequentialUploads: sequential,
             maxRetries: 100,
             retryTimeout: 500,
             /*
             send: function (e, data) {
                 console.log("Send file");
             },
             */
             submit: function (e, data) {
                 //console.log("Submit file");
                 /* Tmp! we preserve pristine data here for resume from scratch */
                 resume_data = data;
                 move_dest = $("#basicfileuploaddest").val();
                 var $this = $(this);
                 $.each(data.files, function (index, file) {
                     console.log("Send file: " + file.name);
                 });
                 /* save reference to upload for pause/cancel to use */
                 var req = $this.fileupload("send", data).error(
                         function (ref, textStatus, errorThrown) {
                             if (errorThrown === "abort") {
                                 console.log("File upload was aborted");
                             } else {
                                 console.log("File upload failed: "+textStatus);
                             }
                     });
                 toggleActions(req);
                 /* Prevent duplicate native send */
                 return false;
             }, 
             progressall: function (e, data) {
                var progress = parseInt(data.loaded / data.total * 100, 10);
                $("#globalprogress").progressbar("option", "value", progress);
                $("#globalprogress > div > span.ui-progressbar-text").html(progress+"%%");
                console.log("progress is "+progress);
             },
             done: function (e, data) {
                 console.log("upload done");
                 resume_data = false;
                 $("#globalprogress").progressbar("option", "value",
                     $("#globalprogress").progressbar("option", "max"));
                 $("#globalprogress > div > span.ui-progressbar-text").html("100%%");
                 //console.log("results: "+data.result);
                 $.each(data.result, function (index, obj) {
                     //console.log("result obj: "+index+" "+obj.toSource());
                     if (obj.object_type == "uploadfiles") {
                         //console.log("found files in obj "+index);
                         var files = obj.files;
                         var upload_entry;
                         //console.log("found files: "+index+" "+files.toSource());
                         $.each(files, function (index, file) {
                             console.log("found file entry in results: "+index);
                             var dst = "(upload-cache)"
                             if (file.error != undefined) {
                                 console.log("found file error: "+file.error);
                                 $("#recentfail").show();
                                 $("#failedfiles").append(file.name+" ("+file.error+")<br />");
                                 deleteUpload(file.name);
                                 return false;
                             } else if (move_dest && moveUpload(file.name, move_dest)) {
                                 dst = move_dest;
                             }
                             $("#recentupload").show();
                             upload_entry = "<div>"+dst+"/"+file.name;
                             del_btn = "<button class=\'deletebutton\'>Delete</button>";
                             if (move_dest == "") {
                                 upload_entry += del_btn;
                             }
                             upload_entry += "</div>";
                             $("#uploadedfiles").append(upload_entry);
                             $("#uploadedfiles > div:contains(\'"+file.name+"\') > button").click(
                                 function() {
                                     deleteUpload(file.name, move_dest);
                                 });
                             //console.log("inserted upload entry: "+upload_entry);
                         });
                     }
                 });
                 /* clear active*/
                 toggleActions(false);
                 console.log("after done handling: "+$("#uploadedfiles"));
             },
             fail: function (e, data) {
                 if (upload_paused) {
                     console.log("upload paused");
                     /* TODO: extract actual resume data here */
                     //resume_data = data;
                 } else {
                     console.log("upload failed/cancelled");
                     resume_data = false;
                     $("#globalprogress").progressbar("option", "value",
                         $("#globalprogress").progressbar("option", "min"));
                     $("#globalprogress > div > span.ui-progressbar-text").html("0%%");
                     $("#recentfail").show();
                     $.each(data.files, function (index, file) {
                         $("#failedfiles").append(file.name+" ("+file.error+")<br />");
                         deleteUpload(file.name);
                     });
                 }
             }
         });

         $(document).bind("drop dragover", function (e) {
             e.preventDefault();
         });
             

    });

</script>
''' % (submit_options, submit_style + "_form")

    output_objects.append({'object_type': 'text', 'text':
                           'This page is used to submit jobs to the grid.'})

    output_objects.append({'object_type': 'verbatim',
                           'text': '''
There are %s interface styles available that you can choose among:''' % \
                           len(submit_options)})

    links = []
    for opt in submit_options:
        name = opt.split('_', 2)[0] 
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

    output_objects.append({'object_type': 'html_form', 'text':
                           '<div id="fields_form" style="display:none;">\n'})
    
    # Fields
    output_objects.append({'object_type': 'sectionheader', 'text'
                          : 'Please fill in your job description in the fields'
                           ' below:'
                          })
    output_objects.append({'object_type': 'text', 'text'
                          : """
Please fill in one or more fields below to define your job before hitting
Submit Job at the bottom of the page.
Empty fields will simply result in the default value being used and each field
is accompanied by a help link providing further details about the field."""})
    output_objects.append({'object_type': 'html_form', 'text'
                          : """
<table class="submitjob">
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
    
    allowed_vgrids = user_allowed_vgrids(configuration, client_id) + \
                     [any_vgrid]
    allowed_vgrids.sort()
    configuration.vgrids = allowed_vgrids
    (re_status, allowed_run_envs) = list_runtime_environments(configuration)
    if not re_status:
        logger.error('Failed to extract allowed runtime envs: %s' % \
                     allowed_run_envs)
        allowed_run_envs = []
    allowed_run_envs.sort()
    configuration.runtimeenvironments = allowed_run_envs
    user_res = user_allowed_res_exes(configuration, client_id)

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
<b>%s:</b>&nbsp;<a class='infolink' href='docs.py?show=job#%s'>help</a><br />
%s""" % (title, field, description)
                               })
        
        if 'input' == spec['Editor']:
            if field_type.startswith('multiple'):
                output_objects.append({'object_type': 'html_form', 'text'
                                       : """
<textarea name='%s' cols='%d' rows='%d'>%s</textarea><br />
""" % (field, area_cols, area_rows, '\n'.join(default))
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
            value_select = ''
            if field_type.startswith('multiple'):
                value_select += '<div class="scrollselect">'
                for name in choices:
                    # Blank default value does not make sense here
                    if not str(name):
                        continue
                    selected = ''
                    if str(name) in res_value:
                        selected = 'checked'
                    value_select += '''
                        <input type="checkbox" name="%s" %s value=%s>%s<br />
                        ''' % (field, selected, name, name)
                value_select += '</div>\n'
            else:
                value_select += "<select name='%s'>\n" % field
                for name in choices:
                    selected = ''
                    if str(res_value) == str(name):
                        selected = 'selected'
                    value_select += """<option %s value='%s'>%s</option>\n""" \
                                    % (selected, name, name)
                value_select += """</select><br />\n"""    
            output_objects.append({'object_type': 'html_form', 'text'
                                   : value_select
                                   })
        output_objects.append({'object_type': 'html_form', 'text': "<br />"})

    output_objects.append({'object_type': 'html_form', 'text'
                          : """
<tr>
<td><br /></td>
<td class=centertext>
<input type="submit" value="Submit Job" />
<input type="checkbox" name="save_as_default"> Save as default job template
</td>
<td><br /></td>
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
                          : 'Please upload your job file or packaged job files'
                           ' below:'
                          })
    output_objects.append({'object_type': 'html_form', 'text'
                          : """
<table class='files'>
<tr class=title><td class=centertext colspan=4>
Upload job files
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
<tr><td colspan=3>
<hr>
</td></tr>
<tr class=title><td class=centertext colspan=4>
Upload other files efficiently (using chunking).
</td></tr>
<tr><td colspan=2>
Upload file to upload cache with optional move to this destination dir:
</td><td class=righttext colspan=2>
<input id='basicfileuploaddest' type='text' size=60 value=''>
</td></tr>
<tr><td>    
File to upload
</td><td class=righttext colspan=3>
<input id='basicfileupload' type='file' name='files[]' multiple>
</td></tr>
<tr><td colspan=4>
<!-- The global progress bar area-->
<div id='uploadfiles' class='uploadfiles'>
<div id='globalprogress' class='uploadprogress'>
</div>
<div id='actionbuttons'>
<button id='pauseupload'>Pause/Resume</button>
<button id='cancelupload'>Cancel</button>
</div>
<br />
<div id='recentupload'>
<b>Recently uploaded files:</b> <button id='clearuploads'>Clear</button>
<div id='uploadedfiles'>
<!-- dynamically filled by javascript after uploads -->
</div>
</div>
<br />
<div id='recentfail'>
<b>Recently failed uploads:</b> <button id='clearfailed'>Clear</button>
<div id='failedfiles'>
<!-- dynamically filled by javascript after uploads -->
</div>
</div>
</td></tr>
</table>
</div>                                                                                    
"""
                           % {'dest_dir': '.' + os.sep}})

    output_objects.append({'object_type': 'html_form', 
                           'text': '\n</div><!-- files_form-->'})
    return (output_objects, status)
