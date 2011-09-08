#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# cp - [insert a few words of module description on this line]
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

# cgi version (automagically updated by cvs)

"""Emulate the un*x function with the same name."""

__version__ = '$Revision: 1910 $'

# $Id: cp.py 1910 2007-06-01 13:08:03Z jones $

import os
import sys
import glob
import shutil

from shared.validstring import valid_user_path
from shared.parseflags import verbose, recursive
from shared.init import initialize_main_variables
from shared.functional import validate_input_and_cert, REJECT_UNSET
import shared.returnvalues as returnvalues


def signature():
    defaults = {
        'flags': [''],
        'src': REJECT_UNSET,
        'dst': REJECT_UNSET,
        'iosessionid': [''],
        }
    return ['', defaults]


def main(cert_name_no_spaces, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables()
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
    src_list = accepted['src']
    dst = accepted['dst'][-1]
    iosessionid = accepted['iosessionid'][-1]

    # Please note that base_dir must end in slash to avoid access to other
    # user dirs when own name is a prefix of another user name

    if cert_name_no_spaces == 'None':
        base_dir = os.path.realpath(configuration.webserver_home
                                     + os.sep + iosessionid) + os.sep
    else:
        base_dir = os.path.abspath(configuration.user_home + os.sep
                                    + cert_name_no_spaces) + os.sep

    status = returnvalues.OK

    real_dest = base_dir + dst
    dst_list = glob.glob(real_dest)
    if not dst_list:

        # New destination?

        if not glob.glob(os.path.dirname(real_dest)):
            output_objects.append({'object_type': 'error_text', 'text'
                                  : 'Illegal dst path provided!'})
            return (output_objects, returnvalues.CLIENT_ERROR)
        else:
            dst_list = [real_dest]

    # Use last match in case of multiple matches

    dest = dst_list[-1]
    if len(dst_list) > 1:
        output_objects.append({'object_type': 'warning', 'text'
                              : 'dst (%s) matches multiple targets - using last: %s'
                               % (dst, dest)})

    real_dest = os.path.abspath(dest)

    # Don't use real_path in output as it may expose underlying
    # fs layout.

    relative_dest = real_dest.replace(base_dir, '')
    if not valid_user_path(real_dest, base_dir, True):

        # out of bounds

        output_objects.append({'object_type': 'error_text', 'text'
                              : "You're only allowed to write to your own home directory! dest (%s) expands to an illegal path (%s)"
                               % (dst, relative_dest)})
        logger.error('Warning: %s tried to copy file(s) to destination %s outside own home! (using pattern %s)'
                      % (cert_name_no_spaces, real_dest, dst))
        return (output_objects, returnvalues.CLIENT_ERROR)

    for pattern in src_list:
        unfiltered_match = glob.glob(base_dir + pattern)
        match = []
        for server_path in unfiltered_match:
            real_path = os.path.abspath(server_path)
            if not valid_user_path(real_path, base_dir):

                # out of bounds - save user warning for later to allow partial match
                # ../*/* is technically allowed to match own files.

                logger.error('Warning: %s tried to %s %s outside own home! (%s)'
                              % (cert_name_no_spaces, op_name,
                             real_path, pattern))
                continue
            match.append(real_path)

        # Now actually treat list of allowed matchings and notify if no (allowed) match

        if not match:
            output_objects.append({'object_type': 'file_not_found',
                                  'name': pattern})
            status = returnvalues.FILE_NOT_FOUND

        for real_path in match:
            relative_path = real_path.replace(base_dir, '')
            if verbose(flags):
                output_objects.append({'object_type': 'file', 'name'
                        : relative_path})

            # src must be a file unless recursive is specified

            if not recursive(flags) and os.path.isdir(real_path):
                output_objects.append({'object_type': 'warning', 'text'
                        : 'skipping directory src %s!' % relative_path})

            # If destination is a directory the src should be copied there

            if os.path.isdir(real_dest):
                real_target = real_dest + os.sep\
                     + os.path.basename(real_path)
            try:
                if recursive(flags) and os.path.isdir(real_path):
                    shutil.copytree(real_path, real_dest)
                else:
                    shutil.copy(real_path, real_target)
            except Exception, exc:
                output_objects.append({'object_type': 'error_text',
                        'text': "%s: '%s': %s" % (op_name,
                        relative_path, exc)})
                logger.error("%s: failed on '%s': %s" % (op_name,
                             relative_path, exc))
                status = returnvalues.SYSTEM_ERROR

    return (output_objects, status)

