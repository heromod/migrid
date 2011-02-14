#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# resadmin - [insert a few words of module description on this line]
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

"""Enable resource administrators to manage their own resources
through a web interface. Management includes adding new
resources, tweaking the configuration of existing resources,
starting, stopping and getting status of resources, and
administrating owners.
"""

import os
import time

import shared.returnvalues as returnvalues
from shared.base import sandbox_resource
from shared.functional import validate_input_and_cert
from shared.init import initialize_main_variables, find_entry
from shared.refunctions import get_re_dict, list_runtime_environments
from shared.vgridaccess import get_resource_map, CONF, OWNERS


def signature():
    """Signature of the main function"""

    defaults = {'benchmark': ['false'], 'unique_resource_name': []}
    return ['html_form', defaults]


def display_resource(
    resourcename,
    raw_conf,
    resource_config,
    owners,
    re_list,
    configuration,
    ):
    """Format and print the information and actions for a
    given resource.
    """

    exe_units = []
    store_units = []
    frontend = None
    hosturl = None
    html = ''
    row_name = ('even_row', 'odd_row')

    if resource_config:
        if resource_config.has_key('EXECONFIG'):
            for exe in resource_config['EXECONFIG']:
                exe_units.append(exe['name'])
        if resource_config.has_key('STORECONFIG'):
            for store in resource_config['STORECONFIG']:
                store_units.append(store['name'])
        if resource_config.has_key('FRONTENDNODE'):
            frontend = resource_config['FRONTENDNODE']
        if resource_config.has_key('HOSTURL'):
            hosturl = resource_config['HOSTURL']

    # Try to split resourcename first to support resources where name
    # doesn't match hosturl.

    sep = '.'
    index = resourcename.rfind(sep)
    if index:
        hosturl = resourcename[:index]
        identifier = resourcename[index + 1:]
    elif hosturl:
        identifier = resourcename.replace(hosturl + sep, '')
    else:
        print 'WARNING: failed to find host identifier from unique resource name!'
        (hosturl, identifier) = (None, 0)

    html += '<a name="%s"></a>' % resourcename
    html += '<h1>%s</h1>\n' % resourcename
    html += '<h3>Configuration</h3>'
    html += \
        'Use the <a href="resedit.py?hosturl=%s;hostidentifier=%s">editing interface</a> '\
         % (hosturl, identifier)
    html += 'or make any changes manually in the text box below.<br />'
    html += \
        '<a href="docs.py?show=Resource">Resource configuration docs</a>'
    html += '<table class=resources>\n<tr><td class=centertext>'
    html += \
        '''
<form method="post" action="updateresconfig.py">
<textarea cols="100" rows="25" wrap="off" name="resconfig">'''
    for line in raw_conf:
        html += '%s\n' % line.strip()
    html += \
        '''</textarea>
<br />
<input type="hidden" name="unique_resource_name" value="%s" />
<input type="submit" value="Save" />
----------
<input type="reset" value="Forget changes" />
</form>
'''\
         % resourcename
    html += '</td></tr></table><p>'

    html += \
        '<table class=resources><tr class=title><td colspan="5">Front End</td></tr>\n'

    if not frontend:
        html += '<tr><td colspan=5>Not specified</td></tr>\n'
    else:
        html += '<tr><td>%s</td>' % frontend

        for action in ['restart', 'status', 'stop', 'clean']:
            if action == 'restart':
                action_str = '(Re)Start'
            else:
                action_str = action.capitalize()
            html += \
                '''<td>
            <form method="get" action="%sfe.py">
            <input type="hidden" name="unique_resource_name" value="%s" />
            <input type="submit" value="%s" />
            </form>
            </td>
            '''\
                 % (action, resourcename, action_str)
        html += '</tr>'

    html += '<tr class=title><td colspan=5>Execution Units</td></tr>\n'

    if not exe_units:
        html += '<tr><td colspan=5>None specified</td></tr>\n'
    else:
        html += '<tr><td>ALL UNITS</td>'
        for action in ['restart', 'status', 'stop', 'clean']:
            html += \
                '''<td>
            <form method="get" action="%sexe.py">
            <input type="hidden" name="unique_resource_name" value="%s" />
            <input type="hidden" name="all" value="true" />
            <input type="hidden" name="parallel" value="true" />'''\
                 % (action, resourcename)
            if action == 'restart':
                action_str = '(Re)Start'
            else:
                action_str = action.capitalize()
            html += \
                '''
            <input type="submit" value="%s" />
            </form>
            </td>
            '''\
                 % action_str
        html += '</tr>'

        row_number = 1
        for unit in exe_units:
            row_class = row_name[row_number % 2]
            html += '<tr class=%s><td>%s</td>' % (row_class, unit)
            for action in ['restart', 'status', 'stop', 'clean']:
                if action == 'restart':
                    action_str = '(Re)Start'
                else:
                    action_str = action.capitalize()
                html += \
                    '''<td>
                <form method="get" action="%sexe.py">
                <input type="hidden" name="unique_resource_name" value="%s" />
                <input type="hidden" name="exe_name" value="%s" />
                <input type="submit" value="%s" />
                </form>
                </td>
                '''\
                     % (action, resourcename, unit, action_str)
            html += '</tr>'
            row_number += 1

    html += '<tr class=title><td colspan=5>Storage Units</td></tr>\n'

    if not store_units:
        html += '<tr><td colspan=5>None specified</td></tr>\n'
    else:
        html += '<tr><td>ALL UNITS</td>'
        for action in ['restart', 'status', 'stop', 'clean']:
            html += \
                '''<td>
            <form method="get" action="%sstore.py">
            <input type="hidden" name="unique_resource_name" value="%s" />
            <input type="hidden" name="all" value="true" />
            <input type="hidden" name="parallel" value="true" />'''\
                 % (action, resourcename)
            if action == 'restart':
                action_str = '(Re)Start'
            else:
                action_str = action.capitalize()
            html += \
                '''
            <input type="submit" value="%s" />
            </form>
            </td>
            '''\
                 % action_str
        html += '</tr>'

        row_number = 1
        for unit in store_units:
            row_class = row_name[row_number % 2]
            html += '<tr class=%s><td>%s</td>' % (row_class, unit)
            for action in ['restart', 'status', 'stop', 'clean']:
                if action == 'restart':
                    action_str = '(Re)Start'
                else:
                    action_str = action.capitalize()
                html += \
                    '''<td>
                <form method="get" action="%sstore.py">
                <input type="hidden" name="unique_resource_name" value="%s" />
                <input type="hidden" name="store_name" value="%s" />
                <input type="submit" value="%s" />
                </form>
                </td>
                '''\
                     % (action, resourcename, unit, action_str)
            html += '</tr>'
            row_number += 1

    html += '</table><p>'

    html += '<h3>Owners</h3>'
    html += \
        '''
Owners are specified with the Distinguished Name (DN)
from the certificate.<br /> 
<table class=resources>
'''

    html += \
        '''<tr><td>
<form method="get" action="addresowner.py">
<input type="hidden" name="unique_resource_name" value="%s" />
<input type="hidden" name="output_format" value="html" />
<input type="text" name="cert_id" size="30" />
</td><td>
<input type="submit" value=" Add " />
</form>
</td></tr></table><br />
<table class=resources>
'''\
         % resourcename

    for owner_id in owners:
        html += \
            '''<tr><td>
<form method="get" action="rmresowner.py">
<input type="hidden" name="unique_resource_name" value="%s" />
<input type="hidden" name="cert_id" value="%s" />
<input type="hidden" name="output_format" value="html" />
<input type="submit" value="Remove" />
</form>
</td>
'''\
             % (resourcename, owner_id)
        html += '<td>' + owner_id + '</td></tr>'
    html += '</table>'

    # create html to select and execute a runtime environment testprocedure

    html += '<h3>Runtime environments</h3>'

    html += \
        """Verify that resource supports the selected runtime environment.
    <table class=resources>
    <tr><td>
    <form method="get" action="testresupport.py">
    <input type="hidden" name="with_html" value="true" />
    <input type="hidden" name="unique_resource_name" value="%s" />
    <select name="re_name">"""\
         % resourcename

    # list runtime environments that have a testprocedure

    for re in re_list:
        (re_dict, re_msg) = get_re_dict(re, configuration)
        if re_dict:
            if re_dict.has_key('TESTPROCEDURE'):
                if re_dict['TESTPROCEDURE'] != []:
                    html += '<option value=%s>%s' % (re, re)

    html += """</select></td>"""
    html += '<td><input type="submit" name="submit" value="verify" />'
    html += '</form></table><p>'

    # create html to select and call script to display testprocedure history

    html += \
        """Show testprocedure history for the selected runtime environment and the resource with its current configuration.
    <table class=resources>
    <tr><td>
    <form method="get" action="showresupporthistory.py">
    <input type="hidden" name="unique_resource_name" value="%s" />
    <select name="re_name">"""\
         % resourcename

    # list runtime environments that have a testprocedure

    for re in re_list:
        (re_dict, re_msg) = get_re_dict(re, configuration)
        if re_dict:
            if re_dict.has_key('TESTPROCEDURE'):
                if re_dict['TESTPROCEDURE'] != []:
                    html += '<option value=%s>%s' % (re, re)

    html += """</select></td>"""
    html += '<td><input type="submit" name="submit" value="Show" />'
    html += '</form></table><p>'
    return html


def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(op_header=False)
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

    benchmark = accepted['benchmark'][-1].lower() != 'false'
    unique_res_names = accepted['unique_resource_name']
    start_time = time.time()

    (re_stat, re_list) = list_runtime_environments(configuration)
    if not re_stat:
        output_objects.append({'object_type': 'error_text', 'text'
                              : 'Error getting list of runtime environments'
                              })
        return (output_objects, returnvalues.SYSTEM_ERROR)

    title_entry = find_entry(output_objects, 'title')
    title_entry['text'] = 'Resource Management'
    output_objects.append({'object_type': 'header', 'text'
                          : ' Resource Management'})

    output_objects.append({'object_type': 'sectionheader', 'text'
                          : '%s Resources Owned' % configuration.short_title})
    quick_links = [{'object_type': 'text', 'text'
                   : 'Quick links to all your resources and individual mangement'}]
    quick_res = {}
    quick_links_index = len(output_objects)
    output_objects.append({'object_type': 'sectionheader', 'text': ''})

    owned = 0
    res_map = get_resource_map(configuration)
    for unique_resource_name in res_map.keys():
        if sandbox_resource(unique_resource_name):
            continue
        owner_list = res_map[unique_resource_name][OWNERS]
        resource_config = res_map[unique_resource_name][CONF]
        if client_id in owner_list:
            quick_res[unique_resource_name] = \
                {'object_type': 'link', 'text': '%s'\
                  % unique_resource_name,
                 'destination': '?unique_resource_name=%s'\
                 % unique_resource_name}

            if unique_resource_name in unique_res_names:
                raw_conf_file = os.path.join(configuration.resource_home,
                                             unique_resource_name,
                                             'config.MiG')
                try:
                    filehandle = open(raw_conf_file, 'r')
                    raw_conf = filehandle.readlines()
                    filehandle.close()
                except:
                    raw_conf = ['']

                res_html = display_resource(
                    unique_resource_name,
                    raw_conf,
                    resource_config,
                    owner_list,
                    re_list,
                    configuration,
                    )
                output_objects.append({'object_type': 'html_form',
                                       'text': res_html})
            owned += 1

    if owned == 0:
        output_objects.append({'object_type': 'text', 'text'
                              : 'You are not listed as owner of any resources!'
                              })
    else:
        sorted_links = quick_res.items()
        sorted_links.sort()
        for (res_id, link_obj) in sorted_links:
            quick_links.append(link_obj)

            # add new line

            quick_links.append({'object_type': 'html_form', 'text'
                               : '<br />'})
        output_objects = output_objects[:quick_links_index]\
             + quick_links + output_objects[quick_links_index:]

    finish_time = time.time()
    if benchmark:
        output_objects.append({'object_type': 'text', 'text'
                              : 'Resource admin back end delivered data in %.2f seconds'
                               % (finish_time - start_time)})

    return (output_objects, returnvalues.OK)

