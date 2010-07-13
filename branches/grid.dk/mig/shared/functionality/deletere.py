#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#

# deletere - Deletes a runtimeenvironment
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


"""Deletion of  runtimeenvironments"""


import time
import base64
import fcntl
import os

import shared.returnvalues as returnvalues
from shared.functional import validate_input_and_cert, REJECT_UNSET
from shared.init import initialize_main_variables, find_entry
from shared.refunctions import is_runtime_environment, \
     get_re_dict, del_re, is_re_active

from shared.vgridaccess import user_visible_resources, \
     get_resource_map,get_vgrid_map, OWNERS, CONF




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

    #Check whether re_name represents a runtimeenvironment.
    if not is_runtime_environment(re_name, configuration):
        output_objects.append({'object_type': 'error_text','text': \
            'Runtime environment %s does not exists!'%re_name})
        return (output_objects, returnvalues.SYSTEM_ERROR)
    

    re_dict = get_re_dict(re_name, configuration)


    #Verifying that the RTE belongs to the user, that tries to delete it.
    if not re_dict[0]:
        output_objects.append({'object_type': 'error_text','text': \
        'Could not read runtime environment details for runtime environment %s'%re_name})
        return (output_objects, returnvalues.SYSTEM_ERROR)

    
    if not client_id == re_dict[0]['CREATOR']:
        output_objects.append({'object_type': 'error_text','text': \
        'You are not the owner of runtime environment "%s"' %re_name})
        return (output_objects, returnvalues.SYSTEM_ERROR)

    #getting a map of all resources
    res_map = get_resource_map(configuration)


    #Check if the RTE is used by resources. If so, it can not be deleted.
    (status, actives) = is_re_active(res_map, re_name, configuration)

    #If the RTE is active, an error message is printet, and a list of the
    #resorces that uses the RTE is printet.
    if status:
        title_entry = find_entry(output_objects, 'title')
        title_entry['text'] = 'Runtimeenviroment deletion failed.'
        output_objects.append({'object_type': 'header', 'text'
                           : 'Failed to delete runtimeenvironment ' + re_name})

        output_objects.append({'object_type': 'text', 'text'
                           : "Could not delete runtimeenvironment " + re_name
                               + "because it is still used by resources:"})

        output_objects.append({'object_type': 'list', 'list'
                           : actives})

        output_objects.append({'object_type': 'link', 'destination': 'redb.py',
                               'class': 'infolink', 'title': 'Show runtime enviroments',
                               'text': 'Show runtime enviroments'})
                
        return (output_objects, returnvalues.OK)
        


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
 
