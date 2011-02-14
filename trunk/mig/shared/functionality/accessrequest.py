#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# accessrequest - let user request access to vgrid or resource
# Copyright (C) 2003-2010  The MiG Project lead by Brian Vinter
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

"""Request access (ownership or membership) back end"""

import shared.returnvalues as returnvalues
from shared.functional import validate_input_and_cert
from shared.init import initialize_main_variables, find_entry


def signature():
    """Signature of the main function"""

    defaults = {}
    return ['html_form', defaults]


def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(client_id, op_header=False)
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

    title_entry = find_entry(output_objects, 'title')
    title_entry['text'] = '%s access request' % \
                          configuration.short_title
    output_objects.append({'object_type': 'header', 'text'
                          : 'Request access (membership/ownership)'})

    output_objects.append({'object_type': 'warning', 'text'
                          : '''
Remember that sending a membership or ownership request
generates a message to the owners of the target. All requests are 
logged together with the ID of the submitter. Spamming and other abuse
will not be tolerated!'''})

    output_objects.append({'object_type': 'sectionheader', 'text'
                          : 'Request VGrid membership/ownership'})
    output_objects.append({'object_type': 'html_form', 'text'
                          : """
<form method='post' action='accessrequestaction.py'>
<table align='center'>
<tr><td>Request type</td><td><select name=request_type>
<option value=vgridmember>VGrid membership</option>
<option value=vgridowner>VGrid ownership</option>
</select></td></tr>
<tr><td>
VGrid name </td><td><input name=vgrid_name />
</td></tr>
<tr>
<td>Reason (text to owners)</td><td><input name=request_text size=40 /></td>
</tr>
<tr><td><input type='submit' value='Submit' /></td><td></td></tr></table>
</form>"""})

    output_objects.append({'object_type': 'sectionheader', 'text'
                          : 'Request resource ownership'})
    output_objects.append({'object_type': 'html_form', 'text'
                          : """
<form method='post' action='accessrequestaction.py'>
<table align='center'>
<tr><td>Request type</td><td><select name=request_type>
<option value=resourceowner>Resource ownership</option>
</select></td></tr>
<tr><td>
Resource ID </td><td><input name=unique_resource_name />
</td></tr>
<tr>
<td>Reason (text to owners)</td><td><input name=request_text size=40 /></td>
</tr>
<tr><td><input type='submit' value='Submit' /></td><td></td></tr></table>
</form>"""})

    return (output_objects, returnvalues.OK)