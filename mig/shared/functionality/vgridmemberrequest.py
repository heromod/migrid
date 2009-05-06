#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# vgridmemberrequest - [insert a few words of module description on this line]
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

"""Request VGrid membership back end"""

import sys
import os
from shared.init import initialize_main_variables
from shared.functional import validate_input_and_cert, REJECT_UNSET
import shared.returnvalues as returnvalues


def signature():
    defaults = {}
    return ['html_form', defaults]


def main(cert_name_no_spaces, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(op_header=False, op_title=False)
    output_objects.append({'object_type': 'title', 'text'
                          : 'MiG VGrid membership request'})
    output_objects.append({'object_type': 'header', 'text'
                          : 'Request VGrid member or ownership'})

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

    output_objects.append({'object_type': 'warning', 'text'
                          : '''
Remember that sending a vgrid membership or ownership request
generates a message to the owners of the VGrid. All requests are 
logged together with the submitters name. Spamming and other misuse
will not be tolerated!'''})

    output_objects.append({'object_type': 'html_form', 'text'
                          : """
    <form method='post' action='/cgi-bin/vgridmemberrequestaction.py'>
<table align='center'><tr><td>
VGrid name</td><td><input name=vgrid_name> </td></tr>
<tr><td>Type</td><td><select name=request_type><option name=member>Member</option><option name=owner>Owner</option></select></td></tr>
<tr><td>Reason (text to VGrid owner)</td><td><input name=request_text size=40></td></tr>
<tr><td><input type='submit' value='Submit'></td><td></td></tr></table>
</form>"""})

    return (output_objects, returnvalues.OK)


