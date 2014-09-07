#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# addvgridtrigger - add vgrid trigger
# Copyright (C) 2003-2014  The MiG Project lead by Brian Vinter
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

"""Add a trigger to a given vgrid"""

import os
import time

from shared.defaults import any_state, keyword_auto, valid_trigger_actions, \
      valid_trigger_changes
from shared.functional import validate_input_and_cert, REJECT_UNSET
from shared.handlers import correct_handler
from shared.init import initialize_main_variables
from shared.vgrid import init_vgrid_script_add_rem, vgrid_is_trigger, \
     vgrid_list_subvgrids, vgrid_add_triggers, vgrid_is_owner_or_member
import shared.returnvalues as returnvalues


def signature():
    """Signature of the main function"""

    defaults = {'vgrid_name': REJECT_UNSET,
                'rule_id': [keyword_auto],
                'path': REJECT_UNSET,
                'changes': [any_state],
                'run_as': [keyword_auto],
                'action': [keyword_auto],
                'arguments': [''],
                }
    return ['', defaults]


def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(client_id, op_header=False)
    defaults = signature()[1]
    output_objects.append({'object_type': 'header', 'text'
                          : 'Add VGrid Trigger'})
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

    if not correct_handler('POST'):
        output_objects.append(
            {'object_type': 'error_text', 'text'
             : 'Only accepting POST requests to prevent unintended updates'})
        return (output_objects, returnvalues.CLIENT_ERROR)

    # strip leftmost slashes from all fields used in filenames to avoid
    # interference with os.path.join
    # merge multi args into one string and split again to get flat array
    rule_id = accepted['rule_id'][-1]
    vgrid_name = accepted['vgrid_name'][-1].lstrip(os.sep)
    path = accepted['path'][-1].lstrip(os.sep)
    changes = [i.strip() for i in ' '.join(accepted['changes']).split()]
    run_as = accepted['run_as'][-1]
    action = accepted['action'][-1]
    arguments = [i.strip() for i in ' '.join(accepted['arguments']).split()]

    # we just use a high res timestamp as automatic rule_id
    
    if rule_id == keyword_auto:
        rule_id = "%d" % (time.time() * 1E8)

    # default to run as user adding rule
    
    if run_as == keyword_auto:
        run_as = client_id

    if action not in valid_trigger_actions:
        action = valid_trigger_actions[0]

    if any_state in changes:
        changes = valid_trigger_changes

    # Validity of user and vgrid names is checked in this init function so
    # no need to worry about illegal directory traversal through variables

    (ret_val, msg, ret_variables) = \
        init_vgrid_script_add_rem(vgrid_name, client_id,
                                  rule_id, 'trigger',
                                  configuration)
    if not ret_val:
        output_objects.append({'object_type': 'error_text', 'text'
                              : msg})
        return (output_objects, returnvalues.CLIENT_ERROR)
    elif msg:

        # In case of warnings, msg is non-empty while ret_val remains True

        output_objects.append({'object_type': 'warning', 'text': msg})

    # we only allow owners/members to have triggers associated

    if not vgrid_is_owner_or_member(vgrid_name, run_as, configuration):
        output_objects.append({'object_type': 'error_text', 'text': 
                    'Only owners of %s can own triggers.' % vgrid_name })
        return (output_objects, returnvalues.CLIENT_ERROR)

    # don't add if already in vgrid or parent vgrid

    if vgrid_is_trigger(vgrid_name, rule_id, configuration):
        output_objects.append({'object_type': 'error_text', 'text'
                              : '%s is already a trigger in the vgrid'
                               % rule_id})
        return (output_objects, returnvalues.CLIENT_ERROR)

    # don't add if already in subvgrid

    (status, subvgrids) = vgrid_list_subvgrids(vgrid_name,
            configuration)
    if not status:
        output_objects.append({'object_type': 'error_text', 'text'
                              : 'Error getting list of subvgrids: %s'
                               % subvgrids})
        return (output_objects, returnvalues.SYSTEM_ERROR)
    for subvgrid in subvgrids:
        if vgrid_is_trigger(subvgrid, rule_id, configuration):
            output_objects.append({'object_type': 'error_text', 'text'
                                  : '''%s is already in a sub-vgrid (%s).
Remove the trigger from the subvgrid and try again''' % \
                                   (rule_id, subvgrid)})
            return (output_objects, returnvalues.CLIENT_ERROR)

    for change in changes:
        if not change in valid_trigger_changes:
            output_objects.append({'object_type': 'error_text', 'text'
                              : "found invalid change value %s" % change})
            return (output_objects, returnvalues.CLIENT_ERROR)

    rule_dict = {'rule_id': rule_id,
                 'vgrid_name': vgrid_name,
                 'path': path,
                 'changes': changes,
                 'run_as': run_as,
                 'action': action,
                 'arguments': arguments,
                 }

    # Add to list and pickle

    (add_status, add_msg) = vgrid_add_triggers(configuration, vgrid_name,
                                                [rule_dict])
    if not add_status:
        output_objects.append({'object_type': 'error_text', 'text': '%s'
                               % add_msg})
        return (output_objects, returnvalues.SYSTEM_ERROR)

    output_objects.append({'object_type': 'text', 'text'
                          : 'New trigger %s successfully added to %s vgrid!'
                           % (rule_id, vgrid_name)})
    output_objects.append({'object_type': 'link', 'destination':
                           'adminvgrid.py?vgrid_name=%s' % vgrid_name, 'text':
                           'Back to administration for %s' % vgrid_name})
    return (output_objects, returnvalues.OK)
