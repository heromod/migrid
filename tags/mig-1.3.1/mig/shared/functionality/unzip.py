#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# unzip - [insert a few words of module description on this line]
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

"""Archiver used to unpack one or more zip files in the home directory of a
MiG user into a given destination directory.
"""

import os
import zipfile
import glob

import shared.returnvalues as returnvalues
from shared.functional import validate_input_and_cert, REJECT_UNSET
from shared.init import initialize_main_variables, find_entry
from shared.parseflags import verbose
from shared.upload import handle_package_upload
from shared.useradm import client_id_dir
from shared.validstring import valid_user_path


def signature():
    """Signature of the main function"""

    defaults = {'src': REJECT_UNSET, 'flags': [''],
                'dst': REJECT_UNSET}
    return ['link', defaults]


def usage(output_objects):
    output_objects.append({'object_type': 'header', 'text': 'unzip usage:'
                          })
    output_objects.append({'object_type': 'text', 'text'
                          : 'SERVER_URL/unzip.py?[output_format=(html|txt|xmlrpc|..);][flags=h;][src=src_path;[...]]src=src_path;dst=dst_path'
                          })
    output_objects.append({'object_type': 'text', 'text'
                          : '- output_format specifies how the script should format the output'
                          })
    output_objects.append({'object_type': 'text', 'text'
                          : '- flags is a string of one character flags to be passed to the script'
                          })
    output_objects.append({'object_type': 'text', 'text'
                          : '- each src specifies a zip file in your home to extract'
                          })
    output_objects.append({'object_type': 'text', 'text'
                          : '- dst is the path where the extracted zip archive contents will be stored'
                          })
    return (output_objects, returnvalues.OK)


def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(client_id, op_header=False)
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
    dst = accepted['dst'][-1]
    pattern_list = accepted['src']

    # Please note that base_dir must end in slash to avoid access to other
    # user dirs when own name is a prefix of another user name

    base_dir = os.path.abspath(os.path.join(configuration.user_home,
                               client_dir)) + os.sep

    title_entry = find_entry(output_objects, 'title')
    title_entry['text'] = 'Zip archive extractor'
    output_objects.append({'object_type': 'header', 'text'
                          : 'Zip archive extractor'})

    if verbose(flags):
        for flag in flags:
            output_objects.append({'object_type': 'text', 'text'
                                  : '%s using flag: %s' % (op_name,
                                  flag)})

    if 'h' in flags:
        usage(output_objects)

    real_dest = os.path.join(base_dir, dst.lstrip(os.sep))

    # Don't use real_path in output as it may expose underlying
    # fs layout.

    relative_dest = real_dest.replace(base_dir, '')
    if not valid_user_path(real_dest, base_dir, True):

        # out of bounds

        output_objects.append({'object_type': 'error_text', 'text'
                              : "You're only allowed to write to your own home directory! dest (%s) expands to an illegal path (%s)"
                               % (dst, relative_dest)})
        logger.error('Warning: %s tried to %s file(s) to destination %s outside own home! (using pattern %s)'
                      % (client_id, op_name, real_dest, dst))
        return (output_objects, returnvalues.CLIENT_ERROR)

    status = returnvalues.OK

    for pattern in pattern_list:

        # Check directory traversal attempts before actual handling to avoid
        # leaking information about file system layout while allowing
        # consistent error messages

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

            if not os.path.isfile(real_path) or \
                   not real_path.lower().endswith('.zip'):
                output_objects.append({'object_type': 'error_text', 'text'
                                       : "ignoring non-zip-file target: %s"
                                       % relative_path})
                status = returnvalues.CLIENT_ERROR
                continue

            (unpack_status, msg) = handle_package_upload(real_path,
                                                         relative_path,
                                                         client_id,
                                                         configuration,
                                                         False, real_dest)
            if not unpack_status:
                output_objects.append({'object_type': 'error_text',
                                       'text': 'Error: %s' % msg})
                status = returnvalues.CLIENT_ERROR
                continue
            output_objects.append({'object_type': 'text', 'text'
                                   : 'Zip archive %s unpacked into %s'
                                   % (relative_path, relative_dest)})

    return (output_objects, status)