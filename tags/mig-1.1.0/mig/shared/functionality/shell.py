#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# shell - [insert a few words of module description on this line]
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

"""Emulate a command line interface with all the cgi functions"""

import os
import getopt

import shared.returnvalues as returnvalues
from shared.init import initialize_main_variables, find_entry
from shared.functional import validate_input_and_cert
from shared.functionality import canceljob, cat, cp, docs, find, grep, \
    head, jobstatus, liveoutput, ls, mkdir, mv, resubmit, rm, rmdir, \
    spell, statpath, submit, tail, touch, truncate, wc
from shared.validstring import valid_user_path


def signature():
    """Signature of the main function"""

    defaults = {'cmd': ['help']}
    return ['html_form', defaults]


def shell_usage():
    """Script usage help"""

    out = []
    out.append({'object_type': 'text', 'text'
               : 'Most commands from the MiG user scripts translate directly to this shell.'
               })
    out.append({'object_type': 'text', 'text'
               : "The biggest difference is that the 'mig' prefix is removed."
               })
    out.append({'object_type': 'text', 'text': 'Example commands:'})
    out.append({'object_type': 'text', 'text': 'ls -l *.txt'})
    out.append({'object_type': 'text', 'text': 'cat *.stdout'})
    out.append({'object_type': 'text', 'text': 'grep flags cpuinfo.txt'
               })
    out.append({'object_type': 'text', 'text': 'find . job*.out'})
    out.append({'object_type': 'text', 'text': 'submit example.mRSL'})
    out.append({'object_type': 'text', 'text': 'head input.txt'})
    out.append({'object_type': 'text', 'text': 'status 34*12'})
    out.append({'object_type': 'text', 'text': 'cancel 333*'})
    out.append({'object_type': 'text', 'text': 'resubmit 3332323*'})
    out.append({'object_type': 'text', 'text': 'rm -rf tmpdir'})
    out.append({'object_type': 'text', 'text': 'cp *.stdout jobstdout/'
               })
    out.append({'object_type': 'text', 'text': 'spell en_us input.txt'})
    out.append({'object_type': 'text', 'text': 'liveoutput 3332323*'})
    return out


def handle_command(cmd_line, client_id, output_objects):
    """Forward command handling to the appropriate back end"""

    parts = cmd_line.split(' ')
    cmd = parts[0]
    opts_str = 'abdefghijklmnopqrstuvwxyz'
    try:
        (opts, args) = getopt.getopt(parts[1:], opts_str)
    except getopt.GetoptError, exc:
        output_objects.append({'object_type': 'error_text', 'text'
                              : 'failed to parse options: %s' % exc})

        opts = []
        args = parts[1:]

    # Strip '-' from opts

    flags = [i[0][-1] for i in opts]
    output_types = [
        'dir_listings',
        'error_text',
        'file',
        'filewcs',
        'file_output',
        'file_not_found',
        'header',
        'job_list',
        'link',
        'list',
        'resubmitobjs',
        'stats',
        'submitstatuslist',
        'text',
        'warning',
        ]

    # Flexible fill with args in order to fit operations
    # ls and find must work without arguments but missing arguments
    # must be caught in other cases.
    # All main functions expect arguments to be on a list form.

    first = args[0:1]
    prefix = args[0:max(len(args) - 1, 1)]
    suffix = args[1:len(args)]
    last = args[max(len(args) - 1, 1):]

    # print "DEBUG: args %s ; first %s; prefix %s; suffix %s; last %s" % \
    #      (args, first, prefix, suffix, last)

    try:
        if 'cancel' == cmd:
            (out, code) = canceljob.main(client_id, {'job_id': args,
                    'flags': flags})
        elif 'cat' == cmd:
            (out, code) = cat.main(client_id, {'path': args, 'flags'
                                   : flags})
        elif 'cp' == cmd:
            (out, code) = cp.main(client_id, {'src': prefix, 'dst'
                                  : last, 'flags': flags})
        elif 'doc' == cmd:
            (out, code) = docs.main(client_id, {'show': args, 'flags'
                                    : flags})
        elif 'find' == cmd:
            (out, code) = find.main(client_id, {'path': prefix, 'name'
                                    : last, 'flags': flags})
        elif 'grep' == cmd:
            (out, code) = grep.main(client_id, {'path': suffix,
                                    'pattern': first, 'flags': flags})
        elif 'head' == cmd:
            (out, code) = head.main(client_id, {'path': args, 'flags'
                                    : flags})
        elif 'help' == cmd:
            out = shell_usage()
        elif 'mkdir' == cmd:
            (out, code) = mkdir.main(client_id, {'path': args, 'flags'
                    : flags})
        elif 'mv' == cmd:
            (out, code) = mv.main(client_id, {'src': prefix, 'dst'
                                  : last, 'flags': flags})
        elif 'liveoutput' == cmd:
            (out, code) = liveoutput.main(client_id, {'job_id': args,
                    'flags': flags})
        elif 'ls' == cmd:
            (out, code) = ls.main(client_id, {'path': args, 'flags'
                                  : flags})
        elif 'resubmit' == cmd:
            (out, code) = resubmit.main(client_id, {'job_id': args,
                    'flags': flags})
        elif 'rm' == cmd:
            (out, code) = rm.main(client_id, {'path': args, 'flags'
                                  : flags})
        elif 'rmdir' == cmd:
            (out, code) = rmdir.main(client_id, {'path': args, 'flags'
                    : flags})
        elif 'spell' == cmd:
            (out, code) = spell.main(client_id, {'path': suffix, 'lang'
                    : first, 'flags': flags})
        elif 'stat' == cmd:
            (out, code) = statpath.main(client_id, {'path': args,
                    'flags': flags})
        elif 'status' == cmd:
            (out, code) = jobstatus.main(client_id, {'job_id': args,
                    'flags': flags})
        elif 'submit' == cmd:
            (out, code) = submit.main(client_id, {'path': args, 'flags'
                    : flags})
        elif 'tail' == cmd:
            (out, code) = tail.main(client_id, {'path': args, 'flags'
                                    : flags})
        elif 'touch' == cmd:
            (out, code) = touch.main(client_id, {'path': args, 'flags'
                    : flags})
        elif 'truncate' == cmd:
            (out, code) = truncate.main(client_id, {'path': args,
                    'flags': flags})
        elif 'wc' == cmd:
            (out, code) = wc.main(client_id, {'path': args, 'flags'
                                  : flags})
        # Undocumented operation for debugging apache environment
        elif 'env' == cmd:
            raise Exception('Dumping environment: %s' % os.environ)
        else:
            raise Exception('command not found')
    except Exception, exc:
        output_objects.append({'object_type': 'error_text', 'text'
                              : '%s: %s' % (cmd, exc)})
        return (output_objects, returnvalues.SYSTEM_ERROR)
    for entry in out:
        if entry['object_type'] in output_types:
            output_objects.append(entry)
    return (output_objects, returnvalues.OK)


def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(op_header=False)

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

    commands = accepted['cmd']

    # Please note that base_dir must end in slash to avoid access to other
    # user dirs when own name is a prefix of another user name

    base_dir = os.path.abspath(configuration.mig_server_home + os.sep
                                + '..' + os.sep + 'cgi-bin') + os.sep

    title_entry = find_entry(output_objects, 'title')
    title_entry['text'] = 'Command Shell'
    output_objects.append({'object_type': 'header', 'text': 'Command Shell'
                          })
    output_objects.append({'object_type': 'html_form', 'text'
                          : """
    <div class='title'>
    This page gives direct access to most MiG commands.
    </div>
    <div class='migcontent'>
    <BR>It supports wildcard expansion but no input/output redirection or pipes.
    <form method='post' action='shell.py'>
    <input type='hidden' name='output_format' value='html'>
    <input type='text' name='cmd' size=80 value=''>
    <input type='submit' value='execute'>
    </form>
    </div>
    """})
    if not commands:
        return (output_objects, status)

    for cmd_line in commands:
        cmd_line = cmd_line.strip()
        parts = cmd_line.split(' ')
        cmd = parts[0]

        # Check directory traversal attempts before actual handling
        # to avoid leaking information about file system layout while
        # allowing consistent error messages

        server_path = base_dir + cmd + '.py'
        real_path = os.path.abspath(server_path)
        if not valid_user_path(real_path, base_dir, True):

            # out of bounds - save user warning for later to allow
            # partial match:
            # ../*/* is technically allowed to match own files.

            logger.error('Warning: %s tried to %s %s outside cgi home! (%s)'
                          % (client_id, op_name, real_path, cmd))
            output_objects.append({'object_type': 'command_not_found',
                                  'name': cmd})
            status = returnvalues.CLIENT_ERROR
            continue

        relative_path = real_path.replace(base_dir, '')

        output_objects.append({'object_type': 'text', 'text': cmd_line})
        (output_objects, status) = handle_command(cmd_line, client_id,
                output_objects)
        output_objects.append({'object_type': 'text', 'text': ''})

    return (output_objects, status)

