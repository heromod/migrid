#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# codegrep - a simple helper to locate strings in the project code.
# Copyright (C) 2007  Jonas Bardino
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

"""Grep for a regular expression in all code"""

import os
import sys

# Ignore backup and dot files in wild card match
plain = '[a-zA-Z0-9]*.py'
code_files = [
    '%s' % plain,
    'cgi-bin/%s' % plain,
    'cgi-sid/%s' % plain,
    'wsgi-bin/%s' % plain,
    'install/%s' % plain,
    'migfs-fuse/%s' % plain,
    'server/%s' % plain,
    'shared/%s' % plain,
    'shared/functionality/%s' % plain,
    'shared/distos/%s' % plain,
    'simulation/%s' % plain,
    'resource/frontend_script.sh',
    'resource/master_node_script.sh',
    'resource/leader_node_script.sh',
    'resource/dummy_node_script.sh',
    'user/%s' % plain,
    'vm-proxy/%s' % plain,
    'webserver/%s' % plain,
    ]
code_files += ['cgi-sid/%s' % name for name in ['requestnewjob',
               'putrespgid']]

code_files += ['cgi-bin/%s' % name for name in [
    'listdir',
    'mkdir',
    'put',
    'remove',
    'rename',
    'rmdir',
    'stat',
    'walk',
    'getrespgid',
    ]]

if '__main__' == __name__:
    if len(sys.argv) < 2:
        print 'Usage: %s PATTERN' % sys.argv[0]
        print 'Grep for PATTERN in all code files'
        sys.exit(1)
    
    pattern = sys.argv[1]
    os.system("grep -E '%s' %s" % (pattern, ' '.join(code_files)))