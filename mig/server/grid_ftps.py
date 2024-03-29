#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# grid_ftps - secure ftp server wrapping ftp in tls/ssl and mapping user home
# Copyright (C) 2003-2015  The MiG Project lead by Brian Vinter
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

#
# This code is a heavily modified version of the tls server example from the
# pyftpdlib package
# https://code.google.com/p/pyftpdlib
#
# = Original copyright notice follows =

#  pyftpdlib is released under the MIT license, reproduced below:
#  ======================================================================
#  Copyright (C) 2007-2013 Giampaolo Rodola' <g.rodola@gmail.com>
#
#                         All Rights Reserved
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
#  ======================================================================

"""An RFC-4217 asynchronous FTPS server supporting both SSL and TLS.

Extended to fit MiG user auth and access restrictions.

Requires PyOpenSSL module (http://pypi.python.org/pypi/pyOpenSSL).
"""

import logging
import os
import sys
import time

try:
    from pyftpdlib.authorizers import DummyAuthorizer, AuthenticationFailed
    from pyftpdlib.handlers import FTPHandler, TLS_FTPHandler
    from pyftpdlib.servers import FTPServer
    from pyftpdlib.filesystems import AbstractedFS, FilesystemError
except ImportError:
    print "ERROR: the python pyftpdlib module is required for this daemon"
    raise

from shared.base import invisible_path
from shared.conf import get_configuration_object
from shared.griddaemons import get_fs_path, acceptable_chmod, refresh_users, \
     hit_rate_limit, update_rate_limit, expire_rate_limit
from shared.logger import daemon_logger
from shared.useradm import check_password_hash


configuration, logger = None, None


class MiGUserAuthorizer(DummyAuthorizer):
    """Authenticate/authorize against MiG users DB and user password files"""

    users = None
    authenticated_user = None

    min_expire_delay = 300
    last_expire = time.time()

    def update_logins(self, username):
        """Update login DB"""

        # We don't have a handle_request for server so expire here instead
        
        if self.last_expire + self.min_expire_delay < time.time():
            self.last_expire = time.time()
            expired = expire_rate_limit(configuration, "ftps")
            logger.debug("expired rate limit entries: %s" % expired)

        # TODO: only refresh for username?

        daemon_conf = configuration.daemon_conf

        logger.debug("update user list")

        # automatic reload of users if more than refresh_delay seconds old
        refresh_delay = 5
        if daemon_conf['time_stamp'] + refresh_delay < time.time():
            daemon_conf = refresh_users(configuration, 'ftps')

        logger.debug("update usermap")
        usermap = {}
        for user_obj in daemon_conf['users']:
            if not usermap.has_key(user_obj.username):
                usermap[user_obj.username] = []
            usermap[user_obj.username].append(user_obj)
        self.users = usermap
        logger.info("updated usermap: %s" % self.users)
        logger.debug("update user_table")
        # Fill users in dictionary for fast lookup. We create a list of
        # matching User objects since each user may have multiple logins (e.g.
        # public keys)
        for (username, user_obj_list) in self.users.items():
            if self.has_user(username):
                self.remove_user(username)
            # We prefer last entry with password but fall back to any entry
            # to assure at least a hit
            user_obj = (user_obj_list + [i for i in user_obj_list \
                                         if i.password is not None])[-1]
            home_path = os.path.join(daemon_conf['root_dir'], user_obj.home)
            logger.debug("add user to user_table: %s" % user_obj)
            # The add_user format and perm string meaning is explained at:
            # http://code.google.com/p/pyftpdlib/wiki/Tutorial#2.2_-_Users
            self.add_user(username, user_obj.password,
                          home_path, perm='elradfmwM')
        logger.debug("updated user_table: %s" % self.user_table)

    def validate_authentication(self, username, password, handler):
        """Password auth against usermap.

        Please note that we take serious steps to secure against password
        cracking, but that it _may_ still be possible to achieve with a big
        effort.

        Paranoid users / grid owners should not enable password access in the
        first place!
        """
        logger.debug("Authenticating %s" % username)
        self.update_logins(username)
        
        offered = None
        if hit_rate_limit(configuration, "ftps", handler.remote_ip, username):
            logger.warning("Rate limiting login from %s" % handler.remote_ip)
        elif 'password' in configuration.user_ftps_auth and \
               self.has_user(username):
            # list of User login objects for username
            entries = [self.user_table[username]]
            offered = password
            for entry in entries:
                if entry['pwd'] is not None:
                    allowed = entry['pwd']
                    logger.debug("Password check for %s" % username)
                    if check_password_hash(offered, allowed):
                        logger.info("Authenticated %s" % username)
                        self.authenticated_user = username
                        update_rate_limit(configuration, "ftps",
                                          handler.remote_ip, username, True)
                        return True
        err_msg = "Password authentication failed for %s" % username
        logger.error(err_msg)
        print err_msg
        self.authenticated_user = None
        update_rate_limit(configuration, "ftps", handler.remote_ip, username,
                          False)
        # Must raise AuthenticationFailed exception since version 1.0.0 instead
        # of returning bool
        raise AuthenticationFailed(err_msg)


class MiGRestrictedFilesystem(AbstractedFS):
    """Restrict access to user home and symlinks into the dirs configured in
    chroot_exceptions. Prevent access to a few hidden files.
    """
    
    # Use shared daemon fs helper functions
    
    def _acceptable_chmod(self, ftps_path, mode):
        """Wrap helper"""
        #logger.debug("acceptable_chmod: %s" % ftps_path)
        reply = acceptable_chmod(ftps_path, mode, self.chmod_exceptions)
        if not reply:
            logger.warning("acceptable_chmod failed: %s %s %s" % \
                                (ftps_path, mode, self.chmod_exceptions))
        #logger.debug("acceptable_chmod returns: %s :: %s" % \
        #                      (ftps_path, reply))
        return reply

    # Public interface functions

    def validpath(self, path):
        """Check that user is allowed inside path checking against configured
        chroot_exceptions and built-in hidden paths.
        """
        daemon_conf = configuration.daemon_conf
        try:
            get_fs_path(path, daemon_conf['root_dir'],
                        daemon_conf['chroot_exceptions'])
            logger.debug("accepted access to %s" % path)
            return True
        except ValueError:
            logger.error("rejected access to %s" % path)
            return False

    def chmod(self, path, mode):
        """Change file/directory mode with MiG restrictions"""
        real_path = self.ftp2fs(path)
        daemon_conf = configuration.daemon_conf
        self.chmod_exceptions = daemon_conf['chmod_exceptions']
        # Only allow change of mode on files and only outside chmod_exceptions
        if self._acceptable_chmod(path, mode):
            # Only allow permission changes that won't give excessive access
            # or remove own access.
            if os.path.isdir(path):
                new_mode = (mode & 0775) | 0750
            else:
                new_mode = (mode & 0775) | 0640
            logger.info("chmod %s (%s) without damage on %s :: %s" % \
                        (new_mode, mode, path, real_path))
            return AbstractedFS.chmod(self, path, new_mode)
        # Prevent users from messing up access modes
        logger.error("chmod %s rejected on path %s :: %s" % (mode, path,
                                                             real_path))
        raise FilesystemError("requested permission change no allowed")

    def listdir(self, path):
        """List the content of a directory with MiG restrictions"""
        return [i for i in AbstractedFS.listdir(self, path) if not \
                invisible_path(i)]

    ### Force symlinks to look like real dirs to avoid client confusion ###
    def lstat(self, path):
        """Modified to always return real stat to hide symlinks"""
        return self.stat(path)
        
    def readlink(self, path):
        """Modified to always return just path to hide symlinks"""
        return path

    def islink(self, path):
        """Modified to always return False to hide symlinks"""
        return False

    def lexists(self, path):
        """Modified to always check with stat to hide symlinks"""
        try:
            self.stat(path)
            return True
        except:
            return False


def start_service(conf):
    """Main server"""
    daemon_conf = configuration.daemon_conf
    authorizer = MiGUserAuthorizer()
    if daemon_conf['nossl'] or not configuration.user_ftps_key:
        logger.warning('Not wrapping connections in SSL - only for testing!')
        handler = FTPHandler
    else:
        logger.info("Using fully encrypted mode")
        handler = TLS_FTPHandler
        # requires SSL for both control and data channel
        handler.tls_control_required = True
        handler.tls_data_required = True
    handler.certfile = conf.user_ftps_key
    handler.authorizer = authorizer
    handler.abstracted_fs = MiGRestrictedFilesystem
    handler.passive_ports = range(conf.user_ftps_pasv_ports[0],
                                  conf.user_ftps_pasv_ports[1])
    
    server = FTPServer((conf.user_ftps_address, conf.user_ftps_ctrl_port),
                       handler)
    server.serve_forever()
        

if __name__ == '__main__':
    configuration = get_configuration_object()
    nossl = False

    # Use separate logger
    logger = daemon_logger("ftps", configuration.user_ftps_log, "debug")

    # Allow configuration overrides on command line
    if sys.argv[1:]:
        nossl = bool(sys.argv[1])
    if sys.argv[2:]:
        configuration.user_ftps_address = sys.argv[2]
    if sys.argv[3:]:
        configuration.user_ftps_ctrl_port = int(sys.argv[3])

    if not configuration.site_enable_ftps:
        err_msg = "FTPS access to user homes is disabled in configuration!"
        logger.error(err_msg)
        print err_msg
        sys.exit(1)
    print """
Running grid ftps server for user ftps access to their MiG homes.

Set the MIG_CONF environment to the server configuration path
unless it is available in mig/server/MiGserver.conf
"""
    print __doc__
    address = configuration.user_ftps_address
    ctrl_port = configuration.user_ftps_ctrl_port
    pasv_ports = configuration.user_ftps_pasv_ports
    # Allow access to vgrid linked dirs and mounted storage resource dirs
    chroot_exceptions = [os.path.abspath(configuration.vgrid_private_base),
                         os.path.abspath(configuration.vgrid_public_base),
                         os.path.abspath(configuration.vgrid_files_home),
                         os.path.abspath(configuration.resource_home)]
    # Any extra chmod exceptions here - we already cover invisible_path check
    # in acceptable_chmod helper.
    chmod_exceptions = []
    configuration.daemon_conf = {
        'address': address,
        'ctrl_port': ctrl_port,
        'pasv_ports': pasv_ports,
        'root_dir': os.path.abspath(configuration.user_home),
        'chmod_exceptions': chmod_exceptions,
        'chroot_exceptions': chroot_exceptions,
        'allow_password': 'password' in configuration.user_ftps_auth,
        'allow_digest': False,
        'allow_publickey': 'publickey' in configuration.user_ftps_auth,
        'user_alias': configuration.user_ftps_alias,
        'users': [],
        'time_stamp': 0,
        'logger': logger,
        'nossl': nossl,
        }
    logger.info("Starting FTPS server")
    info_msg = "Listening on address '%s' and port %d" % (address, ctrl_port)
    logger.info(info_msg)
    print info_msg
    try:
        start_service(configuration)
    except KeyboardInterrupt:
        info_msg = "Received user interrupt"
        logger.info(info_msg)
        print info_msg
        configuration.daemon_conf['stop_running'].set()
    info_msg = "Leaving with no more workers active"
    logger.info(info_msg)
    print info_msg
