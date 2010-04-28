#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# showre - Display a runtime environment
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

"""Get info about a runtime environtment"""

import time
import base64
import fcntl
import os

import shared.returnvalues as returnvalues
from shared.functional import validate_input_and_cert, REJECT_UNSET
from shared.init import initialize_main_variables, find_entry
from shared.refunctions import is_runtime_environment, get_re_dict, del_re, del_re_from_resources
from shared.vgridaccess import user_visible_resources, get_resource_map,get_vgrid_map, OWNERS, CONF




def signature():
    """Signature of the main function"""

    defaults = {'re_name': REJECT_UNSET}
    return ['runtimeenvironment', defaults]



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

    re_name = accepted['re_name'][-1]


    #In order to ensure referential integrity, the RTE re_name must be removed from
    #all resources that has an entry for re_name: 
    
    #getting a map of all resources
    res_map = get_resource_map(configuration)

    #The RTE re_name is removed from all reources that has an entry for re_name
    (status, msg) = del_re_from_resources(res_map, re_name, configuration)

    #If something goes wrong when removing re_name form reources, an error is displayed.
    if not status:
        title_entry = find_entry(output_objects, 'title')
        title_entry['text'] = 'Runtimeenviroment deletion failed.'
        output_objects.append({'object_type': 'header', 'text'
                           : 'Failed to delete runtimeenvironment ' + re_name})
        output_objects.append({'object_type': 'error_text', 'text'
                               : "Resources lists of RTE's maybe inconsistent: %s" % msg})
        
        return (output_objects, returnvalues.SYSTEM_ERROR)
        


    #The RTE re_name is deleted.
    (status, msg) = del_re(re_name, configuration)

    
    #If something goes wrong when trying to delete RTE re_name,
    #an error is displayed.
    if not status:
        title_entry = find_entry(output_objects, 'title')
        title_entry['text'] = 'Runtimeenviroment deletion failed.'
        output_objects.append({'object_type': 'header', 'text'
                           : 'Failed to delete runtimeenvironment ' + re_name})
        output_objects.append({'object_type': 'error_text', 'text'
                               : 'Could not read existing runtime environment details. %s' % msg})
        return (output_objects, returnvalues.SYSTEM_ERROR)

    #If deletion of RTE re_name is successfull, we just returns OK
    else:

         title_entry = find_entry(output_objects, 'title')
         title_entry['text'] = 'Runtimeenviroment has been deleted'
         output_objects.append({'object_type': 'header', 'text'
                           : 'Succesfully deleted runtime enviroment ' + re_name})

         output_objects.append({'object_type': 'link', 'destination': 'redb.py',
                               'class': 'infolink', 'title': 'Show runtime enviroments',
                               'text': 'Show runtime enviroments'})

           
         return (output_objects, returnvalues.OK) 
 
