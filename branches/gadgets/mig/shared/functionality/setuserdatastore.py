#!/usr/bin/env python
# encoding: utf-8
"""
setuserdatastore - sets data in the specified userdata store
Note that the userdatastore is a fixed pickled dictionary. Getting/setting the 
store means getting/setting the value of a specific key (called module) in that
dictionary.

Unlike most scripts this does not have any knowledge of HTML at all, 
nor is it callable as a CGI script.

Created by Jan Wiberg on 2009-06-23.
"""

__version__ = '$Revision$'

import os
import pickle

from shared.validstring import valid_user_path
from shared.init import initialize_main_variables
from shared.functional import validate_input_and_cert
import shared.returnvalues as returnvalues

def signature():
    defaults = {'module': [''], 'data': ['']}
    return ['html_form', defaults]

def main(cert_name_no_spaces, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, _) = \
        initialize_main_variables(op_title=False, op_header=False)
    defaults = signature()[1]
    (validate_status, accepted) = validate_input_and_cert(
        user_arguments_dict,
        defaults,
        output_objects,
        cert_name_no_spaces,
        configuration,
        allow_rejects=False,
        )
        
    logger.info("Loaded setuserdatastore")
    if not validate_status:
        return (accepted, returnvalues.CLIENT_ERROR)
                
    module = accepted['module'][-1]
    module = accepted['data'][-1]

    logger.info("setuserdatastore.module %s, data %s" % (module, data))

    # Please note that base_dir must end in slash to avoid access to other
    # user dirs when own name is a prefix of another user name

    base_dir = os.path.abspath(configuration.user_home + os.sep
                                + cert_name_no_spaces) + os.sep

    # the client can choose to specify the path of the target directory with
    # current_dir + "/" + path, instead of specifying the complete path in
    # subdirs. This is usefull from ls.py where a hidden html control makes it
    # possible to target the directory from the current dir.

    output_objects.append({'object_type': 'header', 'text'
                          : 'Internal setuserdatastore operation'})

    if not module:
        output_objects.append({'object_type': 'error_text', 'text'
                              : 'No module supplied'})
        return (output_objects, returnvalues.CLIENT_ERROR)

    real_path = os.path.abspath(base_dir + configuration.gadget_server_userdatastore)
    
    if not valid_user_path(real_path, base_dir):
        output_objects.append({'object_type': 'error_text', 'text'
                              : "Unable to load the user data store %s." % configuration.gadget_server_userdatastore })
        return (output_objects, returnvalues.CLIENT_ERROR) # not really a client error
        
    if not os.path.isfile(real_path):
        # make it
        logger.debug("'%s' not available for user %s. Creating with empty dictionary." % (real_path, cert_name_no_spaces))
        data = {}
        filedescriptor = open(real_path, 'wb')
        pickle.dump(data, filedescriptor)
        filedescriptor.close();
        
    filedescriptor = open(real_path, 'rwb')
    filedata = pickle.load(filedescriptor)
    logger.info("filedata: %s" % filedata)
    filedata[module] = data
    pickle.dump(filedata, filedescriptor)
    filedescriptor.close()        
     
    return (output_objects, returnvalues.OK)

