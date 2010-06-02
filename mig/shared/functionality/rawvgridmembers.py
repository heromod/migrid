#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# adminvgrid - [insert a few words of module description on this line]
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

"""List owners, members, res's and show html controls to administrate a vgrid"""

import shared.returnvalues as returnvalues
from shared.functional import validate_input_and_cert, REJECT_UNSET
from shared.init import initialize_main_variables, find_entry
from shared.vgrid import vgrid_list, vgrid_is_owner


def signature():
    """Signature of the main function"""

    defaults = {'vgrid_name': REJECT_UNSET}
    return ['html_form', defaults]


def vgrid_add_remove_table(vgrid_name, 
                           item_string, 
                           script_suffix, 
                           configuration):

    (status, msg) = vgrid_list(vgrid_name, '%ss' % item_string, configuration)
    if not status:
        out.append({'object_type': 'error_text',
                    'text': msg })
        return (False, out)

    # success, so msg is a list of user names (DNs) or unique resource ids
    if len(msg) <= 0:
        out.append({'object_type': 'text', 
                    'text': 'No %ss found!' % str.title(item_string)
                    })
    else:
        form = '''
      <form method="get" action="rm%(scriptname)s.py">
        <input type="hidden" name="vgrid_name" value="%(vgrid)s" />
        Current %(item)ss of %(vgrid)s:
        <table class="vgrid%(item)s">
          <thead><tr><th>Remove</th><th>Owner</th></thead>
          <tbody>
''' % { 'item': item_string,
        'scriptname': script_suffix,
        'vgrid': vgrid_name }

        for elem in msg:
            if elem:
                form += \
"          <tr><td><input type=radio name='%s' value='%s' /></td><td>%s</td></tr>"\
                     % (qu_string, elem, elem)
        form += '              </tbody></table>'
    
    return (True, out)

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
    vgrid_name = accepted['vgrid_name'][-1]

    output_objects.append({'object_type': 'header', 'text'
                          : "Administrate '%s'" % vgrid_name })

    if not vgrid_is_owner(vgrid_name, client_id, configuration):

        output_objects.append({'object_type': 'error_text', 'text': 
                    'Only owners of %s can extract this list.' % vgrid_name })

        output_objects.append({'object_type': 'link',
                               'destination':
                               'vgridmemberrequestaction.py?vgrid_name=%s&request_type=owner&request_text=no+text' % vgrid_name,
                               'class': 'addadminlink',
                               'title': 'Request ownership of %s' % vgrid_name,
                               'text': 'Apply to become an owner'})

        return (output_objects, returnvalues.SYSTEM_ERROR)



    (status, os) = vgrid_list(vgrid_name, 'owners', configuration)
    if not status:
        output_objects.append({'object_type': 'error_text',
                               'text': os })
        return (output_objects, returnvalues.SYSTEM_ERROR)

    (status, ms) = vgrid_list(vgrid_name, 'members', configuration)
    if not status:
        output_objects.append({'object_type': 'error_text',
                               'text': ms })

    list = [o for o in (os + ms) if o != '']

    output_objects = [{'object_type': 'start',
                       'headers': [('Content-Type','text/plain')]},
                      {'object_type':'html_form','text':'\n'.join(list)},
                      {'object_type': 'script_status'},
                      {'object_type': 'end'}]

    return (output_objects, returnvalues.OK)

