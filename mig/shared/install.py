#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# install - MiG server install helpers
# Copyright (C) 2003-2012  The MiG Project lead by Brian Vinter
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

"""Install helpers:

Generate the configurations for a custom MiG server installation.
Creates MiG server and Apache configurations to fit the provided settings.

Create MiG developer account with dedicated web server and daemons.
"""

import sys
import os
import re
import random
import crypt
import socket
import datetime

from shared.defaults import default_http_port, default_https_port

def fill_template(template_file, output_file, settings):
    """Fill a configuration template using provided settings dictionary"""
    try:
        template = open(template_file, 'r')
        contents = template.read()
        template.close()
    except Exception, err:
        print 'Error: reading template file %s: %s' % (template_file,
                err)
        return False

    # print "template read:\n", output

    for (variable, value) in settings.items():
        contents = re.sub(variable, value, contents)

    # print "output:\n", contents

    # print "writing specific contents to %s" % (output_file)

    try:
        output = open(output_file, 'w')
        output.write(contents)
        output.close()
    except Exception, err:
        print 'Error: writing output file %s: %s' % (output_file, err)
        return False
    return True

def generate_confs(
    source=os.path.dirname(sys.argv[0]),
    destination=os.path.dirname(sys.argv[0]),
    public_fqdn='localhost',
    cert_fqdn='localhost',
    sid_fqdn='localhost',
    user='mig',
    group='mig',
    apache_etc='/etc/apache2',
    apache_run='/var/run',
    apache_lock='/var/lock',
    apache_log='/var/log/apache2',
    mig_code='/home/mig/mig',
    mig_state='/home/mig/state',
    mig_certs='/home/mig/certs',
    enable_sftp='True',
    moin_etc='',
    moin_share='',
    hg_path='',
    hgweb_scripts='',
    trac_admin_path='',
    trac_ini_path='',
    public_port=default_http_port,
    cert_port=default_https_port,
    sid_port=default_https_port+1,
    user_clause='User',
    group_clause='Group',
    listen_clause='#Listen',
    serveralias_clause='#ServerAlias',
    ):
    """Generate Apache and MiG server confs with specified variables"""

    user_dict = {}
    user_dict['__PUBLIC_FQDN__'] = public_fqdn
    user_dict['__CERT_FQDN__'] = cert_fqdn
    user_dict['__SID_FQDN__'] = sid_fqdn
    user_dict['__USER__'] = user
    user_dict['__GROUP__'] = group
    user_dict['__PUBLIC_PORT__'] = str(public_port)
    user_dict['__CERT_PORT__'] = str(cert_port)
    user_dict['__SID_PORT__'] = str(sid_port)
    user_dict['__MIG_HOME__'] = mig_code
    user_dict['__MIG_STATE__'] = mig_state
    user_dict['__MIG_CERTS__'] = mig_certs
    user_dict['__APACHE_ETC__'] = apache_etc
    user_dict['__APACHE_RUN__'] = apache_run
    user_dict['__APACHE_LOCK__'] = apache_lock
    user_dict['__APACHE_LOG__'] = apache_log
    user_dict['__ENABLE_SFTP__'] = enable_sftp
    user_dict['__MOIN_ETC__'] = moin_etc
    user_dict['__MOIN_SHARE__'] = moin_share
    user_dict['__HG_PATH__'] = hg_path
    user_dict['__HGWEB_SCRIPTS__'] = hgweb_scripts
    user_dict['__TRAC_ADMIN_PATH__'] = trac_admin_path
    user_dict['__TRAC_INI_PATH__'] = trac_ini_path
    user_dict['__USER_CLAUSE__'] = user_clause
    user_dict['__GROUP_CLAUSE__'] = group_clause
    user_dict['__LISTEN_CLAUSE__'] = listen_clause
    user_dict['__SERVERALIAS_CLAUSE__'] = serveralias_clause

    # Apache fails on duplicate Listen directives so comment in that case
    same_port, same_fqdn = (cert_port == sid_port), (cert_fqdn == sid_fqdn)
    user_dict['__IF_SEPARATE_PORTS__'] = '#'
    if not same_port:
        user_dict['__IF_SEPARATE_PORTS__'] = ''

    if same_fqdn and same_port:
        print """
WARNING: you probably have to use either different fqdn or port settings for
cert and sid based https!
"""

    # Enable mercurial module in trackers if Trac is available
    user_dict['__HG_COMMENTED__'] = '#'
    if user_dict['__HG_PATH__']:
        user_dict['__HG_COMMENTED__'] = ''

    try:
        os.makedirs(destination)
    except OSError:
        pass

    # Implicit ports if they are standard: cleaner and removes double hg login
    user_dict['__PUBLIC_URL__'] = 'http://%(__PUBLIC_FQDN__)s' % user_dict
    if str(public_port) != str(default_http_port):
        print "adding explicit public port (%s)" % [public_port,
                                                    default_http_port]
        user_dict['__PUBLIC_URL__'] += ':%(__PUBLIC_PORT__)s' % user_dict
    user_dict['__CERT_URL__'] = 'https://%(__CERT_FQDN__)s' % user_dict
    if str(cert_port) != str(default_https_port):
        print "adding explicit cert port (%s)" % [cert_port, default_https_port]
        user_dict['__CERT_URL__'] += ':%(__CERT_PORT__)s' % user_dict
    user_dict['__SID_URL__'] = 'https://%(__SID_FQDN__)s' % user_dict
    if str(cert_port) != str(default_https_port):
        print "adding explicit sid port (%s)" % [sid_port, default_https_port]
        user_dict['__SID_URL__'] += ':%(__SID_PORT__)s' % user_dict
        
    # modify this list when adding/removing template->target  
    replacement_list = \
                     [("apache-envs-template.conf", "envvars"),
                      ("apache-apache2-template.conf", "apache2.conf"),
                      ("apache-httpd-template.conf", "httpd.conf"),
                      ("apache-ports-template.conf", "ports.conf"),
                      ("apache-MiG-template.conf", "MiG.conf"),
                      ("apache-init.d-template", "apache-%s" % user),
                      ("apache-MiG-template.conf", "MiG.conf"),
                      ("trac-MiG-template.ini", "trac.ini"),
                      ("MiGserver-template.conf", "MiGserver.conf"),
                      # service script for MiG daemons
                      ("MiG-init.d-template", "MiG"),
                      ]
    for (in_name, out_name) in replacement_list:
        in_path = os.path.join(source, in_name)
        out_path = os.path.join(destination, out_name)
        if os.path.exists(in_path):
            fill_template(in_path, out_path, user_dict)
            # Sync permissions
            os.chmod(out_path, os.stat(in_path).st_mode)
        else:
            print "Skipping missing template: %s" % in_path
    return True

def create_user(
    user,
    group,
    ssh_login_group='remotelogin',
    debug=False,
    public_fqdn=socket.getfqdn(),
    cert_fqdn=socket.getfqdn(),
    sid_fqdn=socket.getfqdn(),
    ):
    """Create MiG unix user with supplied user and group name and show
    commands to make it a MiG developer account.
    If sid_fqdn is set to a fqdn different from the default fqdn of this host
    the apache web server configuration will use the same port for cert and
    sid https access but on diffrent IP adresses. Otherwise it will use two
    different ports on the same address.
    """

    # make sure not to wreak havoc if no user supplied

    if not user:
        print "no user supplied! can't continue"
        return False

    print 'groupadd %s' % group
    status = os.system('groupadd %s' % group) >> 8
    if status != 0:
        print 'Warning: exit code %d' % status

    # Don't use 'o'/'0' and 'l'/'1' since they may confuse users

    valid_chars = 'abcdefghijkmnpqrstuvwxyz'\
         + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ23456789'
    pwlen = 8
    pw = ''
    for _ in range(pwlen):
        pw += random.choice(valid_chars)

    # TODO: python does not support md5 passwords - using DES ones
    # from crypt for now

    shell = '/bin/bash'
    enc_pw = crypt.crypt(pw, random.choice(valid_chars)
                          + random.choice(valid_chars))
    print 'useradd -m -s %s -p %s -g %s %s' % (shell, enc_pw, group,
            user)
    status = os.system('useradd -m -s %s -p %s -g %s %s' % (shell,
                       enc_pw, group, user)) >> 8
    if status != 0:
        print 'Warning: exit code %d' % status
    else:
        print '# Created %s in group %s with pw %s' % (user, group, pw)

    home = '/home/%s' % user

    print 'chmod -R g-rwx,o-rwx %s' % home
    status = os.system('chmod -R g-rwx,o-rwx %s' % home) >> 8
    if status != 0:
        print 'Warning: exit code %d' % status
    else:
        print 'Removed global access to %s' % home

    print 'addgroup %s %s' % (user, ssh_login_group)
    status = os.system('addgroup %s %s' % (user, ssh_login_group)) >> 8
    if status != 0:
        print 'Warning: exit code %d' % status
    else:
        print '# Added %s to group %s' % (user, ssh_login_group)

    out = os.popen('id -u %s' % user).readlines()
    uid_str = out[0].strip()
    out = os.popen('id -g %s' % user).readlines()
    gid_str = out[0].strip()
    try:
        uid = int(uid_str)
        gid = int(gid_str)
    except Exception, err:
        print 'Error: %s' % err
        if not debug:
            return False

    # print "uid: %d, gid: %d" % (uid, gid)

    reserved_ports = range(3 * uid, 3 * uid + 3)
    public_port, cert_port, sid_port = reserved_ports[:3]

    mig_dir = os.path.join(home, 'mig')
    server_dir = os.path.join(mig_dir, 'server')
    state_dir = os.path.join(home, 'state')
    apache_etc = '/etc/apache2'
    apache_dir = '%s-%s' % (apache_etc, user)
    apache_run = '%s/run' % apache_dir
    apache_lock = '%s/lock' % apache_dir
    apache_log = '%s/log' % apache_dir
    cert_dir = '%s/MiG-certificates' % apache_dir
    # We don't have a free port for sftp
    enable_sftp = 'False'
    moin_etc = '/etc/moin'
    moin_share = '/usr/share/moin'
    hg_path = '/usr/bin/hg'
    hgweb_scripts = '/usr/share/doc/mercurial-common/examples/'
    trac_admin_path = '/usr/bin/trac-admin'
    trac_ini_path = '%s/trac.ini' % server_dir

    firewall_script = '/root/scripts/firewall'
    print '# Add the next line to %s and run the script:'\
         % firewall_script
    print 'iptables -A INPUT -p tcp --dport %d:%d -j ACCEPT # webserver: %s'\
         % (public_port, sid_port, user)

    sshd_conf = '/etc/ssh/sshd_config'
    print """# Unless 'AllowGroups %s' is already included, append %s
# to the AllowUsers line in %s and restart sshd."""\
         % (ssh_login_group, user, sshd_conf)
    print """# Add %s to the sudoers file (visudo) with privileges
# to run apache init script in %s
visudo""" % (user, apache_dir)
    print """# Set disk quotas for %s using reference user quota:
edquota -u %s -p LOGIN_OF_SIMILAR_USER"""\
         % (user, user)
    expire = datetime.date.today()
    expire = expire.replace(year=expire.year + 1)
    print """# Optionally set account expire date for user:
chage -E %s %s"""\
         % (expire, user)
    print """# Attach full name of user to login:
usermod -c 'INSERT FULL NAME HERE' %s"""\
         % user
    print """# Add mount point for sandbox generator:
echo '/home/%s/state/sss_home/MiG-SSS/hda.img      /home/%s/state/sss_home/mnt  auto    user,loop       0       0' >> /etc/fstab"""\
         % (user, user)

    src = os.path.abspath(os.path.dirname(sys.argv[0]))
    dst = os.path.join(src, '%s-confs' % user)

    server_alias = '#ServerAlias'
    if socket.gethostbyname(sid_fqdn) != socket.gethostbyname(cert_fqdn):
        sid_port = cert_port
        server_alias = 'ServerAlias'
    generate_confs(
        src,
        dst,
        public_fqdn,
        cert_fqdn,
        sid_fqdn,
        user,
        group,
        apache_dir,
        apache_run,
        apache_lock,
        apache_log,
        mig_dir,
        state_dir,
        cert_dir,
        enable_sftp,
        moin_etc,
        moin_share,
        hg_path,
        hgweb_scripts,
        trac_admin_path,
        trac_ini_path,
        public_port,
        cert_port,
        sid_port,
        'User',
        'Group',
        '#Listen',
        server_alias,
        )
    apache_envs_conf = os.path.join(dst, 'envvars')
    apache_apache2_conf = os.path.join(dst, 'apache2.conf')
    apache_httpd_conf = os.path.join(dst, 'httpd.conf')
    apache_ports_conf = os.path.join(dst, 'ports.conf')
    apache_mig_conf = os.path.join(dst, 'MiG.conf')
    server_conf = os.path.join(dst, 'MiGserver.conf')
    trac_ini = os.path.join(dst, 'trac.ini')
    apache_initd_script = os.path.join(dst, 'apache-%s' % user)

    settings = {'user': user, 'group': group, 'server_conf': server_conf,
                'trac_ini': trac_ini, 'home': home, 'server_dir': server_dir,
                'public_fqdn': public_fqdn}
    settings['sudo_cmd'] = 'sudo su - %(user)s -c' % settings

    print '# Clone %s to %s and put config files there:' % (apache_etc,
            apache_dir)
    print 'sudo cp -r -u -d -x %s %s' % (apache_etc, apache_dir)
    print 'sudo rm -f %s/envvars' % apache_dir
    print 'sudo rm -f %s/apache2.conf' % apache_dir
    print 'sudo rm -f %s/httpd.conf' % apache_dir
    print 'sudo rm -f %s/ports.conf' % apache_dir
    print 'sudo rm -f %s/sites-enabled/*' % apache_dir
    print 'sudo rm -f %s/conf.d/*' % apache_dir
    print 'sudo cp -f -d %s %s/' % (apache_envs_conf, apache_dir)
    print 'sudo cp -f -d %s %s/' % (apache_apache2_conf, apache_dir)
    print 'sudo cp -f -d %s %s/' % (apache_httpd_conf, apache_dir)
    print 'sudo cp -f -d %s %s/' % (apache_ports_conf, apache_dir)
    print 'sudo cp -f -d %s %s/conf.d/' % (apache_mig_conf, apache_dir)
    print 'sudo cp -f -d %s %s/' % (apache_initd_script, apache_dir)
    print 'sudo mkdir -p %s %s %s ' % (apache_run, apache_lock, apache_log)

    # allow read access to logs

    print 'sudo chgrp -R %s %s' % (user, apache_log)
    print 'sudo chmod 2755 %s' % apache_log

    print """# Setup MiG for %(user)s:
%(sudo_cmd)s 'ssh-keygen -t rsa -N \"\" -q -f \\
    %(home)s/.ssh/id_rsa'
%(sudo_cmd)s 'cp -f -x \\
    %(home)s/.ssh/{id_rsa.pub,authorized_keys}'
%(sudo_cmd)s 'ssh -o StrictHostKeyChecking=no \\
    %(user)s@%(public_fqdn)s pwd >/dev/null'
%(sudo_cmd)s 'svn checkout http://migrid.googlecode.com/svn/trunk/ %(home)s'
sudo chown %(user)s:%(group)s %(server_conf)s %(trac_ini)s
sudo cp -f -p %(server_conf)s %(trac_ini)s %(server_dir)s/
""" % settings
        
    # Only add non-directory paths manually and leave the rest to
    # checkconf.py below

    print """%(sudo_cmd)s 'mkfifo %(server_dir)s/server.stdin'
%(sudo_cmd)s 'mkfifo %(server_dir)s/notify.stdin'
%(sudo_cmd)s '%(server_dir)s/checkconf.py'
""" % settings

    used_ports = [public_port, cert_port, sid_port]
    extra_ports = [port for port in reserved_ports if not port in used_ports]
    print """
#############################################################
Created %s in group %s with pw %s
Reserved ports:
HTTP:\t\t%d
HTTPS users:\t\t%d
HTTPS resources:\t\t%d
Extra ports:\t\t%s

The dedicated apache server can be started with the command:
sudo %s/%s start

#############################################################
"""\
         % (
        user,
        group,
        pw,
        public_port,
        cert_port,
        sid_port,
        ', '.join(["%d" % port for port in extra_ports]),
        apache_dir,
        os.path.basename(apache_initd_script),
        )
    return True