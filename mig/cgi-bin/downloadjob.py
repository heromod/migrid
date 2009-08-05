#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# downloadjob.py - download output files for a particular job_id
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

"""Script for uploading a proxy to a specific location"""

import cgi
import cgitb
cgitb.enable()

from shared.cgiscriptstub import run_cgi_script

# the functionality we implement... could go into shared/functionality/

import os
from shared.init import initialize_main_variables
from shared.functional import validate_input_and_cert, REJECT_UNSET
import shared.returnvalues as returnvalues
from shared.useradm import client_id_dir
import shared.arcwrapper as arc

def signature():
    """Signature of the main function"""

    defaults = {'job_id':REJECT_UNSET}
    return ['html_form', defaults]

def download(client_id, user_args_dict):
    """Main function used by front end"""
    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables()
    client_dir = client_id_dir(client_id)
    defaults = signature()[1]
    (validate_status, accepted) = validate_input_and_cert(
        user_args_dict,
        defaults,
        output_objects,
        client_id,
        configuration,
        allow_rejects=False,
        )
    if not validate_status:
        return (accepted, returnvalues.CLIENT_ERROR)

    output_objects.append({'object_type': 'header', 'text' :
                           "MiG: Job result download"})

    output_objects.append({'object_type': 'sectionheader', 'text' :
                           "Minimum intrusion Grid: ARC backend prototype"})

    # provide information about the job
    try:
        job_id = accepted['job_id'][-1]
        dir = os.path.join(configuration.user_home,client_dir)
        session_Ui = arc.Ui(dir)
        logger.debug('download request for job %s' % job_id)
        files = session_Ui.getResults(job_id, dir)

    except arc.NoProxyError, err:
        
        output_objects.append({'object_type':'error_text',
                               'text': 'Problem with proxy file: %s' \
                                       % err.what()})
        output_objects = output_objects + arc.askProxy()
        return (output_objects, returnvalues.ERROR)
    except Exception, err:
        output_objects.append({'object_type':'error_text',
                               'text': 'Download failed.\n %s' % err})
        return (output_objects, returnvalues.ERROR)

    if not files:
        output_objects.append(\
            {'object_type':'error_text',
             'text': 'No files downloadad.'})
    else:
        output_objects.append(\
            {'object_type':'text',
             'text': 'Files downloaded: %s'})

        for f in files:
            output_objects.append(\
                    {'object_type':'text',
                     'text': '%s' % f })

    return (output_objects, returnvalues.OK)

# the call
run_cgi_script(download)

