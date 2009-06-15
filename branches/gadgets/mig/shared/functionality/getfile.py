#!/usr/bin/env python
# encoding: utf-8
"""
getfile.py

# getfile - retrieves a single file from a users MiG filesystem. 
# Unlike most scripts this does not have any knowledge of HTML at all, nor is it callable as a CGI script.
# Based on editor.py. This existing mig file already reads a user file and is assumed to be as safe and bugfree as possible.

Created by Jan Wiberg on 2009-06-09.
"""

__version__ = '$Revision$'

# $Id$

import sys
import os

from shared.validstring import valid_user_path
from shared.init import initialize_main_variables
from shared.functional import validate_input_and_cert, REJECT_UNSET
import shared.returnvalues as returnvalues



def signature():
    defaults = {'path': [''], 'current_dir': ['']}
    return ['html_form', defaults]

def read_file(path, real_path, logger):
    """Reads a file in the users directory"""

    text = ""
    if os.path.isfile(real_path):
        try:
            fd = open(real_path, 'rb')
            text = fd.read() # dont overload with massive reads.
            fd.close()
        except Exception, e:
            return 'Failed to open file %s: %s' % (path, e)
    logger.info("Retrieved text field of size %s" % str(len(text)))

    return (path, text)        


def main(cert_name_no_spaces, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
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
        
    logger.info("Loaded getfile")

    if not validate_status:
        return (accepted, returnvalues.CLIENT_ERROR)
    path = accepted['path'][-1]
    current_dir = accepted['current_dir'][-1]
    # TODO: go through accepted instead but currently this mangles the filename (problem associated with signature?)
    #path = user_arguments_dict['path']

    #logger.info("Retrieved arguments %s vs %s" % (path, user_arguments_dict['path']))
    #logger.info("Retrieved argument types %s vs %s" % (str(type(path)), str(type(user_arguments_dict['path']))))


    # Please note that base_dir must end in slash to avoid access to other
    # user dirs when own name is a prefix of another user name

    base_dir = os.path.abspath(configuration.user_home + os.sep
                                + cert_name_no_spaces) + os.sep

    # the client can choose to specify the path of the target directory with
    # current_dir + "/" + path, instead of specifying the complete path in
    # subdirs. This is usefull from ls.py where a hidden html control makes it
    # possible to target the directory from the current dir.

    output_objects.append({'object_type': 'header', 'text'
                          : 'Internal getfile operation'})

    if not path:
        output_objects.append({'object_type': 'error_text', 'text'
                              : 'No path supplied'})
        return (output_objects, returnvalues.CLIENT_ERROR)

    orig_path = path
    path = os.path.normpath(current_dir + path)
    real_path = os.path.abspath(base_dir + current_dir + path)
    if not valid_user_path(real_path, base_dir):
        # out of bounds!
        output_objects.append({'object_type': 'error_text', 'text'
                              : "You're only allowed to edit your own files! (%s expands to an illegal path)"
                               % path})
        return (output_objects, returnvalues.CLIENT_ERROR)

    filedata = read_file(path, real_path, logger)
    output_objects.append({'object_type': 'file', 'data'
                          : filedata, 'name':real_path})
    return (output_objects, returnvalues.OK)

