#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# submitjob - [insert a few words of module description on this line]
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
import sys

import shared.returnvalues as returnvalues
from shared.init import initialize_main_variables
from shared.functional import validate_input_and_cert, REJECT_UNSET

def get_default_mrsl(template_path):
    """Return the default mRSL template for user with supplied certificate"""
    try:
        template_fd = open(template_path, "rb")
        default_mrsl = template_fd.read()
        template_fd.close()
    except:
        # Use default hello grid example
        default_mrsl = """::EXECUTE::
echo 'hello grid!'
echo '...each line here is executed'

::NOTIFY::
email: SETTINGS
jabber: SETTINGS

::INPUTFILES::

::OUTPUTFILES::

::EXECUTABLES::

::MEMORY::
1

::DISK::
1

::CPUTIME::
30

::RUNTIMEENVIRONMENT::

"""
    return default_mrsl

def main(cert_name_no_spaces, user_arguments_dict):
    """Main function used by front end"""
    configuration, logger, output_objects, op_name = initialize_main_variables(op_header=False, op_title=False)
    
    status = returnvalues.OK
    defaults = {}
    (validate_status, accepted) = validate_input_and_cert(user_arguments_dict, defaults, output_objects, cert_name_no_spaces, configuration, allow_rejects = False)
    if not validate_status:
        return (accepted, returnvalues.CLIENT_ERROR)

    # Please note that base_dir must end in slash to avoid access to other
    # user dirs when own name is a prefix of another user name
    base_dir = os.path.abspath(configuration.user_home + os.sep + \
                               cert_name_no_spaces) + os.sep
    
    mrsl_template = os.path.join(base_dir, ".default.mrsl")
    
    output_objects.append({"object_type":"title", "text":"MiG Submit Job"})
    output_objects.append({"object_type":"header", "text":"MiG Submit Job"})
    output_objects.append({"object_type":"sectionheader", "text":"Please type your mRSL job description in the text area below:"})
    output_objects.append({"object_type":"html_form", "text":"""
<div class='smallcontent'>
Example mRSL job descriptions:
<a href=example.mRSL>example 1</a>,
<a href=example2.mRSL>example 2</a>,
<a href=example3.mRSL>example 3</a>,
<a href=example4.mRSL>example 4</a>, and
<a href=example5.mRSL>example 5</a>
<br>
<a href='/cgi-bin/docs.py?show=job'>mRSL Documentation</a>
</div>
    """})
    default_mrsl = get_default_mrsl(mrsl_template)
    output_objects.append({"object_type":"html_form", "text":"""
<!-- 
Please note that textarea.py chokes if no nonempty KEYWORD_X_Y_Z fields 
are supplied: thus we simply send a bogus jobname which does nothing
-->
<form method="post" action="/cgi-bin/textarea.py" id="miginput">
<input type=hidden name=jobname_0_0_0 value=" ">
<textarea cols="82" rows="25" name="mrsltextarea_0">
%s
</textarea>
<br><br>

<input type="submit" value="Submit">
</form>
    """ % default_mrsl})
    output_objects.append({"object_type":"sectionheader", "text":"Upload file to MiG home directory"})
    output_objects.append({"object_type":"html_form", "text":"""
<table class="migtable">
<form enctype="multipart/form-data" action="/cgi-bin/textarea.py"
      method="post" id="miginput">
<tr><td>
Extract package files (.zip, .tar.gz, .tgz, .tar.bz2)
</td><td><input type=checkbox name="extract_0"></td></tr>
<tr><td width="80%">
Submit mRSL files to parser (also .mRSL files included in packages)

</td><td><input type=checkbox name="submitmrsl_0" CHECKED></td></tr>

<tr><td>File</td><td>
<input name="fileupload_0_0_0" type="file" size="70"/>
</td></tr>
<tr><td>Remote filename</td><td>
<input name="remotefilename_0" type="text" size="70"/>
<input type="submit" value="Submit" name="sendfile">
</td></tr>
</form>
</table>
    """})
    output_objects.append({"object_type":"sectionheader", "text":"Create/edit file"})
    output_objects.append({"object_type":"html_form", "text":"""
Fill in the path of a file to edit and press 'edit' to open that file in the
online file editor. Alternatively a file can be selected for editing
through the listing of personal files. 
<form name='editor' method='post' action='/cgi-bin/editor.py'>
<input type='hidden' name='output_format' value='html'>
<input type='text' name='path' value=''><br>
<input type='submit' value='edit'>
</form>
    """})
    return (output_objects, status)
