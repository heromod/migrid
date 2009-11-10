#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# autocreate - create user from signed (grid.dk) confusa certificate
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

"""Automatic sign up back end for external certificates

   Also see extcertaction.py. Differences: 
     - no e-mail, only auto_create functionality or nothing
     - automatic upload of a proxy certificate when provided
     - no special check for DIKU organisation
     - allows empty country, email, and state
"""

import os
import time
import tempfile
import pickle

import shared.returnvalues as returnvalues
from shared.init import initialize_main_variables
from shared.functional import validate_input, REJECT_UNSET
from shared.useradm import db_name, distinguished_name_to_user, \
     create_user, fill_user, client_id_dir
import shared.arcwrapper as arc
from shared.fileio import write_file

def signature():
    """Signature of the main function"""

    defaults = {
        'cert_id': REJECT_UNSET,
        'cert_name': REJECT_UNSET,
        'org': REJECT_UNSET,
        'email': [''],
        'country': [''],
        'state': [''],
        'comment': ['(Created through autocreate)'],
        'proxy_upload': ['']
        }
    return ['text', defaults]


def handle_proxy(proxy_string, client_id, config):
    """If ARC-enabled server: store a proxy certificate.
       Arguments: proxy_string - text  extracted from given upload 
                  client_id  - DN for user just being created 
                  config     - global configuration
    """

    output = []
    client_dir = client_id_dir(client_id)
    dir = os.path.join(config.user_home,client_dir)
    path = os.path.join(config.user_home,client_dir, arc.Ui.proxy_name)

    # store the file
    try:
        write_file(proxy_string, path, config.logger)
        os.chmod(path, 0600)
    except Exception, exc:
        output.append({'object_type': 'error_text', 'text'
                              : 'Proxy file could not be written (%s)!'
                               % str(exc).replace(dir, '')})
        return output

    # provide information about the uploaded proxy
    try:
        session_Ui = arc.Ui(dir)
        proxy = session_Ui.getProxy()
        if proxy.IsExpired():
            # can rarely happen, constructor will throw exception
            output.append({'object_type': 'warning', 
                               'text': 'Proxy certificate is expired.'})
        else:
            output.append({'object_type': 'text', 
                                   'text': 'Proxy for %s' \
                                           % proxy.GetIdentitySN()})
            output.append({'object_type': 'text', 
                 'text': 'Proxy certificate will expire on %s (in %s sec.)' \
                         % (proxy.Expires(), proxy.getTimeleft())
                })
    except arc.NoProxyError, err:
        
        output.append({'object_type':'warning', 'text': 
                       'No proxy certificate to load: %s' % err.what()})
    return output


def main(client_id, user_arguments_dict):
    """Main function used by front end"""


    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(op_header=False)
    logger = configuration.logger
    logger.debug("starting autocreate")
    logger.debug('Arguments: %s' % user_arguments_dict)
    
    output_objects.append({'object_type': 'header', 'text'
                          : 'Automatic MiG sign up'})

    defaults = signature()[1]
    (validate_status, accepted) = validate_input(user_arguments_dict,
            defaults, output_objects, allow_rejects=False)
    if not validate_status:
        return (accepted, returnvalues.CLIENT_ERROR)

    logger.debug('Accepted arguments: %s' % accepted)

    admin_email = configuration.admin_email
    smtp_server = configuration.smtp_server
    user_pending = os.path.abspath(configuration.user_pending)

    # force name to capitalized form (henrik karlsen -> Henrik Karlsen)

    cert_id = accepted['cert_id'][-1].strip()
    cert_name = accepted['cert_name'][-1].strip().title()
    country = accepted['country'][-1].strip().upper()
    state = accepted['state'][-1].strip().title()
    org = accepted['org'][-1].strip()

    # we should have the proxy file read...
    proxy_content = accepted['proxy_upload'][-1]

    # lower case email address

    email = accepted['email'][-1].strip().lower()

    # keep comment to a single line

    comment = accepted['comment'][-1].replace('\n', '   ')

    # single quotes break command line format - remove

    comment = comment.replace("'", ' ')

    logger.debug('Extracted: %s' % \
                 [ n + "=" + eval(n) \
                   for n in ['cert_id','cert_name','country','state', \
                             'org','proxy_content','email','comment'] \
                 ])

    try:
        distinguished_name_to_user(cert_id)
    except:
        output_objects.append({'object_type': 'error_text', 'text'
                              : '''Illegal Distinguished name:
Please note that the distinguished name must be a valid certificate DN with multiple "key=val" fields separated by "/".
'''})
        return (output_objects, returnvalues.CLIENT_ERROR)

    user_dict = {
        'distinguished_name': cert_id,
        'full_name': cert_name,
        'organization': org,
        'state': state,
        'country': country,
        'email': email,
        'password': '',
        'comment': '%s: %s' % ('Existing certificate', comment),
        'expire': int(time.time() + (((2 * 365.25) * 24) * 60) * 60),
        # JB: Why this arbitrary value (2 years)?? 
        #     Can we inspect the SSL certificate?
        }

    # If server allows automatic addition of users with a CA validated cert
    # we create the user immediately and skip mail
    
    if configuration.auto_add_cert_user:
        fill_user(user_dict)

        # Now all user fields are set and we can begin adding the user

        db_path = os.path.join(configuration.mig_server_home, db_name)
        try:
            create_user(user_dict, configuration.config_file, 
                        db_path, ask_renew=False)

            if accepted['proxy_upload'] != ['']:
                # save the file, display expiration date
                proxy_out = handle_proxy(proxy_content, cert_id, 
                                         configuration)
                output_objects.extend(proxy_out)
                
        except Exception, err:
            logger.error('Failed to create user with existing certificate %s: %s'
                     % (cert_id, err))
            output_objects.append({'object_type': 'error_text', 'text'
                                   : '''Could not create the user account for you:
Please report this problem to the grid administrators (%s).''' % admin_email})
            return (output_objects, returnvalues.SYSTEM_ERROR)

        output_objects.append({'object_type': 'text', 'text'
                                   : '''Created the user account for you:
Please use the navigation menu to the left to proceed using it.
'''})
        return (output_objects, returnvalues.OK)

    else:
        output_objects.append({'object_type': 'error_text', 
                               'text': 'Automatic user creation disabled.\n' +
                               'Please send a mail to the Grid ' +
                               'administrators (%s) if you ' % admin_email +
                               'think this is an error.' })
        return (output_objects, returnvalues.ERROR)

###########################################################################
###########################################################################
####### Following: old code, send mail to administrator addresses #########
###########################################################################
    
    # Without auto add we end here and go through the mail-to-admins procedure
    req_path = None
    try:
        (os_fd, req_path) = tempfile.mkstemp(dir=user_pending)
        os.write(os_fd, pickle.dumps(user_dict))
        os.close(os_fd)
    except Exception, err:
        logger.error('Failed to write existing certificate request to %s: %s'
                     % (req_path, err))
        output_objects.append({'object_type': 'error_text', 'text'
                               : 'Request could not be sent to grid administrators. Please contact them manually on %s if this error persists.'
                               % admin_email})
        return (output_objects, returnvalues.SYSTEM_ERROR)

    logger.info('Wrote existing certificate sign up request to %s' % req_path)
    tmp_id = req_path.replace(user_pending, '')
    user_dict['tmp_id'] = tmp_id

    dest = 'karlsen@erda.imada.sdu.dk'
    mig_user = os.environ.get('USER', 'mig')
    command_user_create = \
        """
As '%s' on %s:
cd ~/mig/server
./createuser.py -i '%s' -u '%s'"""\
         % (mig_user, configuration.server_fqdn, cert_id, req_path)
    command_user_delete = \
        """
As '%s' user on %s:
cd ~/mig/server
./deleteuser.py -i '%s'"""\
         % (mig_user, configuration.server_fqdn, cert_id)

    user_dict['command_user_create'] = command_user_create
    user_dict['command_user_delete'] = command_user_delete
    user_dict['migserver_https_url'] = configuration.migserver_https_url
    email_header = 'MiG sign up request for %s' % cert_id
    email_msg = \
        """
Received an existing certificate sign up request with certificate data
 * Distinguished Name: %(distinguished_name)s
 * Full Name: %(full_name)s
 * Organization: %(organization)s
 * State: %(state)s
 * Country: %(country)s
 * Email: %(email)s
 * Comment: %(comment)s
 * Expire: %(expire)s

Command to create user on MiG server:
%(command_user_create)s

Finally add the user to any relevant VGrids from:
%(migserver_https_url)s/cgi-bin/vgridadmin.py

---
Command to delete user again on MiG server:
%(command_user_delete)s
---

"""\
         % user_dict

    logger.info('Sending email: to: %s, header: %s, msg: %s, smtp_server: %s'
                 % (admin_email, email_header, email_msg, smtp_server))
    if not send_email(admin_email, email_header, email_msg, logger,
                      configuration):
        output_objects.append({'object_type': 'error_text', 'text'
                              : 'An error occured trying to send the email requesting the grid administrators to sign up with an existing certificate. Please email the grid administrators (%s) manually and include the session ID: %s'
                               % (admin_email, tmp_id)})
        return (output_objects, returnvalues.SYSTEM_ERROR)

    output_objects.append({'object_type': 'text', 'text'
                          : "Request sent to grid administrators: Your request for a MiG user account with your existing certificate will be verified and handled as soon as possible, so please be patient. In case of inquiries about this request, please email the grid administrators (%s) and include the session ID: %s"
                           % (admin_email, tmp_id)})
    return (output_objects, returnvalues.OK)
