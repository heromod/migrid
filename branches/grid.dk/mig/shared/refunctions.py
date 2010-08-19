#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# refunctions - runtime environment functions
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

"""Runtime Environment functions"""

import os
import datetime
import fcntl
import urllib
import xml.dom.minidom as xml


import shared.rekeywords as rekeywords
import shared.parser as parser
from shared.fileio import pickle, unpickle
from shared.serial import load, dump
from ConfigParser import SafeConfigParser

WRITE_LOCK = 'write.lock'

def list_runtime_environments(configuration):
    """ List all runtime environments consisting of
    traditional runtime environments from configuration.re_home +
    zero install runtime environments from repo.conf
    """
       
    re_list = []
    dir_content = []

    try:
        dir_content = os.listdir(configuration.re_home)
    except Exception:
        if not os.path.isdir(configuration.re_home):
            try:
                os.mkdir(configuration.re_home)
            except Exception, err:
                configuration.logger.info(
                    'refunctions.py: not able to create directory %s: %s'
                    % (configuration.re_home, err))

    for entry in dir_content:

        # Skip dot files/dirs and the write lock

        if (entry.startswith('.')) or (entry == WRITE_LOCK):
            continue
        if os.path.isfile(os.path.join(configuration.re_home, entry)):

            # entry is a file and hence a runtime environment

            re_list.append(entry)
        else:
            configuration.logger.warning(
                '%s in %s is not a plain file, move it?'
                % (entry, configuration.re_home))

    re_list.extend(list_0install_res(configuration))

    return (True, re_list)


def is_runtime_environment(re_name, configuration):
    """Check that re_name is an existing runtime environment"""
    if os.path.isfile(os.path.join(configuration.re_home, re_name)):
        return True
    if re_name in list_0install_res(configuration).keys():
        return True
    else:
        return False

def list_0install_res(configuration):
    """Reads repo.conf of the software repository (location configurable),
       returns dictionary of ( RE-name, URL of 0install feed xml )
    
       Convention: RE names are upper case"""

    # if the feature is not configured, return empty
    if not configuration.zero_install_re \
           or not configuration.repo_conf_path:
        return {}

    try:
        repo_conf = SafeConfigParser()
        conf_fd = open(configuration.repo_conf_path, 'r')
        fcntl.flock(conf_fd, fcntl.LOCK_SH)
        repo_conf.readfp(conf_fd)
        fcntl.flock(conf_fd, fcntl.LOCK_UN)
        conf_fd.close()
    except Exception, err:
        configuration.logger.error("Could not read repo conf." % err)
        return {}
    all_packages = {}
    for package in repo_conf.sections():
        entry = {}
        for (key, val) in repo_conf.items(package):
            entry[key] = val
        
        all_packages[package.upper()] = entry["source"]
        
    return all_packages

def is_0install_re(name, configuration):
    """Simple check, inefficient if called many times"""
    list = list_0install_res(configuration)
    return (name in list)

# 0install RE information is XML and has to be parsed 
def getText(nodelist):
    """concatenate all CData found in nodelist, convert to ASCII"""
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc.__str__()

def get_0install_re_dict(name, configuration, url=None):
    """ http get URL and parse the 0install feed xml, extracting required
        information. If URL is None, retrieve it from a list.

        Returns: (RE dictionary in usual MiG format, error message)
                 where either dictionary or message are empty."""

    if not url:

        # read the URL from the repo.conf (make sure method fails
        # later if name is invalid)
        res = list_0install_res(configuration)
        url = res.get(name, "(undefined)")

    # read in the XML using http
    try:
        h    = urllib.urlopen(url)
        feed = h.read()
        h.close()
    except Exception, err:
        configuration.logger.error('Error opening required URL' + \
                                    ' %s for %s: %s.' % (url, name, err))
        return ({}, 'Could not open required URL ' + \
                    '%s for runtime environment %s' % (url,name))
    
    re_dict = {}
    # timestamp and creator are needed (apart from rekeywords)
    re_dict['CREATED_TIMESTAMP'] = datetime.datetime(2010,05,20)
    re_dict['CREATOR'] = 'provided by zero-install'

    # parse the xml feed, fill the keywords (see rekeywords.py)
    try:
        feeddoc = xml.parseString(feed)

        def textFrom(name):
            """ extract text from first node with given 
            tag name, otherwise empty"""
            ns = feeddoc.getElementsByTagName(name)
            if not ns: 
                return ''
            else:
                return getText(ns[0].childNodes[0:])

        # empty fields:
        empty  = [ 'TESTPROCEDURE', 'VERIFYSTDOUT',
                   'VERIFYSTDERR', 'VERIFYSTATUS']
        re_dict.update([ (e,'') for e in empty])

        # Directly mapped fields between XML and RE keywords:
        re_dict['RENAME'] = textFrom('name').upper()
        re_dict['DESCRIPTION'] = textFrom('description')

        # one SOFTWARE field, containing a dictionary with 
        # 'name', 'version', 'url', 'description', 'icon'
        software = {}
        software['version'] = 'can be provided by zero-install'
        software['name']        = textFrom('name')
        software['url']         = textFrom('homepage')
        software['description'] = textFrom('summary')

        icon = feeddoc.getElementsByTagName('icon')
        if icon:
            software['icon'] = icon[-1].getAttribute('href').__str__()
        else:
            software['icon'] = ''
        re_dict['SOFTWARE'] = [software]

        # build ENVIRONMENTVARIABLE definitions, each containing a dictionary
        # of 'name', 'example', 'description'

        # (field 'name') is upper case of the basename of the field
        # 'example', which should be the real binary name, later used
        # for defining environment variables!

        binaries = feeddoc.getElementsByTagName('binary')
        if binaries:
            env_vars = []
            for b in binaries:
                bin = b.getAttribute('name').__str__()
                var = bin.rsplit('/')[-1].upper()
                env_vars.append({'name': var, 'example':bin,
                          'description':'An executable binary in the package'
                                 })
        else:
            # not defined. Use package name as the only definition (and leave example empty)
            env_vars = [{'name': software['name'].upper(), 
                         'example': '',
                         'description': 'the default binary in the package'}]

        re_dict['ENVIRONMENTVARIABLE'] = env_vars

    except Exception, err:
        configuration.logger.error('Error parsing xml for %s: %s.\n XML dump: %s' % \
                                   (name, err, feed))
        return ({}, 'Could not parse runtime environment %s' % (name))

    return (re_dict,'')

def get_re_dict(name, configuration):
    """Helper to extract a saved runtime environment"""
    if is_0install_re(name, configuration):
        return get_0install_re_dict(name, configuration)

    re_dict = load(os.path.join(configuration.re_home, name))
    if not re_dict:
        return (False, 'Could not open runtime environment %s' % name)
    else:
        return (re_dict, '')

# this was del_re before...
def delete_runtimeenv(re_name, configuration):
    """Delete an existing runtime environment"""
    status, msg = True, ""
    # Lock the access to the runtime env files, so that deletion is done
    # with exclusive access.
    lock_path = os.path.join(configuration.re_home, WRITE_LOCK)
    lock_handle = open(lock_path, 'a')
    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)

    filename = os.path.join(configuration.re_home, re_name)
    if os.path.isfile(filename):
        try:
            os.remove(filename)
        except Exception, err:
            msg = "Exception during deletion of runtime enviroment '%s': %s"\
                  % (re_name, err)
            status = False
    else:
        msg = "Tried to delete non-existing runtime enviroment '%s'" % re_name
        configuration.logger.warning(msg)
        status = False
    lock_handle.close()
    return (status, msg)
    

def create_runtimeenv(filename, client_id, configuration):
    """Create a new runtime environment"""
    result = parser.parse(filename)
    external_dict = rekeywords.get_keywords_dict()

    (status, parsemsg) = parser.check_types(result, external_dict,
            configuration)

    try:
        os.remove(filename)
    except Exception, err:
        msg = \
            'Exception removing temporary runtime environment file %s, %s'\
             % (filename, err)

    if not status:
        msg = 'Parse failed (typecheck) %s' % parsemsg
        return (False, msg)

    new_dict = {}

    # move parseresult to a dictionary

    for (key, value_dict) in external_dict.iteritems():
        new_dict[key] = value_dict['Value']

    new_dict['CREATOR'] = client_id
    new_dict['CREATED_TIMESTAMP'] = datetime.datetime.now()

    re_name = new_dict['RENAME']

    re_filename = os.path.join(configuration.re_home, re_name)

    # Lock the access to the runtime env files, so that creation is done
    # with exclusive access.
    lock_path = os.path.join(configuration.re_home, WRITE_LOCK)
    lock_handle = open(lock_path, 'a')
    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)

    status, msg = True, ''
    if os.path.exists(re_filename):
        status = False
        msg = \
            "can not recreate existing runtime environment '%s'!" % re_name

    try:
        dump(new_dict, re_filename)
    except Exception, err:
        status = False
        msg = 'Internal error saving new runtime environment: %s' % err

    lock_handle.close()
    return (status, msg)

def zero_install_replace(required_res, provided_res, configuration):
    """replaces the job's RE requirements specified (arg.1) by
       environment definitions and ZI requirement, leaving out the
       provided REs.

       ZI configuration needed: name of ZI RE, name of variable for launch
           ( as a pair in configuration.zero_install_re )

       Returns: ([env.var. def.], modified required_res)

       The env.var definitions use the provided runtime environment
       definitions for zero-install itself, to bring them in scope early.
    """

    logger   = configuration.logger

    logger.debug("zero_install_replace, %s, %s" % (required_res, provided_res))

    if not configuration.zero_install_re:
        logger.debug("ZI not configured, returning unchanged")
        return ([], required_res)

    zi_res   = list_0install_res(configuration)

    if not zi_res:
        logger.debug("NO ZI software found, returning unchanged")
        return ([], required_res)

    logger.debug("ZI software: %s" % zi_res)

    (zi_re, zi_launch_var) = configuration.zero_install_re

    # We assume that zero-install itself is provided by the
    # resource, otherwise our definitions above will not work in
    # practice anyway.

    zi_env = dict(provided_res).get(zi_re,[])
    if not zi_env:
        logger.debug("NO ZI provided on the resource, returning unchanged")
        return ([], required_res)

    # The user ENV variables will be set before the runtime
    # env. variable. Hence, we need to pick up the 0launch definition
    # from the provided REs and use it for our env_vars.
    # (we try our best using "0launch" otherwise)

    zi_launch_cmd = dict(zi_env).get(zi_launch_var, None)
    if not zi_launch_cmd:
        logger.error("ZI configuration error: variable content not found")
        zi_launch_cmd = '0launch'
    else:
        # unquote the 0launch command (might be quoted with options in RE)
        zi_launch_cmd = zi_launch_cmd.replace('"', '')
        zi_launch_cmd = zi_launch_cmd.replace("'", "")

    def zi_launch(bin, url):
        if bin == '':
            return "\"%s -c %s\"" % (zi_launch_cmd, url)
        else:
            return "\"%s -c -m %s %s\"" % (zi_launch_cmd, bin, url)

    real_res = []
    env_vars = []

    for re in required_res:

        if re in [k for (k,_) in provided_res]:
            # provided_res carries the respective configuration (var-list)
            real_res.append(re)

        else:
            logger.debug("Need to provide env %s using Zero Install" % re)

            if not re in zi_res:
                # zi_res is a dictionary, so this works without pattern match
                logger.debug("RE mismatch: %s neither ZI (%s), nor provided by resource (%s)" % \
                             (re, zi_res, provided_res))
                # this can still make sense (precedence of 0-install
                # over native), so keep as required RE, go on
                real_res.append(re)

            # get RE information for replacement.
            # use the url from the dictionary instead of retrieving it again.
            url = zi_res.get(re, '(unknown)')
            (re_dict, msg) = get_0install_re_dict(re, configuration, url)
            if msg:
                logger.error("Could not retrieve data for RE %s: %s" % \
                             (re, msg))
                # keep as required RE, go on with next one
                real_res.append(re)

            else:
                for e in re_dict['ENVIRONMENTVARIABLE']:
                    # in re_dict {name: .., example: .., description: ..}
                    # where "name" is upper case of "example",  the bin name
                    env_vars.append( (e['name'], zi_launch(e['example'], url)))

    if env_vars:

        # if anything has been added here, we need the ZI RE we have
        # hard-wired the 0launch command path anyway, so this is "just
        # to be sure"

        real_res.append(zi_re)

    logger.debug("returning (%s,%s)" % (env_vars, real_res))

    return (env_vars, real_res)
