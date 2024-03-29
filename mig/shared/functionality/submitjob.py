#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# submitjob - Job submission interfaces
# Copyright (C) 2003-2015  The MiG Project lead by Brian Vinter
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
from shared.html import themed_styles
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

    css_helpers = {'css_base': os.path.join(configuration.site_images, 'css'),
                   'skin_base': configuration.site_skin_base}
    title_entry['style'] = themed_styles(configuration,
                                         base=['jquery.fileupload.css',
                                               'jquery.fileupload-ui.css'],
                                         skin=['fileupload-ui.custom.css'])
    title_entry['javascript'] = '''
<script type="text/javascript" src="/images/js/jquery.js"></script>
<script type="text/javascript" src="/images/js/jquery-ui.js"></script>
<!--  Filemanager is only needed for fancy upload init wrapper -->
<script type="text/javascript" src="/images/js/jquery.form.js"></script>
<script type="text/javascript" src="/images/js/jquery.filemanager.js"></script>

<!-- Fancy file uploader and dependencies -->
<!-- The Templates plugin is included to render the upload/download listings -->
<script type="text/javascript" src="/images/js/tmpl.min.js"></script>
<!-- The Load Image plugin is included for the preview images and image resizing functionality -->
<script type="text/javascript" src="/images/js/load-image.min.js"></script>
<!-- The Iframe Transport is required for browsers without support for XHR file uploads -->
<script type="text/javascript" src="/images/js/jquery.iframe-transport.js"></script>
<!-- The basic File Upload plugin -->
<script type="text/javascript" src="/images/js/jquery.fileupload.js"></script>
<!-- The File Upload processing plugin -->
<script type="text/javascript" src="/images/js/jquery.fileupload-process.js"></script>
<!-- The File Upload image preview & resize plugin -->
<script type="text/javascript" src="/images/js/jquery.fileupload-image.js"></script>
<!-- The File Upload validation plugin -->
<script type="text/javascript" src="/images/js/jquery.fileupload-validate.js"></script>
<!-- The File Upload user interface plugin -->
<script type="text/javascript" src="/images/js/jquery.fileupload-ui.js"></script>
<!-- The File Upload jQuery UI plugin -->
<script type="text/javascript" src="/images/js/jquery.fileupload-jquery-ui.js"></script>

<script type="text/javascript" >

    options = %s;

    function setDisplay(this_id, new_d) {
        //console.log("setDisplay with: "+this_id);
        el = document.getElementById(this_id)
        if ( el == undefined || el.style == undefined ) {
            console.log("failed to locate display element: "+this_id);
            return; // avoid js null ref errors
        }
        el.style.display=new_d;
    }

    function switchTo(name) {
        //console.log("switchTo: "+name);
        for (o=0; o < options.length; o++) {
            if (name == options[o]) {
                setDisplay(options[o],"block");
            } else {
                setDisplay(options[o],"none");
            }
        }
    }

    function openFancyUpload() {
        var open_dialog = mig_fancyuploadchunked_init("fancyuploadchunked_dialog");
        var remote_path = ".";
        open_dialog("Upload Files", function() { return false; },
                    remote_path, false);
    }

    $(document).ready( function() {
         //console.log("document ready handler");
         switchTo("%s");
         $("#fancydialog").click(openFancyUpload);
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
<div class="submitjob">
<form method="post" action="submitfields.py">
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
                    display = "%s" % name
                    if display == '':
                        display = ' '
                    value_select += """<option %s value='%s'>%s</option>\n""" \
                                    % (selected, name, display)
                value_select += """</select><br />\n"""    
            output_objects.append({'object_type': 'html_form', 'text'
                                   : value_select
                                   })
        output_objects.append({'object_type': 'html_form', 'text': "<br />"})

    output_objects.append({'object_type': 'html_form', 'text'
                          : """
<br />
<table class='centertext'>
<tr><td><input type='submit' value='Submit Job' />
<input type='checkbox' name='save_as_default'> Save as default job template
</td></tr>
</table>
<br />
</form>
</div>
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
<a href=/public/cpuinfo.mRSL>CPU Info</a>,
<a href=/public/basic-io.mRSL>Basic I/O</a>,
<a href=/public/notification.mRSL>Job Notification</a>,
<a href=/public/povray.mRSL>Povray</a> and
<a href=/public/vcr.mRSL>VCR</a>
</div>
    """})

    output_objects.append({'object_type': 'html_form', 'text'
                          : """
<!-- 
Please note that textarea.py chokes if no nonempty KEYWORD_X_Y_Z fields 
are supplied: thus we simply send a bogus jobname which does nothing
-->
<form method="post" action="textarea.py">
<table class="submitjob">
<tr><td class="centertext">
<input type=hidden name=jobname_0_0_0 value=" " />
<textarea cols="82" rows="25" name="mrsltextarea_0">
%(default_mrsl)s
</textarea>
</td></tr>
<tr><td class='centertext'>
<input type="submit" value="Submit Job" />
<input type="checkbox" name="save_as_default" >Save as default job template
</td></tr>
</table>
</form>
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
<form enctype='multipart/form-data' action='textarea.py' method='post'>
<table class='files'>
<tr class='title'><td class='centertext' colspan=4>
Upload job files
</td></tr>
<tr><td colspan=3>
Upload file to current directory (%(dest_dir)s)
</td><td><br /></td></tr>
<tr><td colspan=2>
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
</td><td class='righttext' colspan=3>
<input name='fileupload_0_0_0' type='file'/>
</td></tr>
<tr><td>
Optional remote filename (extra useful in windows)
</td><td class='righttext' colspan=3>
<input name='default_remotefilename_0' type='hidden' value='%(dest_dir)s'/>
<input name='remotefilename_0' type='text' size='50' value='%(dest_dir)s'/>
<input type='submit' value='Upload' name='sendfile'/>
</td></tr>
</table>
</form>
<table class='files'>
<tr class='title'><td class='centertext'>
Upload other files efficiently (using chunking).
</td></tr>
<tr><td class='centertext'>
<button id='fancydialog'>Open Upload dialog</button>
</td></tr>
</table>
</div><!-- files_form-->

<div id='fancyuploadchunked_dialog' title='Upload File' style='display: none;'>

    <!-- The file upload form used as target for the file upload widget -->
    <form id='fancyfileupload' action='uploadchunked.py?output_format=json;action=put'
        method='POST' enctype='multipart/form-data'>
        <fieldset id='fancyfileuploaddestbox'>
            <label id='fancyfileuploaddestlabel' for='fancyfileuploaddest'>
                Optional final destination dir:
            </label>
            <input id='fancyfileuploaddest' type='text' size=60 value=''>
        </fieldset>

        <!-- The fileupload-buttonbar contains buttons to add/delete files and start/cancel the upload -->
        <div class='fileupload-buttonbar'>
            <div class='fileupload-buttons'>
                <!-- The fileinput-button span is used to style the file input field as button -->
                <span class='fileinput-button'>
                    <span>Add files...</span>
                    <input type='file' name='files[]' multiple>
                </span>
                <button type='submit' class='start'>Start upload</button>
                <button type='reset' class='cancel'>Cancel upload</button>
                <button type='button' class='delete'>Delete</button>
                <input type='checkbox' class='toggle'>
                <!-- The global file processing state -->
                <span class='fileupload-process'></span>
            </div>
            <!-- The global progress state -->
            <div class='fileupload-progress fade' style='display:none'>
                <!-- The global progress bar -->
                <div class='progress' role='progressbar' aria-valuemin='0' aria-valuemax='100'></div>
                <!-- The extended global progress state -->
                <div class='progress-extended'>&nbsp;</div>
            </div>
        </div>
        <!-- The table listing the files available for upload/download -->
        <table role='presentation' class='table table-striped'><tbody class='uploadfileslist'></tbody></table>
    </form>
    <!-- For status and error output messages -->
    <div id='fancyuploadchunked_output'></div>
</div>
    """ % {'dest_dir': '.' + os.sep}})
    
    output_objects.append({'object_type': 'html_form', 
                           'text': '''
<!-- The template to display files available for upload -->
<script id="template-upload" type="text/x-tmpl">
{% console.log("using upload template"); %}
{% console.log("... with upload files: "+$.fn.dump(o)); %}
{% var dest_dir = "./" + $("#fancyfileuploaddest").val(); %}
{% console.log("using upload dest: "+dest_dir); %}
{% for (var i=0, file; file=o.files[i]; i++) { %}
    {% var rel_path = $.fn.normalizePath(dest_dir+"/"+file.name); %}
    {% console.log("using upload rel_path: "+rel_path); %}
    <tr class="template-upload fade">
        <td>
            <span class="preview"></span>
        </td>
        <td>
            <p class="name">{%=rel_path%}</p>
            <strong class="error"></strong>
        </td>
        <td>
            <div class="size pending">Processing...</div>
            <div class="progress"></div>
        </td>
        <td>
            {% if (!i && !o.options.autoUpload) { %}
                <button class="start" disabled>Start</button>
            {% } %}
            {% if (!i) { %}
                <button class="cancel">Cancel</button>
            {% } %}
        </td>
    </tr>
{% } %}
</script>
<!-- The template to display files available for download -->
<script id="template-download" type="text/x-tmpl">
{% console.log("using download template"); %}
{% console.log("... with download files: "+$.fn.dump(o)); %}
{% for (var i=0, file; file=o.files[i]; i++) { %}
    {% var rel_path = $.fn.normalizePath("./"+file.name); %}
    {% console.log("using download rel_path: "+rel_path); %}
    <tr class="template-download fade">
        <td>
            <span class="preview">
                {% if (file.thumbnailUrl) { %}
                <a href="{%=file.url%}" title="{%=file.name%}" download="{%=file.name%}" data-gallery><img src="{%=file.thumbnailUrl%}"></a>
                {% } %}
            </span>
        </td>
        <td>
            <p class="name">
                <a href="{%=file.url%}" title="{%=file.name%}" download="{%=file.name%}" {%=file.thumbnailUrl?\'data-gallery\':\'\'%}>{%=rel_path%}</a>
            </p>
            {% if (file.error) { %}
                <div><span class="error">Error</span> {%=file.error%}</div>
            {% } %}
        </td>
        <td>
            <div class="size">{%=o.formatFileSize(file.size)%}</div>
        </td>
        <td>
            <button class="delete" data-type="{%=file.deleteType%}" data-url="{%=file.deleteUrl%}"{% if (file.deleteWithCredentials) { %} data-xhr-fields=\'{"withCredentials":true}\'{% } %}>{% if (file.deleteUrl) { %}Delete{% } else { %}Dismiss{% } %}</button>
            <input type="checkbox" name="delete" value="1" class="toggle">
        </td>
    </tr>
{% } %}
</script>
    '''})
    return (output_objects, status)
