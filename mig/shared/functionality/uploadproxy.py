#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# upload_proxy - upload a proxy file, then redirect to dashboard
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

import os
from shared.init import initialize_main_variables
from shared.functional import validate_input_and_cert, REJECT_UNSET
import shared.returnvalues as returnvalues
from shared.useradm import client_id_dir
import shared.arcwrapper as arc

def signature():
    """Signature of the main function"""

    defaults = {}
    return ['html_form', defaults]

def upload(client_id, user_args_dict):
    """Main function used by front end"""
    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(op_header=False)
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
                           "MiG: Proxy file upload"})

    output_objects.append({'object_type': 'sectionheader', 'text' :
                           "Minimum intrusion Grid: ARC backend prototype"})

    # provide information about the available proxy
    try:
        dir = os.path.join(configuration.user_home,client_dir)
        session_Ui = arc.Ui(dir)
        proxy = session_Ui.getProxy()
        if proxy.IsExpired():
            # can rarely happen, constructor will throw exception
            output_objects.append({'object_type': 'text', 
                               'text': 'Current proxy has expired.'})
        else:
            output_objects.append({'object_type': 'text', 
                                   'text': 'Proxy for %s' \
                                           % proxy.GetIdentitySN()})
            output_objects.append(\
                {'object_type': 'text', 
                 'text': 'Current proxy will expire on %s (in %s sec.)' \
                         % (proxy.Expires(), proxy.getTimeleft())
                })
    except arc.NoProxyError, err:
        
        output_objects.append({'object_type':'warning',
                               'text': 'Problem with proxy file: %s' \
                                       % err.what()})
    
    output_objects = output_objects + arc.askProxy()

    return (output_objects, returnvalues.OK)
