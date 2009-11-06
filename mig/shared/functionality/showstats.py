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


# allowed parameters, first value is default
displays = ['machine','user']
time_groups = ['month', 'week', 'day', 'all']

def signature():
    """Signature of the main function"""

    defaults = { 'group_in_time':time_groups[0:1]
                 ,'display'     :displays[0:1]
                 ,'summary'     :[''] # means: no grouping by display item
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

    # include javascript for visualisation...
    title_entry['javascript'] = \
"""        <link rel="stylesheet" type="text/css" 
             href="/images/css/stats.visualize.css" />
         <script type="text/javascript" 
                 src="/images/js/jquery.js"></script>
         <script type="text/javascript" 
                 src="/images/js/visualize.jQuery.js"></script>
         <script type="text/javascript">
             jQuery(function(){
                 //make some charts
                 $('.stats').visualize({type: 'line'});
                 $('.stats').visualize({type: 'pie'});
                 $('.stats').visualize();
                 });
         </script>
<!-- 
 http://www.filamentgroup.com/lab/jquery_visualize_plugin_accessible_charts_graphs_from_tables_html5_canvas/ 
 http://github.com/marclove/jquery-visualize
-->
"""

    # read view options
    group_in_time = accepted['group_in_time'][-1] # all, month, day, year
    time_start    = accepted['time_start'][-1]
    display       = accepted['display'][-1] # machine, user
    grouping      = True
    if accepted['summary'][-1] == 'on':
        grouping = False

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

    # always include a form to re-display with different values:
    updateform = '           <form action="%s" >' %  \
                 os.path.basename(sys.argv[0])
    updateform +='''
                <table>
                  <tr>
                    <th>Grouping by time
                    <th>Start <th>End
                    <th>Category<th>Summary?
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
    summary_checked = ''
    if not grouping:
        summary_checked = 'CHECKED'
    updateform +='''
                        </select>
                    <td><input type="checkbox" name="summary" %s>
                  <tr><td colspan="4"><td><input type="submit" value="Update View">
                </table>
            </form>
            <hr>
''' % summary_checked

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

    if not grouping:
        # global statistics per-time only, use a different view
        view = group_in_time + '-' + 'user-machine'
        group_level = group_level - 1
        start_key = '['+ start + ',null,null]'
        end_key = '['+ end + ',{},{}]'
    else:
        # normal: use predefined views and defaults
        view = display + '-' + group_in_time

        if display == 'user':
            # only own user ID allowed
            start_key = '[' + client_id + ','+ start + ']'
            end_key = '[' + client_id + ','+ end + ']'
        else:
            # all machines allowed (?)
            start_key = '[null,'+ start + ']'
            end_key = '[{},'+ end + ']'
            
    # couchdb URL, default http://localhost:5984/
    database = 'http://localhost:5984/' # TODO use configuration.usagedb
    
    # to proceed: 
    #  1. get json data from couchdb using the view
    #     group=true, group_level as calculated,
    #     start and end key as constructed

    # we generate some dummy data here instead...
    if view == 'user-month': # user Rasmus_Andersen, from 06 2007
        jsonreply = \
"""{"rows":[
{"key":["Rasmus_Andersen","2007-06"],"value":{"count":2,"wall_duration":7,"charge":7}},
{"key":["Rasmus_Andersen","2007-08"],"value":{"count":110,"wall_duration":360208,"charge":360208}},
{"key":["Else_Someone","2007-09"],"value":{"count":493,"wall_duration":941665,"charge":941665}},
{"key":["Else_Someone","2007-10"],"value":{"count":303,"wall_duration":33751,"charge":33751}},
{"key":["Rasmus_Andersen","unknown"],"value":{"count":9,"wall_duration":0,"charge":0}}
]}
"""
    elif view == 'machine-month': # small sample!, from 5 2007
        jsonreply = \
"""{"rows":[
{"key":["amigos24.diku.dk.1","2007-09"],"value":{"count":8,"wall_duration":693,"charge":693}},
{"key":["lucia.imada.sdu.dk.0","2007-05"],"value":{"count":11,"wall_duration":267,"charge":267}},
{"key":["lucia.imada.sdu.dk.0","2007-08"],"value":{"count":15,"wall_duration":6617,"charge":6617}},
{"key":["lucia.imada.sdu.dk.0","2007-09"],"value":{"count":861,"wall_duration":1908082,"charge":1908082}},
{"key":["lucia.imada.sdu.dk.0","2007-10"],"value":{"count":329,"wall_duration":569629,"charge":569629}},
{"key":["lucia.imada.sdu.dk.0","2007-11"],"value":{"count":20,"wall_duration":0,"charge":0}},
{"key":["lucia.imada.sdu.dk.0","2008-01"],"value":{"count":3,"wall_duration":0,"charge":0}},
{"key":["niflheim.fysik.dtu.dk.0","2007-05"],"value":{"count":28,"wall_duration":6894,"charge":22376}},
{"key":["niflheim.fysik.dtu.dk.0","2007-06"],"value":{"count":6,"wall_duration":3339,"charge":5945}}
]}
"""
    else:  # view = month-user-machine, group-level=1, 06 to 10 2007
        jsonreply = \
"""{"rows":[
{"key":["2007-06"],"value":{"count":2224,"wall_duration":72463,"charge":75069}},
{"key":["2007-08"],"value":{"count":125,"wall_duration":366825,"charge":366825}},
{"key":["2007-09"],"value":{"count":2279,"wall_duration":4409175,"charge":4409175}},
{"key":["2007-10"],"value":{"count":653,"wall_duration":687981,"charge":687981}}
]}
"""

    #  2. convert from json to dictionary, extract values we need
    # ...we do not really need json here...
    data = eval(jsonreply)['rows'] # :: list of dict with "key","value"

    lookupdict = dict( [ (tuple(d['key']),d['value']) for d in data ] )

    #   split off dates (eliminate dup.s and sort them)
    
    dates = list(set([ date[-1] for date in lookupdict ])) # :p
    dates.sort()

    # build data rows
    if not grouping:
        datarows = [['(All)'] + [ lookupdict[date] for d in dates ]]
        output_objects.append({'object_type':'error_text', 'text'
                               :'FIXME! wrong selection!'}) 
        output_objects.append({'object_type':'html_form', 'text'
                               :'lookup: %s <br>dates: %s <br>rows: %s'
                                 % (lookupdict,dates,datarows)}) 
    else:
        # fill in missing data...
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
        html += '</table>'
        output_objects.append({'object_type': 'html_form', 'text'
                              : html})

    # and done
    return (output_objects, returnvalues.OK)

