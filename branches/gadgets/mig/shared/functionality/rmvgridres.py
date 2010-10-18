#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# rmvgridres - [insert a few words of module description on this line]
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

"""Remove a resource from a given vgrid"""

import os

from shared.validstring import cert_name_format
from shared.listhandling import remove_item_from_pickled_list
from shared.vgrid import init_vgrid_script_add_rem, vgrid_is_owner
from shared.init import initialize_main_variables
from shared.functional import validate_input_and_cert, REJECT_UNSET
import shared.returnvalues as returnvalues


def signature():
    defaults = {'vgrid_name': REJECT_UNSET,
                'unique_resource_name': REJECT_UNSET}
    return ['text', defaults]


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
    vgrid_name = accepted['vgrid_name'][-1]
    unique_resource_name = accepted['unique_resource_name'][-1].lower()

    # Validity of user and vgrid names is checked in this init function so
    # no need to worry about illegal directory traversal through variables

    (ret_val, msg, ret_variables) = \
        init_vgrid_script_add_rem(vgrid_name, cert_name_no_spaces,
                                  unique_resource_name, 'resource',
                                  configuration)
    if not ret_val:
        output_objects.append({'object_type': 'error_text', 'text'
                              : msg})
        return (output_objects, returnvalues.CLIENT_ERROR)
    elif msg:

        # In case of warnings, msg is non-empty while ret_val remains True

        output_objects.append({'object_type': 'warning', 'text': msg})

    if not vgrid_is_owner(vgrid_name, cert_name_no_spaces,
                          configuration):
        output_objects.append({'object_type': 'error_text', 'text'
                              : 'You must be an owner of the vgrid to remove a vgrid resource!'
                              })
        return (output_objects, returnvalues.CLIENT_ERROR)

    # remove

    resources_file = configuration.vgrid_home + os.sep + vgrid_name\
         + os.sep + 'resources'
    (status, msg) = remove_item_from_pickled_list(resources_file,
            unique_resource_name, logger)
    if not status:
        output_objects.append({'object_type': 'error_text', 'text'
                              : msg})
        output_objects.append({'object_type': 'error_text', 'text'
                              : '%s might be listed as a resource of this VGrid because it is a resource of a parent VGrid. Removal must be performed from the most significant VGrid possible.'
                               % unique_resource_name})
        return (output_objects, returnvalues.SYSTEM_ERROR)

    output_objects.append({'object_type': 'text', 'text'
                          : 'Resource %s successfully removed from %s vgrid!'
                           % (unique_resource_name, vgrid_name)})
    return (output_objects, returnvalues.OK)

