#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# refunctions - [insert a few words of module description on this line]
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
# -- END_HEADER ---
#

"""Runtime Environment functions"""

import os
import datetime
import fcntl
import urllib
import xml.dom.minidom as xml

import shared.parser as parser
import shared.rekeywords as rekeywords
from shared.fileio import pickle, unpickle
from shared.validstring import valid_dir_input
#from shared.parser import parse 
from shared.shared.serial import load, dump

def list_runtime_environments(configuration):
    re_list = []
    dir_content = []

    try:
        dir_content = os.listdir(configuration.re_home)
    except Exception:
        if not os.path.isdir(configuration.re_home):
            try:
                os.mkdir(configuration.re_home)
            except Exception, err:
                configuration.logger.info('refunctions.py: not able to create directory %s: %s'
                         % (configuration.re_home, err))

    for entry in dir_content:

        # Skip dot files/dirs and the rte.lock

        if (entry.startswith('.')) or (entry == "rte.lock"):
            continue
        if os.path.isfile(configuration.re_home + entry):

            # entry is a file and hence a re

            re_list.append(entry)
        else:
            configuration.logger.info('%s in %s is not a plain file, move it?'
                     % (entry, configuration.re_home))

    return (True, re_list)


def is_runtime_environment(re_name, configuration):
    if not valid_dir_input(configuration.re_home, re_name):
        configuration.logger.warning("registered possible illegal directory traversal attempt re_name '%s'"
                 % re_name)
        return False
    if os.path.isfile(configuration.re_home + re_name):
        return True
    else:
        return False

def list_0install_res(configuration):
    """Reads repo.conf of the software repository (location configurable),
    returns dictionary of ( RE-name, URL of 0install feed xml )"""

    # this is a dummy definition, remove when merging with the real code
    if not configuration.site_swrepo_url:
        return []

    return {'flac':'http://localhost:10080/0install/flac.xml',
            'blast2':'http://localhost:10080/0install/blast2.xml'}

def is_0install_re(name, configuration):
    """Simple check, inefficient if called many times"""
    list = list_0install_res(configuration)
    return (name in list)

def get_0install_re_dict(name, configuration):
    """ http get and parse the 0install feed xml, extracting required information"""

    # read the URL from the repo.conf (make sure method fails later if name is invalid)
    res = list_0install_res(configuration)
    url = res.get(name,"(undefined)")

    # read in the XML using http
    try:
        h    = urllib.urlopen(url)
        feed = h.read() # FIXME make sure all contents are read (not guaranteed with urllib2)
        h.close()
    except Exception, err:
        configuration.logger.error('Error opening required URL' + \
                                    ' %s for %s: %s.' % (url, name, err))
        return (False, 'Could not open required URL ' + \
                       '%s for runtime environment %s' % (url,name))
    
    re_dict = {}
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
        empty  = [ 'TESTPROCEDURE', 'VERIFYSTDOUT', 'VERIFYSTDERR', 'VERIFYSTATUS']
        re_dict.update([ (e,'') for e in empty])

        # Directly mapped fields between XML and RE keywords:
        re_dict['NAME'] = textFrom('name').upper()
        re_dict['DESCRIPTION'] = textFrom('summary')
            
        # one SOFTWARE field, containing a dictionary with 
        # 'name', 'version', 'url', 'description', 'icon'
        software = {}
        software['version'] = 'can be provided by zero-install'
        software['name']        = textFrom('name')
        software['url']         = textFrom('homepage')
        software['description'] = textFrom('description')
        software['icon']        = textFrom('icon')
        
        re_dict['SOFTWARE'] = [software]

        # build ENVIRONMENTVARIABLE definitions, each containing a dictionary
        # of 'name', 'example', 'description'
        binaries = feeddoc.getElementsByTagName('binary')
        if binaries:
            env_vars = [ {'name':b.getAttribute('name').__str__().upper(), 
                          'example':'(none)',
                          'description':'An executable binary in the package'}
                        for b in binaries ]
        else:
            # not defined. Use package name as the only definition
            env_vars = [{'name': software['name'], 
                         'example': '(none)', 
                         'description': 'An executable binary'}]

        re_dict['ENVIRONMENTVARIABLE'] = env_vars

    except Exception, err:
        raise err
        configuration.logger.error('Error parsing xml for %s: %s.\n XML dump: %s' % (name, err, feed))
        return (False, 'Could not parse runtime environment %s' % (name))

    return re_dict

def getText(nodelist):
    """concatenate all CData found in nodelist, convert to ASCII"""
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc.__str__()

def get_re_dict(name, configuration):
    dict = unpickle(configuration.re_home + name, configuration.logger)
    if not dict:
        return (False, 'Could not open runtimeenvironment %s' % name)
    else:
        return (dict, '')

#Function for determining whether or not a runtimeenvironment is active:
def is_re_active(res_map, re_name, configuration):
    #Lock down access to resources, ensuring exclusive access during deletion
    lock_path = os.path.join(configuration.resource_home, "resource.lock")
    lock_handle = open(lock_path, 'a')
    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)

    actives = []

    for res in res_map:
        for rte in res_map[res]['__conf__']['RUNTIMEENVIRONMENT']:
            if rte[0] == re_name:

                #Building the path to relevant config files
                path = configuration.resource_home + str(res)
                config_file = path + "/" + "config"

                #Check if the rte is in the resource under investigation.
                if rte in res_map[res]['__conf__']['RUNTIMEENVIRONMENT']:
                    actives.append(res)

    #Release the lock on the resources.
    lock_handle.close()
 
    #If the RTE was found in any resource, (true, actives) is returned.
    #Otherwise (False, actives), as to indicate whether the RTE is active or not
    if len(actives) > 0:
        return (True, actives)
    else:
        return (False, actives)

                

                
        



#Function for removing an RTE from all resources.
def del_re_from_resources(res_map, re_name, configuration):
    #Lock down access to resources, ensuring exclusive access during deletion
    lock_path = os.path.join(configuration.resource_home, "resource.lock")
    lock_handle = open(lock_path, 'a')
    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)


    #Iterate over all resources, removing RTE re_name from the resources
    for res in res_map:        
        for rte in res_map[res]['__conf__']['RUNTIMEENVIRONMENT']:
            if rte[0] == re_name:

                #Building the path to relevant config files
                path = configuration.resource_home + str(res)
                config_file = path + "/" + "config"

                #Remove RTE re_name from the config file and write it back
                res_map[res]['__conf__']['RUNTIMEENVIRONMENT'].remove(rte)
                dump(res_map[res]['__conf__'],config_file)
                
                #Load and parse the MRSL file for the resource
                mrsldata = parser.parse(config_file + ".MiG")

                #Iterate through the parse tree for the MRSL file,
                #removing any entry of RTE re_name
                for section in mrsldata:
                    if section[0] == "::RUNTIMEENVIRONMENT::":
                        start = section[1].index("name: " + re_name)
                        next_rte = False
                        stop = start
                        while not next_rte:
                            stop =stop + 1
                            if not stop < len(section[1]):
                                next_rte = True
                                
                            else:
                                if section[1][stop][0:5] == "name:":
                                    next_rte = True
                        del section[1][start:stop]
                        
                #Build MRSL string from the revised parse tree
                mrsl = ""
                for section in mrsldata:
                    mrsl = mrsl + section[0]  + "\n"
                    for item in section[1]:
                        mrsl = mrsl + item + "\n"
                    mrsl = mrsl + "\n"



                #Write MRSL string to config.tmp
                tmp_path = config_file + ".tmp"
                accepted_path = config_file + ".MiG"

                try:
                    fh = open(tmp_path, 'w')
                    fh.write(mrsl)
                    fh.close()
                except Exception, err:
                    pass #FILL OUT


                #Truncate the temporary file with the real one.
                try:
                    os.rename(tmp_path, accepted_path)
                except Exception, err:
                    pass
                   
    
    #Release the lock on the resources.
    lock_handle.close()
    return (True, "")



#Function for deleting a RTE
def del_re(re_name, configuration):
    #Lock the access to the RTE files, so that deletion is done with exclusive access.
    lock_path = os.path.join(configuration.re_home, "rte.lock")
    lock_handle = open(lock_path, 'a')
    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)

    #If the RTE does not exists, an error is returned
    if not valid_dir_input(configuration.re_home, re_name):
        msg = "registered possible illegal directory traversal attempt re_name '%s'" % re_name
        configuration.logger.warning(msg)
        lock_handle.close()      
        return False, msg
    
    #If the RTE does exists, deletion is atempted. If an error acours, it is returned.
    filename = configuration.re_home + re_name
    if os.path.isfile(configuration.re_home + re_name):
        try:
            os.remove(filename)
            lock_handle.close()
            return True, ""        
        except Exception, err:
            msg = "Exception during deletion of runtime enviroment '%s'" %re_name
            lock_handle.close()
            return False, msg
            
    else:
        msg = "Tried to delete unexisting runtime enviroment '%s'" %re_name
        configuration.logger.warning(msg)
        lock_handle.close()
        return False, msg
    
    
    

def create_runtimeenv(filename, client_id, configuration):
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

        # should we exit because of this? o.reply_and_exit(o.ERROR)

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

    pickle_filename = configuration.re_home + re_name

    if os.path.exists(pickle_filename):
        msg = \
            "'%s' not created because a runtime environment with the same name exists!"\
             % re_name
        return (False, msg)

    if not pickle(new_dict, pickle_filename, configuration.logger):
        msg = 'Error pickling and/or saving new runtime environment'
        return (False, msg)

    # everything ok

    return (True, '')


def get_active_re_list(re_home):
    result = []
    try:
        re_list = os.listdir(re_home)
        for re in re_list:
            re_version_list = os.listdir(re_home + re)
            maxcounter = -1
            for re_version in re_version_list:
                if -1 != re_version.find('.RE.MiG'):
                    lastdot = re_version.rindex('.RE.MiG')
                    counter = int(re_version[:lastdot])
                    if counter > maxcounter:
                        maxcounter = counter

        if -1 < maxcounter:
            result.append(re + '_' + str(maxcounter))
    except Exception, err:

        return (False,
                'Could not retrieve Runtime environment list! Failure: %s'
                 % str(err), [])

    return (True, 'Active RE list retrieved with success.', result)


