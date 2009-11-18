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
import urllib
import re
import sys
import time

import simplejson as json

import shared.returnvalues as returnvalues
from shared.init import initialize_main_variables, find_entry
from shared.functional import validate_input
from shared.safeinput import html_escape


# allowed parameters, first value is default
displays = ['machine','user','summary']
time_groups = ['month', 'week', 'day']


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
    group_in_time = accepted['group_in_time'][-1] # day, week, month
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

    # always include a form to re-display with different values:
    updateform = '           <form action="%s" >' %  \
                 os.path.basename(sys.argv[0])
    updateform +='''
                <table class="runtimeenventry">
                  <tr>
                    <th>Grouping by time
                    <th>Start (YYYY-MM)
                    <th>End (YYYY-MM)
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

    # determine the view and group level to use:

    # we use couchdb views with name convention <group-in-time>-<display>
    view = group_in_time + '-' + display

    # default group-level (max. 2 view components relevant)
    group_level = 2

    # could handle summary display specially, by setting group_level = 1
    # and using either <time>-machine or <time>-user view
#    if display == 'summary':
#        display = 'user'
#        group_level = 1

    # construct start and end key.

    # machine and user cannot be filtered from the user, only 
    # time can be specified, and as YYYY-MM only.
    # for view per week, we have to convert it to a week number
    # python starts by week 0, whereas javascript starts by week 1
    if group_in_time == 'week':
        t = time.strptime(time_start + '-07',"%Y-%m-%d")
        time_start = time.strftime("%Y,week%U",t)

    start_key = '["'+ time_start.replace("-"," ") + '",null]'
    # 2nd component: user or machine
    # TODO allow only own user ID and only machines owned???
    # drawback: cannot restrict user/machine when requesting more than one time period 
    # To restrict user/machine, views which have this as the first key part 
    # have to be used. In which case only one user can be selected 
    # to keep the time period selection valid.

    if not time_end:
        end_key = '[{},{}]'
        end = '{}'
    else:
        if group_in_time == 'week':
            t = time.strptime(time_end + '-07',"%Y-%m-%d")
            end_key = '["'+ time.strftime("%Y,week%U-",t) + '",{}]'
        else:
            end_key = '["'+ time_end.replace("-"," ") + ' 32' + '",{}]'
            # append last day, so inclusive end

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
    query += urllib.urlencode({'group'      : 'true',
                               'group_level': group_level,
                               'startkey'   : start_key,
                               'endkey'     : end_key,
                               })
    try:
        logger.debug("asking database at %s: %s" % (db_url,query))
        res = urllib.urlopen('http://' + db_url + query)
        jsonreply = res.read()
        res.close()
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

    if group_level == 1: 
        # if view not grouped in time (currently unused)
        # => only one column, but rows with other keys
        dates = ['']
        datarows = [ [k[0],lookupdict[k]] for k in lookupdict]
    else:
        #   split off dates (eliminate dup.s and sort them)
        # date comes first in keys for all views we are using 
        dates = list(set([ date[0] for date in lookupdict ])) # :p
        dates.sort()

        # build data rows, fill in missing data...
        nullval = {'count':0, 'wall_duration':0,'charge':0}
        keys = set([ date[-1] for date in lookupdict ])
        datarows = []
        for k in keys:
            row = [k]
            for d in dates:
                if (d,k) in lookupdict:
                    row.append(lookupdict[(d,k)])
                else:
                    row.append(nullval)
            datarows.append(row)

    # could split rows with excessive length into several rows
    # (repeat header row with new headers, or make it two tables)
        
    # TODO extend the visualisation options here, estimate width by 
    # length of date list 

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

    # include javascript for visualisation...
    # we do this here, when we know how much data to show.

    # visualisations for the different queries:
    bar_default = "barMargin:'0',barGroupMargin:'4',height:'300'"
    pie_default = "type:'pie',height:'200',width:'400'"

    bars = len(dates) * len(datarows)
    # default width is table width. Avoid extremes...
    if bars < 30 or len(datarows) < 3:    # limit to a maximum width
        w = bars * 30 
    elif bars > 150: # enforce a minimum width
        w = bars * 10
    else:
        w = None
    if w: bar_default += ',width:"%s"' % w

    # predefine 30 colours ( lazy way )
    seq = [0,9,12,2,11,4,6,13,15,1,8,10,14,3,5,7]
    colours = [ ('#%1X0%1X0%1X0' % (x,y,z))
                 for (x,y,z) in zip(seq[2:15]+seq,seq[1:15]+seq[1:15],seq+seq[2:15]) ] 

    cols = ",colors:%s" % str(colours)
    viz_options = { 'machine': [bar_default + cols]
                       ,'user': [bar_default + cols, pie_default + cols]
                       ,'summary': [bar_default + cols]
                       }
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

    # and done
    return (output_objects, returnvalues.OK)

