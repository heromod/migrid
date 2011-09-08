#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# jobobjsubmit - [insert a few words of module description on this line]
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

# Minimum Intrusion Grid

"""
"""

import os
import sys
import glob
import shared.mrslkeywords as mrslkeywords
from shared.conf import get_resource_configuration
from shared.refunctions import get_re_dict, list_runtime_environments
from shared.fileio import unpickle
from shared.init import initialize_main_variables
from shared.functional import validate_input_and_cert, REJECT_UNSET
import shared.returnvalues as returnvalues
from shared.job import new_job, create_job_object_from_pickled_mrsl
import tempfile


def signature():
    defaults = {'EXECUTE': REJECT_UNSET}
    external_dict = mrslkeywords.get_keywords_dict(configuration)

    for (key, value_dict) in external_dict.iteritems():
        if not defaults.has_key(key):

            # do not overwrite

            defaults[key] = []
    return ['html_form', defaults]


def main(cert_name_no_spaces, user_arguments_dict):
    """Main function used by front end"""

    global configuration
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

    external_dict = mrslkeywords.get_keywords_dict(configuration)
    spec = []
    for (key, value_dict) in external_dict.iteritems():
        attrName = key
        if user_arguments_dict.has_key(attrName):
            spec.append('::%s::' % attrName)
            attr = user_arguments_dict[attrName]

            # output_objects.append({"object_type":"text", "text":attrName})

            # FIXME: this type check is not perfect... I should be
            # able to extend on any sequence...

            if isinstance(attr, list):
                spec.extend(attr)
            elif isinstance(attr, tuple):
                spec.extend(attr)
            else:
                spec.append(attr)

            # if appendNewline:

            spec.append('')

    mrsl = ''
    for line in spec:
        mrsl += line + """
"""
    output_objects.append({'object_type': 'text', 'text': '%s' % mrsl})

    tmpfile = None

    # save to temporary file

    try:
        (filehandle, tmpfile) = tempfile.mkstemp(text=True)
        os.write(filehandle, mrsl)
        os.close(filehandle)
    except Exception, err:
        status = False

    (status, newmsg, job_id) = new_job(tmpfile, cert_name_no_spaces,
            configuration, False, True)
    if not status:
        output_objects.append({'object_type': 'error_text', 'text'
                              : newmsg})
        return (output_objects, returnvalues.CLIENT_ERROR)
    base_dir = os.path.abspath(configuration.mrsl_files_dir + os.sep
                                + cert_name_no_spaces)

    ret_status = returnvalues.OK

    # job = Job()

    filepath = os.path.join(base_dir, job_id)
    filepath += '.mRSL'

    (new_job_obj_status, new_job_obj) = \
        create_job_object_from_pickled_mrsl(filepath, logger,
            external_dict)
    if not new_job_obj_status:
        output_objects.append({'object_type': 'error_text', 'text'
                              : new_job_obj})
        ret_status = returnvalues.CLIENT_ERROR
    else:

        # return new_job_obj

        output_objects.append({'object_type': 'jobobj', 'jobobj'
                              : new_job_obj})
    return (output_objects, ret_status)

