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
from shared.conf import get_resource_configuration
from shared.functional import validate_input_and_cert, REJECT_UNSET
from shared.init import initialize_main_variables, find_entry
from shared.resconfkeywords import get_resource_keywords, get_exenode_keywords
from shared.resource import anon_to_real_res_map
from shared.vgridaccess import user_visible_resources, user_allowed_vgrids, \
     get_resource_map, get_vgrid_map, CONF

from shared.serial import load, dump
import os
import fcntl
import shutil

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
    vgrid_map = get_vgrid_map(configuration)


    #Locking the access to resources and vgrids.
    lock_path_vgrid = os.path.join(configuration.resource_home, "vgrid.lock")
    lock_handle_vgrid = open(lock_path_vgrid, 'a')

    fcntl.flock(lock_handle_vgrid.fileno(), fcntl.LOCK_EX)

    lock_path_res = os.path.join(configuration.resource_home, "resource.lock")
    lock_handle_res = open(lock_path_res, 'a')

    fcntl.flock(lock_handle_res.fileno(), fcntl.LOCK_EX)



    #Check whether the resource is a member of a vgrid.
    #If so, the resource can't be deleted.
    res_active = False
    vgrids = []
    
    for vgrid in vgrid_map['__vgrids__']:
        if res_name in vgrid_map['__vgrids__'][vgrid]:
           vgrids.append(vgrid)
           res_active = True
        


    if res_active:
        title_entry = find_entry(output_objects, 'title')
        title_entry['text'] = 'Resource deletion failed.'
        output_objects.append({'object_type': 'header', 'text'
                           : 'Failed to delete resource ' + res_name})

        output_objects.append({'object_type': 'text', 'text'
                           : "Could not delete resource " + res_name
                               + "because it is still member of:"})

        output_objects.append({'object_type': 'list', 'list'
                           : vgrids})

        output_objects.append({'object_type': 'link', 'destination': 'resman.py',
                               'class': 'infolink', 'title': 'Show resources',
                               'text': 'Show resources'})
                
        return (output_objects, returnvalues.OK)


    #If the reource is not a member of a vgrid, it is deleted.
    try:
         shutil.rmtree(res_dir)
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
    title_entry = find_entry(output_objects, 'title')
    title_entry['text'] = 'Resource Deletion'
    output_objects.append({'object_type': 'header', 'text'
                          : 'Deleting resource'})
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
