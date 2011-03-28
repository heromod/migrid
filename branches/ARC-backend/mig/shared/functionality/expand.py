#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# expand - emulate shell wild card expansion
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

"""Script to provide users with a means of expanding patterns to files and
directories in their home directories. This script tries to mimic basic shell
wild card expansion.
"""

import os
import glob

from shared.parseflags import all, long_list, recursive
from shared.validstring import valid_user_path
from shared.init import initialize_main_variables
from shared.functional import validate_input_and_cert
import shared.returnvalues as returnvalues
from shared.settings import load_settings
from shared.useradm import client_id_dir
from shared.functionality.ls import select_all_javascript, \
    selected_file_actions_javascript


def signature():
    """Signature of the main function"""

    defaults = {'flags': [''], 'path': ['.'], 'with_dest': ['false']}
    return ['dir_listings', defaults]


def handle_file(
    listing,
    filename,
    file_with_dir,
    actual_file,
    flags='',
    dest='',
    show_dest=False,
    ):
    """handle a file"""

    # Build entire line before printing to avoid newlines

    if os.path.basename(file_with_dir) == '.htaccess':

        # Always hide .htaccess

        return
    file_obj = {
        'object_type': 'direntry',
        'type': 'file',
        'name': filename,
        'file_with_dir': file_with_dir,
        'flags': flags,
        }

    if show_dest:
        file_obj['file_dest'] = dest

    listing.append(file_obj)


def handle_expand(
    output_objects,
    listing,
    base_dir,
    real_path,
    flags='',
    dest='',
    depth=0,
    show_dest=False,
    ):
    """Recursive function to expand paths in a way not unlike ls, but only
    files are interesting in this context. The order of recursively expanded
    paths is different from that in ls since it simplifies the code and
    doesn't really matter to the clients.
    """

    # Sanity check

    if depth > 255:
        output_objects.append({'object_type': 'error_text', 'text'
                              : 'Error: file recursion maximum exceeded!'
                              })
        return (output_objects, returnvalues.SYSTEM_ERROR)

    # references to '.' or similar are stripped by abspath

    if real_path + os.sep == base_dir:
        base_name = relative_path = '.'
    else:
        base_name = os.path.basename(real_path)
        relative_path = real_path.replace(base_dir, '')

    if os.path.isfile(real_path):
        handle_file(
            listing,
            base_name,
            relative_path,
            real_path,
            flags,
            dest,
            show_dest,
            )
    else:
        try:
            contents = os.listdir(real_path)
        except Exception, exc:
            output_objects.append({'object_type': 'error_text', 'text'
                                  : 'Failed to list contents of %s: %s'
                                   % (base_name, exc)})
            return (output_objects, returnvalues.SYSTEM_ERROR)

        # Filter out dot files unless '-a' is used

        if not all(flags):
            contents = [i for i in contents if not i.startswith('.')]
        contents.sort()

        if not recursive(flags) or depth < 0:

            for name in contents:
                path = real_path + os.sep + name
                rel_path = path.replace(base_dir, '')
                if os.path.isfile(path):
                    handle_file(
                        listing,
                        name,
                        rel_path,
                        path,
                        flags,
                        dest,
                        show_dest,
                        )
        else:

            # Force pure content listing first by passing a negative depth

            handle_expand(
                output_objects,
                listing,
                base_dir,
                real_path,
                flags,
                dest,
                -1,
                show_dest,
                )

            for name in contents:
                path = real_path + os.sep + name
                rel_path = path.replace(base_dir, '')
                if os.path.isdir(path):
                    handle_expand(
                        output_objects,
                        listing,
                        base_dir,
                        path,
                        flags,
                        dest,
                        depth + 1,
                        show_dest,
                        )


def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(op_header=False, op_title=False)
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

    flags = ''.join(accepted['flags'])
    pattern_list = accepted['path']
    show_dest = accepted['with_dest'][0].lower() == 'true'
    listing = []

    # Please note that base_dir must end in slash to avoid access to other
    # user dirs when own name is a prefix of another user name

    base_dir = os.path.abspath(os.path.join(configuration.user_home,
                               client_dir)) + os.sep

    status = returnvalues.OK

    settings_dict = load_settings(client_id, configuration)
    if not settings_dict or not settings_dict.has_key('FILESUI'):
        logger.info('Settings dict does not have FILESUI key - using default'
                    )
        files_style = configuration.filesui[0]
    else:
        files_style = settings_dict['FILESUI']

    if 'full' == files_style:
        javascript = '%s\n%s' % (select_all_javascript(),
                                 selected_file_actions_javascript())
    else:
        javascript = ''

    output_objects.append({
        'object_type': 'title',
        'text': 'MiG Files',
        'javascript': javascript,
        'bodyfunctions': '',
        })
    output_objects.append({'object_type': 'header', 'text': 'MiG Files'
                          })

    location_pre_html = \
        """
<div class='files'>
<table class='files'>
<tr class=title><td class=centertext colspan=2>
Working directory:
</td></tr>
<tr><td class=centertext>
"""
    output_objects.append({'object_type': 'html_form', 'text'
                          : location_pre_html})
    for pattern in pattern_list:
        links = []
        links.append({'object_type': 'link', 'text': 'MiG HOME',
                     'destination': 'ls.py?path=.'})
        prefix = ''
        parts = pattern.split(os.sep)
        for i in parts:
            prefix = os.path.join(prefix, i)
            links.append({'object_type': 'link', 'text': i,
                         'destination': 'ls.py?path=%s' % prefix})
        output_objects.append({'object_type': 'multilinkline', 'links'
                              : links})

    location_post_html = """
</td></tr>
</table>
</div>
<br>
"""

    output_objects.append({'object_type': 'html_form', 'text'
                          : location_post_html})
    if 'full' == files_style:
        more_html = \
            """
<div class='files'>
<table class='files'>
<tr class=title><td class=centertext colspan=2>
Advanced file actions
</td></tr>
<tr><td>
Action on paths selected below
(please hold mouse cursor over button for a description):
</td>
<td class=centertext>
<form method='post' name='fileform' onSubmit='return selectedFilesAction();'>
<input type='hidden' name='output_format' value='html'>
<input type='hidden' name='flags' value='v'>
<input type='submit' title='Show concatenated contents (cat)' onClick='document.pressed=this.value' value='cat'>
<input type='submit' onClick='document.pressed=this.value' value='head' title='Show first lines (head)'>
<input type='submit' onClick='document.pressed=this.value' value='tail' title='Show last lines (tail)'>
<input type='submit' onClick='document.pressed=this.value' value='wc' title='Count lines/words/chars (wc)'>
<input type='submit' onClick='document.pressed=this.value' value='stat' title='Show details (stat)'>
<input type='submit' onClick='document.pressed=this.value' value='touch' title='Update timestamp (touch)'>
<input type='submit' onClick='document.pressed=this.value' value='truncate' title='TRUNCATE! (truncate)'>
<input type='submit' onClick='document.pressed=this.value' value='rm' title='DELETE! (rm)'>
<input type='submit' onClick='document.pressed=this.value' value='rmdir' title='Remove directory (rmdir)'>
<input type='submit' onClick='document.pressed=this.value' value='submit' title='Submit file (submit)'>
</td></tr>
</table>    
</div>
"""

        output_objects.append({'object_type': 'html_form', 'text'
                              : more_html})
    dir_listings = []
    output_objects.append({
        'object_type': 'dir_listings',
        'dir_listings': dir_listings,
        'flags': flags,
        'style': files_style,
        'show_dest': show_dest,
        })

    first_match = None
    for pattern in pattern_list:

        # Check directory traversal attempts before actual handling to avoid leaking
        # information about file system layout while allowing consistent error messages

        unfiltered_match = glob.glob(base_dir + pattern)
        match = []
        for server_path in unfiltered_match:
            real_path = os.path.abspath(server_path)
            if not valid_user_path(real_path, base_dir, True):

                # out of bounds - save user warning for later to allow partial match:
                # ../*/* is technically allowed to match own files.

                logger.error('Warning: %s tried to %s %s outside own home! (using pattern %s)'
                              % (client_id, op_name, real_path,
                             pattern))
                continue
            match.append(real_path)
            if not first_match:
                first_match = real_path

        # Now actually treat list of allowed matchings and notify if no (allowed) match

        if not match:
            output_objects.append({'object_type': 'file_not_found',
                                  'name': pattern})
            status = returnvalues.FILE_NOT_FOUND

        for real_path in match:
            if real_path + os.sep == base_dir:
                relative_path = '.'
            else:
                relative_path = real_path.replace(base_dir, '')
            entries = []
            dir_listing = {
                'object_type': 'dir_listing',
                'relative_path': relative_path,
                'entries': entries,
                'flags': flags,
                }

            dest = ''
            if show_dest:
                if os.path.isfile(real_path):
                    dest = os.path.basename(real_path)
                elif recursive(flags):

                    # references to '.' or similar are stripped by abspath

                    if real_path + os.sep == base_dir:
                        dest = ''
                    else:

                        # dest = os.path.dirname(real_path).replace(base_dir, "")

                        dest = os.path.basename(real_path) + os.sep

            handle_expand(
                output_objects,
                entries,
                base_dir,
                real_path,
                flags,
                dest,
                0,
                show_dest,
                )
            dir_listings.append(dir_listing)

    if 'full' == files_style:
        output_objects.append({'object_type': 'html_form', 'text'
                              : """
    <div class='files'>
    <table class='files'>
    <tr class=title><td class=centertext>
    Filter paths (wildcards like * and ? are allowed)
    <form method='post' action='ls.py'>
    <input type='hidden' name='output_format' value='html'>
    <input type='hidden' name='flags' value='%s'>
    <input type='text' name='path' value=''>
    <input type='submit' value='Filter'>
    </form>
    </td></tr>
    </table>    
    </div>
    """
                               % flags})

    # Short/long format buttons

    htmlform = \
        """<table class='files'>
    <tr class=title><td class=centertext colspan=4>
    File view options
    </td></tr>
    <tr><td><br></td></tr>
    <tr class=title><td>Parameter</td><td>Setting</td><td>Enable</td><td>Disable</td></tr>
    <tr><td>Long format</td><td>
    %s</td><td>"""\
         % long_list(flags)\
         + """
    <form method='post' action='ls.py'>
    <input type='hidden' name='output_format' value='html'>
    <input type='hidden' name='flags' value='%s'>"""\
         % (flags + 'l')

    for entry in pattern_list:
        htmlform += "<input type='hidden' name='path' value='%s'>"\
             % entry
    htmlform += \
        """
    <input type='submit' value='On'><br>
    </form>
    </td><td>
    <form method='post' action='ls.py'>
    <input type='hidden' name='output_format' value='html'>
    <input type='hidden' name='flags' value='%s'>"""\
         % flags.replace('l', '')
    for entry in pattern_list:
        htmlform += "<input type='hidden' name='path' value='%s'>"\
             % entry

    htmlform += \
        """
    <input type='submit' value='Off'><br>
    </form>
    </td></tr>
    """

    if 'full' == files_style:

        # Recursive output

        htmlform += \
            """
    <!-- Non-/recursive list buttons -->
    <tr><td>Recursion</td><td>
    %s</td><td>"""\
             % recursive(flags)
        htmlform += \
            """
    <form method='post' action='ls.py'>
    <input type='hidden' name='output_format' value='html'>
    <input type='hidden' name='flags' value='%s'>"""\
             % (flags + 'r')
        for entry in pattern_list:
            htmlform += " <input type='hidden' name='path' value='%s'>"\
                 % entry
        htmlform += \
            """
    <input type='submit' value='On'><br>
    </form>
    </td><td>
    <form method='post' action='ls.py'>
    <input type='hidden' name='output_format' value='html'>
    <input type='hidden' name='flags' value='%s'>"""\
             % flags.replace('r', '')
        for entry in pattern_list:
            htmlform += "<input type='hidden' name='path' value='%s'>"\
                 % entry
            htmlform += \
                """
    <input type='submit' value='Off'><br>
    </form>
    </td></tr>
    """

    htmlform += \
        """
    <!-- Show dot files buttons -->
    <tr><td>Show hidden files</td><td>
    %s</td><td>"""\
         % all(flags)
    htmlform += \
        """
    <form method='post' action='ls.py'>
    <input type='hidden' name='output_format' value='html'>
    <input type='hidden' name='flags' value='%s'>"""\
         % (flags + 'a')
    for entry in pattern_list:
        htmlform += "<input type='hidden' name='path' value='%s'>"\
             % entry
    htmlform += \
        """
    <input type='submit' value='On'><br>
    </form>
    </td><td>
    <form method='post' action='ls.py'>
    <input type='hidden' name='output_format' value='html'>
    <input type='hidden' name='flags' value='%s'>"""\
         % flags.replace('a', '')
    for entry in pattern_list:
        htmlform += "<input type='hidden' name='path' value='%s'>"\
             % entry
    htmlform += \
        """
    <input type='submit' value='Off'><br>
    </form>
    </td></tr>
    </table>
    """

    # show flag buttons after contents to avoid

    output_objects.append({'object_type': 'html_form', 'text'
                          : htmlform})

    # create upload file form

    if first_match:

        # use first match for current directory
        # Note that base_dir contains an ending slash

        if os.path.isdir(first_match):
            dir_path = first_match
        else:
            dir_path = os.path.dirname(first_match)

        if dir_path + os.sep == base_dir:
            relative_dir = '.'
        else:
            relative_dir = dir_path.replace(base_dir, '')

        output_objects.append({'object_type': 'html_form', 'text'
                              : """
<br>
<table class='files'>
<tr class=title><td class=centertext colspan=3>
Edit file
</td></tr>
<tr><td>
Fill in the path of a file to edit and press 'edit' to open that file in the<br>
online file editor. Alternatively a file can be selected for editing through<br>
the listing of personal files. 
</td><td colspan=2 class=righttext>
<form name='editor' method='post' action='editor.py'>
<input type='hidden' name='output_format' value='html'>
<input name='current_dir' type='hidden' value='%(dest_dir)s'>
<input type='text' name='path' size=50 value=''>
<input type='submit' value='edit'>
</form>
</td></tr>
</table>
<br>
<table class='files'>
<tr class=title><td class=centertext colspan=4>
Create directory
</td></tr>
<tr><td>
Name of new directory to be created in current directory (%(dest_dir)s)
</td><td class=righttext colspan=3>
<form action='mkdir.py' method=post>
<input name='path' size=50>
<input name='current_dir' type='hidden' value='%(dest_dir)s'/>
<input type='submit' value='Create' name='mkdirbutton'>
</form>
</td></tr>
</table>
<br>
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
<input type=checkbox name='extract_0'>
</td></tr>
<tr><td colspan=2>
Submit mRSL files (also .mRSL files included in packages)
</td><td colspan=2>
<input type=checkbox name='submitmrsl_0' CHECKED>
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
<input name='remotefilename_0' type='input' size='50' value='%(dest_dir)s'/>
<input type='submit' value='Upload' name='sendfile'/>
</form>
</td></tr>
</table>
    """
                               % {'dest_dir': relative_dir + os.sep}})

    output_objects.append({'object_type': 'text', 'text': ''})
    return (output_objects, status)

