#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# showstats - read statistics from couchdb and display them 
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

# showstats.py by Jost Berthold (berthold@diku.dk)
#
"""Read usage statistics from couchdb and display it in html table and
   graphics. Uses jquery visualization module and views defined in
   couchdb (for sgas-experimental)."""

import os
import httplib
import re
import sys

import simplejson as json

import shared.returnvalues as returnvalues
from shared.init import initialize_main_variables, find_entry
from shared.functional import validate_input
from shared.safeinput import html_escape


# allowed parameters, first value is default
displays = ['machine','user', 'summary']
time_groups = ['month', 'week', 'day', 'all']

# visualizations for the different queries:
bar_default = "barMargin:'0',barGroupMargin:'4',height:'300'"
pie_default = "type:'pie',height:'200',width:'400'"
viz_options = { 'machine': [bar_default]
                ,'user': [bar_default, pie_default]
                ,'summary': [bar_default]
               }

def signature():
    """Signature of the main function"""

    defaults = { 'group_in_time':time_groups[0:1]
                 ,'display'     :displays[0:1]
                 ,'time_start'  :['2009-09'] # allowed are year-month strings
                 ,'time_end'    :[]          # ditto. 
               }
    return ['html_form', defaults]


def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(op_header=False)
    logger.debug('Starting showstats: %s' % user_arguments_dict)

    defaults = signature()[1]
    (validate_status, accepted) = validate_input(user_arguments_dict,
            defaults, output_objects, allow_rejects=False)
    logger.debug('Accepted: %s' % accepted)

    if not validate_status:
        return (accepted, returnvalues.CLIENT_ERROR)

    title_entry = find_entry(output_objects, 'title')
    title_entry['text'] = 'Usage Statistics'

    # read view options
    group_in_time = accepted['group_in_time'][-1] # all, month, day, year
    time_start    = accepted['time_start'][-1]
    display       = accepted['display'][-1] # machine, user, summary

    # check arguments against configured lists of valid inputs:
    reject = False

    # make sure: grouping in ['user','machine']
    if not display in displays:
        output_objects.append({'object_type': 'error_text', 'text'
                   : 'invalid display grouping specified: %s' % display })
        display = displays[0]
        reject = True
    # make sure: group_in_time in ['all', 'month', 'day', 'week']
    if not group_in_time in time_groups:
        output_objects.append({'object_type': 'error_text', 'text'
                   : 'invalid time grouping specified: %s' % group_in_time })
        group_in_time = time_groups[0]
        reject = True
    # make sure: start and end match "20[0-9]{2}-[01][0-9]"
    if not re.match('20\d\d-[01]\d', time_start):
        output_objects.append({'object_type': 'error_text', 'text'
                   : 'invalid start time specified: %s' % time_start })
        time_start = '2009-09'
        reject = True

    if accepted['time_end'] and accepted['time_end'] != ['']:
        time_end  = accepted['time_end'][-1]
        if not re.match('20\d\d-[01]\d', time_end):
            output_objects.append({'object_type': 'error_text', 'text'
                   : 'invalid end time specified: %s' % time_end })
            time_end = ''
            reject = True
    else:
        time_end = ''

    # include javascript for visualisation...
    # we do this here, after determining/defaulting "display"
    include_viz = """
<!-- 
 http://www.filamentgroup.com/lab/jquery_visualize_plugin_accessible_charts_graphs_from_tables_html5_canvas/ 
 http://github.com/marclove/jquery-visualize
-->
         <link rel="stylesheet" type="text/css" 
             href="/images/css/stats.visualize.css" />
         <script type="text/javascript" 
                 src="/images/js/jquery.js"></script>
         <script type="text/javascript" 
                 src="/images/js/visualize.jQuery.js"></script>
         <script type="text/javascript">
             jQuery(function(){
"""
    for v in viz_options[display]:
        include_viz += "$('.stats').visualize({" + v + "});"
    include_viz +="""
                 });
         </script>
"""
    title_entry['javascript'] = include_viz

    # always include a form to re-display with different values:
    updateform = '           <form action="%s" >' %  \
                 os.path.basename(sys.argv[0])
    updateform +='''
                <table class="runtimeenventry">
                  <tr>
                    <th>Grouping by time
                    <th>Start
                    <th>End
                    <th>Category
                  <tr>
                    <td><select name="group_in_time">
'''
#     updateform += \
#      ''.join([ '\n<option value="' + t + '">' + t.title() + '</option>'
#                for t in time_groups ])
    for t in time_groups:
        updateform +='<option '
        if group_in_time == t:
            updateform += 'selected '
        updateform += 'value="' + t + '">' + t.title() + '</option>\n'
    updateform +='''
                        </select>
                    <td><input type="text" name="time_start" value="%s">
                    <td><input type="text" name="time_end" value="%s">
''' %  (time_start, time_end) + '''
                    <td><select name="display">
'''
#     updateform += \
#     ''.join([ '\n<option value="' + d + '">' + d.title() + '</option>'
#                 for d in displays ])
    for d in displays:
        updateform +='<option '
        if display == d:
            updateform += 'selected '
        updateform += 'value="' + d + '">' + d.title() + '</option>\n'
    updateform +='''
                        </select>
                    <td><input type="submit" value="Update View">
                </table>
            </form>
            <hr>
'''

    output_objects.append({'object_type': 'html_form', 'text': updateform})
    if reject:
        output_objects.append({'object_type': 'text', 'text'
                   : 'Please check your view parameters.'})
        return(output_objects, returnvalues.CLIENT_ERROR)

    # else: all parameters OK, go:

    # construct start and end key.

    # machine and user cannot be filtered from the user, only 
    # time can be specified, and as YYYY-MM only.
    start = time_start
    if not time_end:
        end = '{}'
    else:
        end = time_end + '-32' # append last day, so inclusive end

    # determine the view and group level to use:

    # default group-level (max. 2 view components relevant)
    group_level = 2

    # handle group_in_time "all" specially:
    #   set view to a coarse unit and group_level = 1
    #   (group_level will be further decreased below if only time)
    if group_in_time == 'all':
        group_in_time = 'month'
        group_level = 1

    # we use couchdb views with name convention <display>-<group-in-time>
    view = display + '-' + group_in_time

    if display == 'summary':
        start_key = '[(Summary),'+ start + ']'
        end_key = '[(Summary),'+ end + ']'
    else:
        # users or machines
        # allow only own user ID???
        start_key = '[null,'+ start + ']'
        end_key = '[{},'+ end + ']'
    # TODO time restriction does not work if user/machine not restricted!
    # need to define the views with date first to allow date restriction,
    # but then we cannot have user restriction.
        

    #  1. get json data from couchdb using the view
    #     group=true, group_level as calculated,
    #     start and end key as constructed

    # couchdb URL, default http://localhost:5984/
    # TODO use configuration.usagedb
    database ='http://localhost:5984/usagerecords' 

    [check,db_url,db_name] = database.rsplit('/',2)
    if check and check != 'http:/':
        logger.debug('bad URL %s' % database)
        db_url = 'none'
        db_name = 'none'
    
    # views are organised in files per "timegrouping",
    # and contain views with names <category>-<timegrouping>
    query = '/'.join(['',db_name,'_design' ,group_in_time,'_view',view])
    query += '?'
    query += '&'.join(['group=true'
                       ,'group_level=%s' % group_level
                       ,'start_key=%s' % html_escape(start_key)
                       ,'end_key=%s'   % html_escape(end_key)])

    try:
        logger.debug("asking database at %s: %s" % (db_url,query))
        conn = httplib.HTTPConnection(db_url)
        conn.request('GET',query)
        res = conn.getresponse()
        logger.debug('response: %s %s' % (res.status, res.reason))
        if res.status != 200:
            logger.error('%s to couchdb at %s replied: %s %s' \
                         % (query, db_url, res.status, res.reason))
            raise Exception(res.reason)
        jsonreply = res.read()
        conn.close()
    except Exception, err:
        logger.error('Could not get data from database: %s' % err)
        output_objects.append({'object_type': 'error_text', 'text'
                   : 'Error accessing the database.' })
        jsonreply = '{"rows":[]}'

    logger.debug('Reply data\n %s' % jsonreply)

    #  2. convert from json to dictionary, extract values we need
    # ...we do not really need json here...
    reply = jsonreply.replace('\r','')
    data = eval(reply)['rows'] # :: list of dict with "key","value"

    if not data:
        output_objects.append({'object_type': 'sectionheader', 'text' :
                               'No data available'})
        output_objects.append({'object_type': 'text', 'text' :
                               '''
The query you have requested did not return any data.
                               '''})
        return (output_objects, returnvalues.OK)

    lookupdict = dict( [ (tuple(d['key']),d['value']) for d in data ] )

    #   split off dates (eliminate dup.s and sort them)
    if group_level == 1: # view not grouped in time
        dates = ['']
        datarows = [ [k[0],lookupdict[k]] for k in lookupdict]
    else:
        dates = list(set([ date[-1] for date in lookupdict ])) # :p
        dates.sort()

        # build data rows, fill in missing data...
        nullval = {'count':0, 'wall_duration':0,'charge':0}
        keys = set([ date[0] for date in lookupdict ])
        datarows = []
        for k in keys:
            row = [k]
            for d in dates:
                if (k,d) in lookupdict:
                    row.append(lookupdict[(k,d)])
                else:
                    row.append(nullval)
            datarows.append(row)
        
    #   build tables for all data we have. could make field names
    # configurable as well, but this is anyway highly proprietary code

    table_names = {'count':'Job Count',
                   'wall_duration': 'Accumulated Wall Clock Time',
                   'charge': 'Accumulated Charge'}
    for key in table_names:
        output_objects.append({'object_type': 'text', 'text' :
                               ''}) # spacer.. :-S
        output_objects.append({'object_type': 'sectionheader', 'text' :
                               table_names[key]})

        html = '<table class="stats"><caption>%s</caption>' % table_names[key]
        
        # fill header (date part of keys) and data (other ky part = col.1)
        # ...
        html += '<thead><tr>'
        # header, col.s are date part of key
        # first col. should be empty and not tagged th
        html += '<td/><th>' + '<th>'.join(dates)
        html += '</thead>\n<tbody>'
        # body, with first col.  key part
        for r in datarows:
            html += '<tr><th>' + r[0] + '<td>'
            html += '<td>'.join([ str(x[key]) for x in r[1:] ])
            
        html += '</tbody>'
        html += '</table></p>'
        output_objects.append({'object_type': 'html_form', 'text'
                              : html})

    # and done
    return (output_objects, returnvalues.OK)

