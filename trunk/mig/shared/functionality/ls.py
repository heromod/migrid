#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# ls - emulate ls command
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
their home directories. This script tries to mimic GNU ls behaviour.
"""

import os
import sys
import time
import glob
import stat

from shared.parseflags import all, long_list, recursive
from shared.validstring import valid_user_path
from shared.init import initialize_main_variables
from shared.functional import validate_input_and_cert, REJECT_UNSET
import shared.returnvalues as returnvalues


def signature():
    """Signature of the main function"""
    defaults = {'flags': [''], 'path': ['.']}
    return ['dir_listings', defaults]


def select_all_javascript():
    """ return javascript to select all html checkboxes """

    return """
<script LANGUAGE='JavaScript'>
document.fileform.allbox.onclick = un_check;
function un_check() {
   for(var i = 0; i < document.fileform.elements.length; i++) {
      var e = document.fileform.elements[i];
      if ((e.name != 'allbox') && (e.type == 'checkbox')) {
         e.checked = document.fileform.allbox.checked;
      }
   }
}
</script>
"""


def selected_file_actions_javascript():
    """ return javascript """

    return """
<script language='JavaScript'>
function selectedFilesAction() {
    if (document.pressed == 'cat') {
       document.fileform.action = 'cat.py';
    }
    else if (document.pressed == 'head') {
       document.fileform.action = 'head.py';
    }
    else if (document.pressed == 'rm') {
       document.fileform.action = 'rm.py';
       document.fileform.flags.value = 'rv';
    }
    else if (document.pressed == 'rmdir') {
       document.fileform.action = 'rmdir.py';
    }
    else if (document.pressed == 'stat') {
       document.fileform.action = 'stat.py';
    }
    else if (document.pressed == 'submit') {
       document.fileform.action = 'submit.py';
    }
    else if (document.pressed == 'tail') {
       document.fileform.action = 'tail.py';
       document.fileform.flags.value = '';
    }
    else if (document.pressed == 'touch') {
       document.fileform.action = 'touch.py';
    }
    else if (document.pressed == 'truncate') {
       document.fileform.action = 'truncate.py';
    }
    else if (document.pressed == 'wc') {
       document.fileform.action = 'wc.py';
    }
    return true;
}
</script>
"""


def long_format(path):
    """ output extra info like filesize about the file located at path """

    format_line = ''
    perms = ''

    # Make a single stat call and extract all info from it

    try:
        stat_info = os.stat(path)
    except Exception, err:

        # Don't give away FS information - only log full failure reason
        # (logger not available here)
        # logger.warning("ls failed to stat %s: %s" % (path, err))

        return 'Internal error: stat failed!'

    mode = stat_info.st_mode
    if stat.S_ISDIR(mode):
        perms = 'd'
    elif stat.S_ISREG(mode):
        perms = '-'

    mode = stat.S_IMODE(mode)

    for entity in ('USR', 'GRP', 'OTH'):
        for permission in ('R', 'W', 'X'):

            # lookup attribute at runtime using getattr

            if mode & getattr(stat, 'S_I' + permission + entity):
                perms = perms + permission.lower()
            else:
                perms = perms + '-'

    format_line += perms + '\t'
    size = str(stat_info.st_size)
    format_line += size + '\t'
    atime = time.asctime(time.gmtime(stat_info.st_mtime))
    format_line += atime + '\t'

    return format_line


def handle_file(
    listing,
    filename,
    file_with_dir,
    actual_file,
    flags='',
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

    if long_list(flags):
        file_obj['long_format'] = long_format(actual_file)

    listing.append(file_obj)


def handle_dir(
    listing,
    dirname,
    dirname_with_dir,
    actual_dir,
    flags='',
    ):
    """handle a dir"""

    dir_obj = {
        'object_type': 'direntry',
        'type': 'directory',
        'name': dirname,
        'dirname_with_dir': dirname_with_dir,
        'flags': flags,
        }

    if long_list(flags):
        dir_obj['actual_dir'] = long_format(actual_dir)

    listing.append(dir_obj)


def handle_ls(
    output_objects,
    listing,
    real_path,
    flags='',
    depth=0,
    ):
    """Recursive function to emulate GNU ls (-R)"""

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
        handle_file(listing, base_name, relative_path, real_path, flags)
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

            # listdir does not include '.' and '..' - add manually
            # to ease navigation

            if all(flags):
                handle_dir(listing, '.', relative_path, real_path,
                           flags)
                handle_dir(listing, '..',
                           os.path.dirname(relative_path),
                           os.path.dirname(real_path), flags)
            for name in contents:
                path = real_path + os.sep + name
                rel_path = path.replace(base_dir, '')
                if os.path.isfile(path):
                    handle_file(listing, name, rel_path, path, flags)
                else:
                    handle_dir(listing, name, rel_path, path, flags)
        else:

            # Force pure content listing first by passing a negative depth

            handle_ls(output_objects, listing, real_path, flags, -1)

            for name in contents:
                path = real_path + os.sep + name
                rel_path = path.replace(base_dir, '')
                if os.path.isdir(path):
                    handle_ls(output_objects, listing, path, flags,
                              depth + 1)


def main(cert_name_no_spaces, user_arguments_dict):
    """Main function used by front end"""

    global output_objects

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(op_header=False, op_title=False)
    defaults = signature()[1]
    (validate_status, accepted) = validate_input_and_cert(
        user_arguments_dict,
        defaults,
        output_objects,
        cert_name_no_spaces,
        configuration,
        allow_rejects=False,
        )
    if not validate_status:
        return (accepted, returnvalues.CLIENT_ERROR)

    flags = ''.join(accepted['flags'])
    pattern_list = accepted['path']
    listing = []

    # Please note that base_dir must end in slash to avoid access to other
    # user dirs when own name is a prefix of another user name

    global base_dir
    base_dir = os.path.abspath(configuration.user_home + os.sep
                                + cert_name_no_spaces) + os.sep

    status = returnvalues.OK

    javascript = '%s\n%s' % (select_all_javascript(),
                             selected_file_actions_javascript())

    output_objects.append({
        'object_type': 'title',
        'text': 'MiG Files',
        'javascript': javascript,
        'bodyfunctions': '',
        })
    output_objects.append({'object_type': 'header', 'text': 'MiG Files'
                          })

    location_pre_html = """
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
    more_html = \
                  """
<div class='files'>
<table class='files'>
<tr class=title><td class=centertext colspan=2>
File actions
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
    output_objects.append({'object_type': 'dir_listings', 'dir_listings'
                          : dir_listings, 'flags': flags})

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
                              % (cert_name_no_spaces, op_name,
                             real_path, pattern))
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

            handle_ls(output_objects, entries, real_path, flags)
            dir_listings.append(dir_listing)

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
    """% flags})

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

    <!-- Show dot files buttons -->
    <tr><td>Show dot files</td><td>
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
<form name='editor' method='post' action='/cgi-bin/editor.py'>
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
<form action='/cgi-bin/mkdir.py' method=post>
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
<form enctype='multipart/form-data' action='/cgi-bin/textarea.py' method='post'>
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
    """ % {'dest_dir':(relative_dir + os.sep)}})

    output_objects.append({'object_type': 'text', 'text':''})
    return (output_objects, status)


