#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# delres - Deletes a resource
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

"""Deletion of a resource"""

import shared.returnvalues as returnvalues
from shared.functional import validate_input_and_cert, REJECT_UNSET
from shared.init import initialize_main_variables, find_entry
from shared.resconfkeywords import get_resource_keywords, get_exenode_keywords
from shared.resource import anon_to_real_res_map
from shared.vgridaccess import  user_allowed_vgrids,\
     get_resource_map,  user_owned_resources

from shared.serial import load, dump
import os
import fcntl

def signature():
    """Signature of the main function"""

    defaults = {'unique_resource_name': REJECT_UNSET}
    return ['resource_info', defaults]





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
    resource_list = accepted['unique_resource_name']
    res_name = resource_list.pop()

    res_dir = os.path.join(configuration.resource_home, res_name)


    #Checking that the user own the reosurce he is trying to delete.
    users_resources = user_owned_resources(configuration, client_id)

    if not res_name in users_resources:
        output_objects.append({'object_type': 'text', 'text'
                                : 'You are not the owner of resource %s. You can not delete a resource you don\'t own!: ' + res_name})

        output_objects.append({'object_type': 'link', 'destination': 'resman.py',
                               'class': 'infolink', 'title': 'Show resources',
                               'text': 'Show resources'})

        status = returnvalues.CLIENT_ERROR
        return (output_objects, status)
        

    #Locking the access to resources and vgrids.
    lock_path_vgrid = os.path.join(configuration.resource_home, "vgrid.lock")
    lock_handle_vgrid = open(lock_path_vgrid, 'a')

    fcntl.flock(lock_handle_vgrid.fileno(), fcntl.LOCK_EX)

    lock_path_res = os.path.join(configuration.resource_home, "resource.lock")
    lock_handle_res = open(lock_path_res, 'a')

    fcntl.flock(lock_handle_res.fileno(), fcntl.LOCK_EX)



    #Check to verify that a resource is down.
    #On resources that are down may be deleted.

    resource_config_file = os.path.join(res_dir, 'config')
    resource_config = load(resource_config_file)
    exe = resource_config['EXECONFIG'][0]['name']
    
    last_req_file = os.path.join(configuration.resource_home,
                                 res_name,
                                 'last_request.%s' % exe)
    

    if not os.path.isfile(last_req_file):
        output_objects.append({'object_type': 'text', 'text'
                               : 'Could not determine wheter the resource %s is busy.'% res_name })

        output_objects.append({'object_type': 'link', 'destination': 'resman.py',
                               'class': 'infolink', 'title': 'Show resources',
                               'text': 'Show resources'})
         
        status = returnvalues.CLIENT_ERROR
        lock_handle_vgrid.close()
        lock_handle_res.close()
        return (output_objects, status)




    #Deleting the reosurce files, but not the resouce directory it self.
    #The resource directory is kept, to prevent hijacking of reource id's

    try:
        for f in os.listdir(res_dir):
            file_path = os.path.join(res_dir, f)
            if os.path.isfile(file_path):
                os.unlink(file_path)
    except Exception, err:
        output_objects.append({'object_type': 'text', 'text'
                                : 'Deletion exception: ' + str(err)})

        output_objects.append({'object_type': 'link', 'destination': 'resman.py',
                               'class': 'infolink', 'title': 'Show resources',
                               'text': 'Show resources'})

        status = returnvalues.CLIENT_ERROR
        lock_handle_vgrid.close()
        lock_handle_res.close()
        return (output_objects, status)
        

            
    #Deleting vgrid.map and resource.map, so that new maps will be generated
    #on the next listing of resources.
   
    try:
        if os.path.exists(os.path.join(configuration.resource_home, 'vgrid.map')):
            os.remove(os.path.join(configuration.resource_home ,'vgrid.map'))

        if os.path.exists(os.path.join(configuration.resource_home, 'resource.map')):
            os.remove(os.path.join(configuration.resource_home ,'resource.map'))

    except Exception, err:
         output_objects.append({'object_type': 'text', 'text'
                               : 'Exception on deleting maps:' + str(err)})

         output_objects.append({'object_type': 'link', 'destination': 'resman.py',
                               'class': 'infolink', 'title': 'Show resources',
                               'text': 'Show resources'})
         
         status = returnvalues.CLIENT_ERROR
         lock_handle_vgrid.close()
         lock_handle_res.close()
         return (output_objects, status)


   


    #The resource has been deleted, and OK is returned.
    title_entry = find_entry(output_objects, 'title')
    title_entry['text'] = 'Resource Deletion'
    output_objects.append({'object_type': 'header', 'text'
                          : 'Deleting resource'})
    
    output_objects.append({'object_type': 'text', 'text'
                           : 'Sucessfully deleted resource: ' + res_name})

    
    output_objects.append({'object_type': 'link', 'destination': 'resman.py',
                               'class': 'infolink', 'title': 'Show resources',
                               'text': 'Show resources'})

    
    #Releasing locks
    lock_handle_vgrid.close()
    lock_handle_res.close()

    status = returnvalues.OK

    return (output_objects, status)
