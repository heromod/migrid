#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# viewres - Display public details about a resource
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

"""Get info about a resource"""

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

    title_entry = find_entry(output_objects, 'title')
    title_entry['text'] = 'Resource Deletion'
    output_objects.append({'object_type': 'header', 'text'
                          : 'Deleting resource'})

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


    #Check to verify that a resource is down.
    #On resources that are down may be deleted.

    resource_config_file = os.path.join(res_dir, 'config')
    resource_config = load(resource_config_file)
    exe = resource_config['EXECONFIG'][0]['name']
    
    last_req_file = os.path.join(configuration.resource_home,
                                 res_name,
                                 'last_request.%s' % exe)


    last_request = load(last_req_file)
    last_status = last_request['STATUS']

    if not last_status == "down?":
        output_objects.append({'object_type': 'text', 'text'
                               : 'You must take down the resource before deleting it!'})

        output_objects.append({'object_type': 'link', 'destination': 'resman.py',
                               'class': 'infolink', 'title': 'Show resources',
                               'text': 'Show resources'})
         
        status = returnvalues.CLIENT_ERROR
        lock_handle_vgrid.close()
        lock_handle_res.close()
        return (output_objects, status)
        
    

 

    #The resource is removed from all vgrids, the resource is a member of:    
    #Iterate through all vgrids, removing the resource res_name from the vgrids
    #that has an entry for res_name
    for vgrid in vgrid_map['__vgrids__']:
        if not vgrid == "Generic":
             if res_name in vgrid_map['__vgrids__'][vgrid]:
                 vgrid_map['__vgrids__'][vgrid].remove(res_name)
                 conf_path = os.path.join(configuration.vgrid_home, vgrid, "resources")
                 dump(vgrid_map['__vgrids__'][vgrid], conf_path)





    #Deleting the reosurce files, including vgrid.map and resource.map
    #shutil.rmtree is used, because a resource consists of multiple
    #files in a directory.
    
    
    
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
