#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# migsftp - sample paramiko-based sftp client for user home access
# Copyright (C) 2003-2014  The MiG Project lead by Brian Vinter
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

"""Sample Paramiko-based sftp client working with your MiG home.

Requires paramiko (http://pypi.python.org/pypi/paramiko) and thus PyCrypto
(http://pypi.python.org/pypi/pycrypto).

Run with:
python migsftp.py [GENERATED_USERNAME]

where the optional GENERATED_USERNAME is the username displayed on your
personal MiG ssh settings page. You will be interactively prompted for it if
it is not provided on the command line.

Please check the global configuration section below if it fails. The comments
should help you tweak the configuration to solve most common problems.

This example should be a good starting point for writing your own custom sftp
client acting on your MiG home.
"""

import os
import sys
import paramiko


### Global configuration ###

server_fqdn = 'dk-cert.migrid.org'
server_port = 2222
server_host_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAgQCwxYFM1tzy7RyNpPFCSVHG0fTiq1SWnmsFHCJp4UskAuodbWAzuKNml9HBI0Bk0ynOVhMfneh5sv2sFuXfFTHiNVUM+vpqtSNCHEF/2jYHzPnp5aT4jvrTUmJ1PYmzfNQonjrWxPpXt9ROfLAhZib2qs5QzkiqpcY3NNh8EOEZOQ=="
known_hosts_path = os.path.expanduser("~/.ssh/known_hosts")
user_key = None
host_key_policy = paramiko.RejectPolicy()
data_compression = True

# Uncomment the next line if you don't have a valid key in ssh-agent or ~/.ssh/
# but use a key from ~/.mig/id_rsa instead. Obviously, you can modify the path
# if your key is stored elsewhere.
#user_key = [os.path.expanduser('~/.mig/id_rsa')]

# Uncomment the next line if you have not connected to MiG before
# and want to silently accept the host key - please beware of the
# security implications!
#host_key_policy = paramiko.AutoAddPolicy()
# ... or the next line if you want a warning in that case but want to continue
#host_key_policy = paramiko.WarningPolicy()

# Uncomment the next line if don't want compressed transfers. This is a trade
# off between CPU usage and throughput
#data_compression = False


### Initialize client session ###

if __name__ == "__main__":

    # Get auto-generated username from command line or interactively

    if sys.argv[1:]:
        user_name = sys.argv[1]
    else:
        print """Please enter/paste the long username from your MiG ssh
settings page"""
        user_name = raw_input('Username: ')

    if len(user_name) < 64:
        print """Warning: the supplied username is shorter than expected!
Please verify it on your MiG ssh Settings page in case of failure."""

    # Connect with provided settings

    ssh = paramiko.SSHClient()
    known_host_keys = ssh.get_host_keys()
    key_type, key_data = server_host_key.split(' ')[:2]
    pub_key = paramiko.PKey(msg=server_fqdn, data=key_data)
    known_host_keys.add(server_fqdn, key_type, pub_key)
    known_host_keys.load(known_hosts_path)
    ssh.set_missing_host_key_policy(host_key_policy)
    ssh.connect(server_fqdn, username=user_name, port=server_port,
                key_filename=user_key, compress=data_compression)
    ftp = ssh.open_sftp()


    ### Sample actions on your MiG home directory ###

    # List and stat files in the remote .ssh dir which should always be there

    base = '.ssh'
    files = ftp.listdir(base)
    path_stat = ftp.stat(base)
    print "stat %s:\n%s" % (base, path_stat)
    print "files in %s dir:\n%s" % (base, files)
    for name in files:
        rel_path = os.path.join(base, name)
        path_stat = ftp.stat(rel_path)
        print "stat %s:\n%s" % (rel_path, path_stat)
    dummy = 'this-is-a-migsftp-dummy-file.txt'
    dummy_text = "sample file\ncontents from client\n"
    dummy_fd = open(dummy, "w")
    dummy_fd.write(dummy_text)
    dummy_fd.close()
    print "create dummy in %s" % dummy
    path_stat = os.stat(dummy)
    print "local stat %s:\n%s" % (dummy, path_stat)
    print "upload migsftpdummy in %s home" % dummy
    ftp.put(dummy, dummy)
    path_stat = ftp.stat(dummy)
    print "remote stat %s:\n%s" % (dummy, path_stat)
    print "delete dummy in %s" % dummy
    os.remove(dummy)
    print "verify gone: %s" % (dummy not in os.listdir('.'))
    print "download migsftpdummy from %s home" % dummy
    ftp.get(dummy, dummy)
    path_stat = os.stat(dummy)
    print "local stat %s:\n%s" % (dummy, path_stat)
    dummy_fd = open(dummy, "r")
    verify_text = dummy_fd.read()
    dummy_fd.close()
    print "verify correct contents: %s" % (dummy_text == verify_text)
    print "delete dummy in %s" % dummy
    os.remove(dummy)

    ### Clean up before exit ###

    ftp.close()
    ssh.close()
