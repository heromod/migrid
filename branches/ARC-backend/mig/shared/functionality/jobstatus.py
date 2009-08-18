#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# jobstatus - Display status of jobs
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

"""Job status back end functionality"""

import os
import time

import shared.returnvalues as returnvalues
from shared.functional import validate_input_and_cert
from shared.parseflags import verbose, sorted
from shared.init import initialize_main_variables
from shared.useradm import client_id_dir

import shared.arcwrapper as arc

def signature():
    """Signature of the main function"""

    defaults = {
        'job_id': [],
        'max_jobs': ['1000000'],
        'flags': [''],
        'project_name': [],
        }
    return ['jobs', defaults]


def sort(paths, new_first=True):
    """Sort list of paths after modification time. The new_first
    argument specifies if the newest ones should be at the front
    of the resulting list.
    """

    mtime = os.path.getmtime
    if new_first:
        paths.sort(lambda i, j: cmp(mtime(j), mtime(i)))
    else:
        paths.sort(lambda i, j: cmp(mtime(i), mtime(j)))
    return paths


def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(op_header=False)
    client_dir = client_id_dir(client_id)
    status = returnvalues.OK
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

    flags = ''.join(accepted['flags'])
    max_jobs = int(accepted['max_jobs'][-1])
    order = 'unsorted '
    if sorted(flags):
        order = 'sorted '
    patterns = accepted['job_id']
#    project_names = accepted['project_name']
#
#    if len(project_names) > 0:
#        for project_name in project_names:
#            project_name_job_ids = \
#                get_job_ids_with_specified_project_name(client_id,
#                    project_name, configuration.mrsl_files_dir, logger)
#            patterns.extend(project_name_job_ids)
#
#    # Please note that base_dir must end in slash to avoid access to other
#    # user dirs when own name is a prefix of another user name
#
#    base_dir = \
#        os.path.abspath(os.path.join(configuration.mrsl_files_dir,
#                        client_dir)) + os.sep
    output_objects.append({'object_type': 'header', 'text'
                          : 'MiG %s job status' % order})

    if not patterns:
        output_objects.append({'object_type': 'error_text', 'text'
                              : 'No job_id specified!'})
        return (output_objects, returnvalues.NO_SUCH_JOB_ID)

    if verbose(flags):
        for flag in flags:
            output_objects.append({'object_type': 'text', 'text'
                                  : '%s using flag: %s' % (op_name,
                                  flag)})

#    if not os.path.isdir(base_dir):
#        output_objects.append({'object_type': 'error_text', 'text'
#                              : 'You have not been created'
#                               + ' as a user on the MiG server!'
#                               + ' Please contact the MiG team.'})
#        return (output_objects, returnvalues.CLIENT_ERROR)

    try: 
        dir = os.path.join(configuration.user_home,client_dir)
        session_Ui = arc.Ui(dir)

        if patterns == ['*']:
            jobvalues = session_Ui.AllJobStatus()
            logger.debug(jobvalues)
        else:
            jobs = [] # for now, should be GetJobIDs => filter by match 
            jobvalues = {}
            for job in jobs:
                jobval = session_Ui.jobStatus(job)
                jobvalues[job] = jobval

    except arc.NoProxyError, err:
        logger.error('No valid proxy found for job status: %s' % err.what())
        output_objects.append({'object_type':'warning',
                               'text':'Proxy error while retrieving job status:\n'
                               +' %s' % err})
        output_objects = output_objects + arc.askProxy()
        return(output_objects, returnvalues.ERROR)
    except Exception, err:
        logger.error('Exception while retrieving job status\n%s' % err) 
        output_objects.append({'object_type':'warning',
                               'text':'Could not retrieve status: %s' % err})
        return(output_objects, returnvalues.ERROR)

    # format output, iterating over jobvalues:
    
    if len(jobvalues) == 0 :
            output_objects.append({'object_type': 'error_text', 'text'
                                  : '%s: You do not have any matching job IDs!'
                                   % patterns})
            status = returnvalues.CLIENT_ERROR
    
    if max_jobs < len(jobvalues):
        output_objects.append({'object_type': 'text', 'text'
                              : 'Only showing first %d of the %d matching jobs as requested'
                               % (max_jobs, len(jobvalues))})
        jobvalues = jobvalues[:max_jobs]

    # Iterate through jobs and print details for each

    job_list = {'object_type': 'job_list', 'jobs': []}

    for job_id in jobvalues.keys():
        job_obj = {'object_type': 'job', 
                   'job_id': ' (' + jobvalues[job_id]['name'] + ')' + job_id }
        job_obj['status'] = jobvalues[job_id]['status']
        job_obj['received_timestamp'] = jobvalues[job_id]['submitted']
        if jobvalues[job_id].has_key('completed'):
            job_obj['finished_timestamp'] = jobvalues[job_id]['completed']

        # hacked in more values here...
        if jobvalues[job_id].has_key('cpu_time') \
            and jobvalues[job_id].has_key('cpu_time'): 
            job_obj['execution_histories'] = \
                [{'count':'',
                  'execution_history':{'executing':
                                  'CPU time: %s, Wall time: %s'\
                                    % (jobvalues[job_id]['cpu_time' ],
                                       jobvalues[job_id]['wall_time'])}}]
        else:
            job_obj['execution_histories'] = []

        # get the suffix (local job directory):
        (prefix, job_dir) = arc.splitJobId(job_id)
                
        job_obj['statuslink'] = {'object_type': 'link',
                                 'destination': 'ls.py?path=%s/%s/*'\
                                  % ('.', job_dir), 
                                  'text': 'View local output files'}
        # changed the meaning here:
        job_obj['mrsllink'] = {'object_type': 'link',
                               'destination': 'downloadjob.py?job_id=%s'\
                                % job_id,
                               'text': 'Download job output'}

        job_obj['resubmitlink'] = {'object_type': 'link',
                                   'destination': 'resubmit.py?job_id=%s'\
                                    % job_id, 'text': 'Resubmit job'}

        job_obj['cancellink'] = {'object_type': 'link',
                                 'destination': 'canceljob.py?job_id=%s'\
                                  % job_id, 'text': 'Cancel job'}
        job_obj['jobschedulelink'] = {'object_type': 'link',
                'destination': 'jobschedule.py?job_id=%s' % job_id,
                'text': 'Request schedule information'}
        job_obj['liveoutputlink'] = {'object_type': 'link',
                'destination': 'liveoutput.py?job_id=%s' % job_id,
                'text': 'Request live update'}

        job_list['jobs'].append(job_obj)

    output_objects.append(job_list)
    output_objects.append({'object_type': 'text', 'text': ''})

    return (output_objects, status)


