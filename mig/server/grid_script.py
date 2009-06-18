#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# grid_script - the core job handling daemon on a MiG server
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

"""Main script running on the MiG server"""

import sys
import time
import datetime
import threading
import pickle
import os
import signal
import copy

import jobscriptgenerator
from jobqueue import JobQueue
from shared.configuration import Configuration
from shared.conf import get_configuration_object
from shared.notification import notify_user_thread
from shared.fileio import pickle, unpickle, unpickle_and_change_status, \
    send_message_to_grid_script
from shared.conf import get_resource_exe
from shared.gridscript import clean_grid_stdin, \
    remove_jobrequest_pending_files, check_mrsl_files, requeue_job, \
    server_cleanup, load_queue, save_queue
from shared.resadm import atomic_resource_exe_restart, put_exe_pgid
from shared.vgrid import default_vgrid

try:
    import servercomm
except ImportError, ime:
    print 'could not import servercomm, probably due to missing pycurl'
    print ime


def time_out_jobs(stop_event):
    """Examine queue of current executing jobs and send a JOBTIMEOUT
    message if specified cputime is exceeded.
    Please note that (under load) this decoupling of time out check
    and handling may result in this function sending multiple
    JOBTIMEOUT messages for the same job to the input pipe before
    the first one gets through the pipe and handled. Thus we may see
    'echoes' in the log. 
    """

    # We must make sure that thread keeps running even
    # if the time out code unexpectantly throws an exception

    try:

        # Keep running until main sends stop signal

        counter = 0
        while not stop_event.isSet():
            counter = (counter + 1) % 60

            # Responsive sleep for 60 seconds

            if 0 < counter:
                time.sleep(1)
                continue

            qlen = executing_queue.queue_length()
            if qlen == 0:
                logger.info('No jobs in executing_queue')
            else:
                logger.info('time_out_jobs(): %d job(s) in queue', qlen)

                # TODO: this is a race - 'Main' may modify executing_queue at
                # any time!
                # Especially since we ask it to remove the job we just looked
                # at and then look at the next index, so we may skip jobs
                # if it removes the job before we dequeue next index.
                # We should use locking or at least remove from back to
                # make it slightly better.

                for i in range(0, qlen):
                    job = executing_queue.get_job(i)
                    if not job:
                        logger.warning('time-out RC? found empty job in slot %d!'
                                 % i)
                        continue
                    try:
                        delay = int(job['EXECUTION_DELAY'])
                    except StandardError, err:
                        logger.warning('no execution delay field: %s Exception: %s'
                                 % (job, err))
                        delay = 0
                    try:
                        cputime = int(job['CPUTIME'])
                    except StandardError, err:
                        logger.warning('cputime extraction failed for %s! %s'
                                 % (job, err))
                        cputime = 120
                    extra_cputime = 90
                    total_cputime = delay + extra_cputime + cputime
                    timestamp = job['EXECUTING_TIMESTAMP']

                    # is there a  nicer way to convert time.gmtime() to
                    # a datetime?
                    # Time is in UTC timezone

                    start_executing_datetime = datetime.datetime(
                        timestamp.tm_year,
                        timestamp.tm_mon,
                        timestamp.tm_mday,
                        timestamp.tm_hour,
                        timestamp.tm_min,
                        timestamp.tm_sec,
                        )

                    last_valid_finish_time = start_executing_datetime\
                         + datetime.timedelta(seconds=total_cputime)

                    # now, in utc timezone

                    now = datetime.datetime.utcnow()

                    if now > last_valid_finish_time:
                        logger.info('timing out job %s with allowed time %s including delay %s'
                                     % (job['JOB_ID'], total_cputime,
                                    delay))
                        grid_script_msg = 'JOBTIMEOUT %s %s %s\n'\
                             % (job['UNIQUE_RESOURCE_NAME'], job['EXE'
                                ], job['JOB_ID'])
                        send_message_to_grid_script(grid_script_msg,
                                logger, configuration)
    except Exception, err:
        logger.error('time_out_jobs: unexpected exception: %s' % err)
    logger.info('time_out_jobs: time out thread terminating')


def clean_shutdown(signum, frame):
    """Request clean shutdown when pending requests are handled"""

    print '--- REQUESTING SAFE SHUTDOWN ---'
    shutdown_msg = 'SHUTDOWN\n'
    send_message_to_grid_script(shutdown_msg, logger, configuration)


def graceful_shutdown():
    """This function is responsible for shutting down the server in a
    graceful way. It should only be called by the SHUTDOWN request
    handler to avoid interfering with other active requests.
    """

    print 'graceful_shutdown called'
    try:
        logger.info('graceful_shutdown called')
        job_time_out_stop.set()
        # make sure queue gets saved even if timeout thread goes haywire
        job_time_out_thread.join(3)
        if not save_queue(job_queue, job_queue_path, logger):
            logger.warning('failed to save job queue')
        if not save_queue(executing_queue, executing_queue_path,
                          logger):
            logger.warning('failed to save executing queue')
        # Now make sure timeout thread finishes
        job_time_out_thread.join()
        if configuration.logger_obj:
            configuration.logger_obj.shutdown()
    except StandardError:
        pass
    sys.exit(0)


# ## Main ###
# register ctrl+c signal handler to shutdown system cleanly

signal.signal(signal.SIGINT, clean_shutdown)

print """
Running main grid 'daemon'.

Set the MIG_CONF environment to the server configuration path
unless it is available in the default path
mig/server/MiGserver.conf
"""
configuration = get_configuration_object()
logger = configuration.logger
logger.info('Starting MiG server')

# Load queues from file dump if available

job_queue_path = configuration.mig_system_files + 'job_queue.pickle'
executing_queue_path = configuration.mig_system_files\
     + 'executing_queue.pickle'
only_new_jobs = True
job_queue = load_queue(job_queue_path, logger)
executing_queue = load_queue(executing_queue_path, logger)
if not job_queue or not executing_queue:
    logger.warning('Could not load queues from previous run')
    only_new_jobs = False
    job_queue = JobQueue(logger)
    executing_queue = JobQueue(logger)
else:
    logger.info('Loaded queues from previous run')
    job_queue.logger = logger
    executing_queue.logger = logger

# Always use an empty done queue after restart

done_queue = JobQueue(logger)

logger.info('starting scheduler ' + configuration.sched_alg)
if configuration.sched_alg == 'FirstFit':
    from firstfitscheduler import FirstFitScheduler
    scheduler = FirstFitScheduler(logger, configuration)
elif configuration.sched_alg == 'BestFit':
    from bestfitscheduler import BestFitScheduler
    scheduler = BestFitScheduler(logger, configuration)
elif configuration.sched_alg == 'FairFit':
    from fairfitscheduler import FairFitScheduler
    scheduler = FairFitScheduler(logger, configuration)
elif configuration.sched_alg == 'MaxThroughput':
    from maxthroughputscheduler import MaxThroughputScheduler
    scheduler = MaxThroughputScheduler(logger, configuration)
elif configuration.sched_alg == 'Random':
    from randomscheduler import RandomScheduler
    scheduler = RandomScheduler(logger, configuration)
elif configuration.sched_alg == 'FIFO':
    from fifoscheduler import FIFOScheduler
    scheduler = FIFOScheduler(logger, configuration)
else:
    from firstfitscheduler import FirstFitScheduler
    print 'Unknown sched_alg %s - using FirstFit scheduler'\
         % configuration.sched_alg
    scheduler = FirstFitScheduler(logger, configuration)

scheduler.attach_job_queue(job_queue)
scheduler.attach_done_queue(done_queue)

# redirect grid_stdin to sys.stdin

try:
    if not os.path.exists(configuration.grid_stdin):
        logger.info('creating grid_script input pipe %s'
                     % configuration.grid_stdin)
        try:
            os.mkfifo(configuration.grid_stdin, 0600)
        except StandardError, err:
            logger.error('Could not create missing grid_stdin fifo: '
                          + '%s exception: %s '
                          % (configuration.grid_stdin, err))
    grid_stdin = open(configuration.grid_stdin, 'r')
except StandardError:
    logger.error('failed to open grid_stdin! %s' % sys.exc_info()[0])
    sys.exit(1)

logger.info('cleaning pipe')
clean_grid_stdin(grid_stdin)

# Make sure empty job home exists

empty_home = os.path.join(configuration.user_home,
                          configuration.empty_job_name)
if not os.path.exists(empty_home):
    logger.info('creating empty job home dir %s' % empty_home)
    try:
        os.mkdir(empty_home)
    except Exception, exc:
        logger.error('failed to create empty job home dir %s: %s'
                      % (empty_home, exc))

msg = 'Checking for mRSL files with status parse or queued'
print msg
logger.info(msg)
check_mrsl_files(configuration, job_queue, executing_queue,
                 only_new_jobs, logger)

msg = 'Cleaning up after pending job requests'
print msg
remove_jobrequest_pending_files(configuration)

# start the timer function to check if cputime is exceeded

logger.info('starting time_out_jobs()')
job_time_out_stop = threading.Event()
job_time_out_thread = threading.Thread(target=time_out_jobs,
        args=(job_time_out_stop, ))
job_time_out_thread.start()

msg = 'Starting main loop'
print msg
logger.info(msg)

# main loop

loop_counter = 0
last_read_from_grid_stdin_empty = False

# print str(executing_queue.queue_length())
# print str(job_queue.queue_length())
# print str(done_queue.queue_length())

# TODO: perhaps we should run the pipe reader as main thread
#   and then spawn threads for actual handling. It should of
#   course still be thread safe.

while True:
    line = grid_stdin.readline()
    strip_line = line.strip()
    cap_line = strip_line.upper()
    linelist = strip_line.split(' ')
    if strip_line == '':
        if last_read_from_grid_stdin_empty:
            time.sleep(1)
        last_read_from_grid_stdin_empty = True

        # no reason to investigate content of line

        continue
    else:
        last_read_from_grid_stdin_empty = False

    if cap_line.find('USERJOBFILE ') == 0:

        # *********                *********
        # *********     USER JOB   *********
        # *********                *********

        print cap_line
        logger.info(cap_line)

        # add to queue

        file_userjob = configuration.mrsl_files_dir\
             + strip_line.replace('USERJOBFILE ', '') + '.mRSL'
        dict_userjob = unpickle_and_change_status(file_userjob, 'QUEUED'
                , logger)

        if not dict_userjob:
            logger.error('Could not unpickle and change status. '
                          + 'Job not enqueued!')
            continue

        # Set owner to be able to do per-user job statistics

        user_str = strip_line.replace('USERJOBFILE ', '')
        (user_id, filename) = user_str.split(os.sep)

        dict_userjob['OWNER'] = user_id
        dict_userjob['MIGRATE_COUNT'] = str(0)

        # put job in queue

        job_queue.enqueue_job(dict_userjob, job_queue.queue_length())

        user_dict = {}
        user_dict['USER_ID'] = user_id

        # Update list of users - create user if new

        scheduler.update_users(user_dict)
        user_dict = scheduler.find_user(user_dict)
        user_dict['QUEUE_HIST'].pop(0)
        user_dict['QUEUE_HIST'].append(dict_userjob)
        scheduler.update_seen(user_dict)
    elif cap_line.find('SERVERJOBFILE ') == 0:

        # *********                  *********
        # *********     SERVER JOB   *********
        # *********                  *********

        print cap_line
        logger.info(cap_line)

        # add to queue

        file_serverjob = configuration.mrsl_files_dir\
             + strip_line.replace('SERVERJOBFILE ', '') + '.mRSL'
        dict_serverjob = unpickle(file_serverjob, logger)
        if dict_serverjob == False:
            logger.error('Could not unpickle migrated job - not put into queue!'
                         )
            continue

        # put job in queue

        job_queue.enqueue_job(dict_serverjob, job_queue.queue_length())
    elif cap_line.find('JOBSCHEDULE ') == 0:

        # *********                     *********
        # *********     SCHEDULE DUMP   *********
        # *********                     *********

        print cap_line
        logger.info(cap_line)

        if len(linelist) != 2:
            logger.error('Invalid job schedule request %s' % linelist)
            continue

        # read values

        job_id = linelist[1]

        # find job in queue and dump schedule values to mRSL for job status

        job_dict = job_queue.get_job_by_id(job_id)
        if not job_dict:
            logger.info('Job is not in waiting queue - no schedule to update'
                        )
            continue

        file_serverjob = configuration.mrsl_files_dir\
             + job_dict['USER_CERT'] + os.sep + job_id + '.mRSL'
        dict_serverjob = unpickle(file_serverjob, logger)
        if dict_serverjob == False:
            logger.error('Could not unpickle job - not updating schedule!'
                         )
            continue

        # update and save schedule

        for field in ['SCHEDULE_TIMESTAMP', 'SCHEDULE_HINT']:
            if job_dict.has_key(field):
                dict_serverjob[field] = job_dict[field]
                logger.info('Job %s updated to %s' % (field,
                            dict_serverjob[field]))
        pickle(dict_serverjob, file_serverjob, logger)
    elif cap_line.find('RESOURCEREQUEST ') == 0:

        # *********                       *********
        # *********    RESOURCE REQUEST   *********
        # *********                       *********

        print cap_line
        logger.info(cap_line)
        logger.info('RESOURCEREQUEST: %d job(s) in the queue.',
                    job_queue.queue_length())

        if len(linelist) != 8:
            logger.error('Invalid resource request %s' % linelist)
            continue

        # read values

        exe = linelist[1]
        unique_resource_name = linelist[2]
        cputime = linelist[3]
        nodecount = linelist[4]
        localjobname = linelist[5]
        execution_delay = linelist[6]
        exe_pgid = linelist[7]
        last_job_failed = False

        # read resource config file

        resource_config = unpickle(configuration.resource_home
                                    + unique_resource_name + '/config',
                                   logger)
        if resource_config == False:
            logger.error('error unpickling resource config for %s'
                          % unique_resource_name)
            continue

        sandboxed = resource_config.get('SANDBOX', 0)

        # Write the PGID of EXE to PGID file

        (status, msg) = put_exe_pgid(
            configuration.resource_home,
            unique_resource_name,
            exe,
            exe_pgid,
            logger,
            sandboxed == 1,
            )
        if status:
            logger.info(msg)
        else:
            logger.error('Problem writing EXE PGID to file, job request aborted: %s'
                          % msg)

            # we cannot create and dispatch job without pgid written to file!

            continue

        # Debug queue
        # job_queue.ShowQueue(['JOB_ID', 'MAXPRICE', 'CPUTIME'])

        job_dict = None

        # mark job failed if resource requests a new job and
        # previously dispatched job is not marked done yet

        last_req_file = configuration.resource_home\
             + unique_resource_name + '/last_request.' + exe
        last_req = unpickle(last_req_file, logger)
        if last_req == False:

            # last_req could not be pickled, this is probably
            # because it is the first request from the resource

            last_req = {'EMPTY_JOB': True}

        if last_req.has_key('EMPTY_JOB'):
            logger.info('last job was an empty job')
            if last_req.has_key('JOB_ID'):

                # Dequeue empty job and cleanup
                # This is done to avoid them stacking up in the executing_queue
                # in case of a faulty resource who keeps requesting jobs

                job_dict = \
                    executing_queue.dequeue_job_by_id(last_req['JOB_ID'
                        ])
                if job_dict:
                    if not server_cleanup(
                        job_dict['SESSIONID'],
                        job_dict['IOSESSIONID'],
                        job_dict['LOCALJOBNAME'],
                        job_dict['JOB_ID'],
                        configuration,
                        logger,
                        ):
                        logger.error('could not clean up MiG server')
        elif not last_req.has_key('USER_CERT'):

            logger.error('non-empty last job has no USER_CERT! %s'
                          % last_req)
            if last_req.has_key('JOB_ID'):

                # Dequeue faulty job and cleanup
                # This is done to avoid them stacking up in the executing_queue

                job_dict = \
                    executing_queue.dequeue_job_by_id(last_req['JOB_ID'
                        ])
                if job_dict:
                    if not server_cleanup(
                        job_dict['SESSIONID'],
                        job_dict['IOSESSIONID'],
                        job_dict['LOCALJOBNAME'],
                        job_dict['JOB_ID'],
                        configuration,
                        logger,
                        ):
                        logger.error('could not clean up MiG server')
        else:

            # open the mRSL file belonging to the last request
            # and check if the status is FINISHED or CANCELED.

            last_job_ok_status_list = ['FINISHED', 'CANCELED']
            filenamelast = configuration.mrsl_files_dir\
                 + last_req['USER_CERT'] + os.sep + last_req['JOB_ID']\
                 + '.mRSL'
            job_dict = unpickle(filenamelast, logger)
            if job_dict:
                if job_dict['STATUS'] not in last_job_ok_status_list:
                    last_job_failed = True
                    exe_job = \
                        executing_queue.get_job_by_id(job_dict['JOB_ID'
                            ])
                    if exe_job:

                        # Ignore missing fields

                        (last_res, last_exe) = ('', '')
                        if exe_job.has_key('UNIQUE_RESOURCE_NAME'):
                            last_res = exe_job['UNIQUE_RESOURCE_NAME']
                        if exe_job.has_key('EXE'):
                            last_exe = exe_job['EXE']

                    if exe_job and last_res == unique_resource_name\
                         and last_exe == exe:
                        logger.info('%s:%s requested job and was NOT done with last %s'
                                     % (unique_resource_name, exe,
                                    job_dict['JOB_ID']))
                        print 'YOU ARE NOT DONE WITH %s'\
                             % job_dict['JOB_ID']

                        requeue_job(
                            executing_queue.get_job_by_id(job_dict['JOB_ID'
                                    ]),
                            'RESOURCE DIED',
                            job_queue,
                            executing_queue,
                            configuration,
                            logger,
                            )
                    else:
                        logger.info('%s:%s requested job but last %s was rescheduled'
                                     % (unique_resource_name, exe,
                                    job_dict['JOB_ID']))
                        print 'YOUR LAST JOB %s WAS RESCHEDULED'\
                             % job_dict['JOB_ID']
                else:
                    logger.info('%s requested job and previous was done'
                                 % unique_resource_name)
                    print 'OK, last job %s was done' % job_dict['JOB_ID'
                            ]

        # Now update resource config fields with requested attributes

        resource_config['CPUTIME'] = cputime

        # overwrite execution_delay attribute

        resource_config['EXECUTION_DELAY'] = execution_delay

        # overwrite number of available nodes (a pbs resource might not
        # want a job for all nodes)

        resource_config['NODECOUNT'] = nodecount
        resource_config['RESOURCE_ID'] = '%s_%s'\
             % (unique_resource_name, exe)

        # specify vgrid

        (status, exe_conf) = get_resource_exe(resource_config, exe,
                logger)
        if not status:
            logger.error('could not get exe configuration for resource!'
                         )
            continue

        last_request_dict = {'RESOURCE_CONFIG': resource_config,
                             'CREATED_TIME': datetime.datetime.now(),
                             'STATUS': ''}

        # find the vgrid that should receive the job request

        last_vgrid = 0
        if not exe_conf.has_key('vgrid'):

            # all resources should have vgrid section!

            continue

        if exe_conf['vgrid'] == '':

            # fall back to default vgrid

            exe_conf['vgrid'] = [default_vgrid]

        exe_conf_vgrid = exe_conf['vgrid']
        if type(exe_conf_vgrid) == type([]):

            # list

            if last_req.has_key('LAST_VGRID'):

                # index of last vgrid found

                last_vgrid_index = last_req['LAST_VGRID']

                # make sure the index is within bounds (some vgrids
                # might have been removed from conf since last run)

                res_vgrid_count = len(exe_conf_vgrid)
                if last_vgrid_index + 1 > res_vgrid_count - 1:

                    # out of bounds, use index 0

                    pass
                else:

                    # within bounds

                    last_vgrid = last_vgrid_index + 1

        # The scheduler checks the vgrids in the order as they appear in
        # the list, so to be fair the order of the vgrids in the list
        # should be cycled according to the last_request

        vgrids_in_prioritized_order = []

        list_indexes = range(last_vgrid, len(exe_conf_vgrid))
        list_indexes = list_indexes + range(0, last_vgrid)

        for index in list_indexes:

            # replace "" with default_vgrid

            add_vgrid = exe_conf['vgrid'][index]
            if add_vgrid == '':
                add_vgrid = default_vgrid
            vgrids_in_prioritized_order.append(add_vgrid)
        logger.info('vgrids in prioritized order: %s (last %s)'
                     % (vgrids_in_prioritized_order, last_vgrid))

        # set found values

        resource_config['VGRID'] = vgrids_in_prioritized_order
        resource_config['LAST_VGRID'] = last_vgrid
        last_request_dict['LAST_VGRID'] = last_vgrid

        # Update list of resources

        scheduler.update_resources(resource_config)
        scheduler.update_seen(resource_config)

        if job_queue.queue_length() == 0 or last_job_failed:

            # No jobs: Create 'empty' job script and double sleep time if
            # repeated empty job

            if not last_req.has_key('EMPTY_JOB'):
                sleep_factor = 1.0
            else:
                sleep_factor = 2.0
            print 'N'
            empty_job = jobscriptgenerator.create_empty_job(
                unique_resource_name,
                exe,
                cputime,
                sleep_factor,
                localjobname,
                execution_delay,
                configuration,
                logger,
                )
            (sessionid, iosessionid) = \
                jobscriptgenerator.create_job_script(
                unique_resource_name,
                exe,
                empty_job,
                resource_config,
                localjobname,
                configuration,
                logger,
                )
            if sessionid and iosessionid:
                last_request_dict['JOB_ID'] = empty_job['JOB_ID']
                last_request_dict['STATUS'] = 'No jobs in queue'
                if last_job_failed:
                    last_request_dict['STATUS'] = \
                        'Last job failed - forced empty job'
                last_request_dict['EXECUTING_TIMESTAMP'] = time.gmtime()
                last_request_dict['EXECUTION_DELAY'] = \
                    empty_job['EXECUTION_DELAY']
                last_request_dict['UNIQUE_RESOURCE_NAME'] = \
                    unique_resource_name
                last_request_dict['EXE'] = exe
                last_request_dict['RESOURCE_CONFIG'] = resource_config
                last_request_dict['LOCALJOBNAME'] = localjobname
                last_request_dict['SESSIONID'] = sessionid
                last_request_dict['IOSESSIONID'] = iosessionid
                last_request_dict['CPUTIME'] = empty_job['CPUTIME']
                last_request_dict['EMPTY_JOB'] = True

                executing_queue.enqueue_job(last_request_dict,
                        executing_queue.queue_length())
                logger.info('empty job script created')
            else:
                msg = 'Failed to create job script: %s' % sessionid
                print msg
                logger.error(msg)
                continue
        else:

            # there are jobs in the queue

            # Expire outdated jobs - expire_jobs removes them from queue
            # and returns them in a list: handle the file update here.

            expired_jobs = scheduler.expire_jobs()
            for expired in expired_jobs:

                # tell the user about the expired job - we do not wait for notification
                # to finish but hope for the best since this script is long running.
                # the thread only writes a message to the notify pipe so it finishes
                # immediately if the notify daemon is listening and blocks indefinitely
                # otherwise.

                notify_user_thread(
                    expired,
                    configuration.myfiles_py_location,
                    'EXPIRED',
                    logger,
                    False,
                    configuration,
                    )
                expired_file = configuration.mrsl_files_dir\
                     + expired['USER_CERT'] + os.sep + expired['JOB_ID']\
                     + '.mRSL'

                if not unpickle_and_change_status(expired_file,
                        'EXPIRED', logger):
                    logger.error('Could not unpickle and change status. '

                                  + 'Job could not be officially expired!'
                                 )
                    continue

            # Remove references to expired jobs

            expired_jobs = []

            # Schedule and create appropriate job script
            # loop until a non-cancelled job is scheduled (fixes small
            # race condition if a job has not been dequeued after the
            # status in the mRSL file has been changed to CANCELED)

            while True:
                job_dict = scheduler.schedule(resource_config)
                if not job_dict:
                    break

                mrsl_filename = configuration.mrsl_files_dir\
                     + job_dict['USER_CERT'] + '/' + job_dict['JOB_ID']\
                     + '.mRSL'
                dummy_dict = unpickle(mrsl_filename, logger)

                # The job status should be "QUEUED" at this point

                if dummy_dict == False:
                    logger.error('error unpickling mrsl in %s' % \
                         mrsl_filename)
                    continue

                if dummy_dict['STATUS'] == 'QUEUED':
                    break

            if not job_dict:

                # no jobs in the queue fits the resource!

                print 'X'
                logger.info('No jobs in the queue can be executed by '
                             + 'resource, queue length: %s'
                             % job_queue.queue_length())

                # Create 'empty' job script and double sleep time if
                # repeated empty job

                if not last_req.has_key('EMPTY_JOB'):
                    sleep_factor = 1.0
                else:
                    sleep_factor = 2.0
                empty_job = jobscriptgenerator.create_empty_job(
                    unique_resource_name,
                    exe,
                    cputime,
                    sleep_factor,
                    localjobname,
                    execution_delay,
                    configuration,
                    logger,
                    )
                (sessionid, iosessionid) = \
                    jobscriptgenerator.create_job_script(
                    unique_resource_name,
                    exe,
                    empty_job,
                    resource_config,
                    localjobname,
                    configuration,
                    logger,
                    )
                if sessionid and iosessionid:
                    last_request_dict['JOB_ID'] = empty_job['JOB_ID']
                    last_request_dict['STATUS'] = \
                        'No jobs in queue can be executed by resource'
                    last_request_dict['EXECUTING_TIMESTAMP'] = \
                        time.gmtime()
                    last_request_dict['EXECUTION_DELAY'] = \
                        execution_delay
                    last_request_dict['UNIQUE_RESOURCE_NAME'] = \
                        unique_resource_name
                    last_request_dict['EXE'] = exe
                    last_request_dict['RESOURCE_CONFIG'] = \
                        resource_config
                    last_request_dict['LOCALJOBNAME'] = localjobname
                    last_request_dict['SESSIONID'] = sessionid
                    last_request_dict['IOSESSIONID'] = iosessionid
                    last_request_dict['CPUTIME'] = empty_job['CPUTIME']
                    last_request_dict['EMPTY_JOB'] = True

                    executing_queue.enqueue_job(last_request_dict,
                            executing_queue.queue_length())
                    logger.info('empty job script created')
            else:

                # a job has been scheduled to be executed on this
                # resource: change status in the mRSL file

                mrsl_filename = configuration.mrsl_files_dir\
                     + job_dict['USER_CERT'] + '/' + job_dict['JOB_ID']\
                     + '.mRSL'
                mrsl_dict = unpickle(mrsl_filename, logger)
                if mrsl_dict:
                    (sessionid, iosessionid) = \
                        jobscriptgenerator.create_job_script(
                        unique_resource_name,
                        exe,
                        job_dict,
                        resource_config,
                        localjobname,
                        configuration,
                        logger,
                        )
                    if sessionid and iosessionid:

                        # Write executing details to mRSL file

                        mrsl_dict['STATUS'] = 'EXECUTING'
                        mrsl_dict['EXECUTING_TIMESTAMP'] = time.gmtime()
                        mrsl_dict['EXECUTION_DELAY'] = execution_delay
                        mrsl_dict['UNIQUE_RESOURCE_NAME'] = \
                            unique_resource_name
                        mrsl_dict['EXE'] = exe
                        mrsl_dict['RESOURCE_CONFIG'] = resource_config
                        mrsl_dict['LOCALJOBNAME'] = localjobname
                        mrsl_dict['SESSIONID'] = sessionid
                        mrsl_dict['IOSESSIONID'] = iosessionid

                        # pickle the new version

                        pickle(mrsl_dict, mrsl_filename, logger)

                        last_request_dict['STATUS'] = 'Job assigned'
                        last_request_dict['CPUTIME'] = \
                            job_dict['CPUTIME']
                        last_request_dict['EXECUTION_DELAY'] = \
                            execution_delay
                        last_request_dict['NODECOUNT'] = \
                            job_dict['NODECOUNT']

                        # job id and user_cert is used to check if the current
                        # job is done when a resource requests a new job

                        last_request_dict['JOB_ID'] = job_dict['JOB_ID']
                        last_request_dict['USER_CERT'] = \
                            job_dict['USER_CERT']

                        # Save actual VGrid for fair VGrid cycling

                        try:
                            vgrid_index = \
                                vgrids_in_prioritized_order.index(job_dict['RESOURCE_VGRID'
                                    ])
                        except StandardError:

                            # fall back to simple increment

                            vgrid_index = last_vgrid
                        last_request_dict['LAST_VGRID'] = vgrid_index

                        print 'Job assigned ' + job_dict['JOB_ID']
                        logger.info('Job %s assigned to %s execution unit %s'
                                     % (job_dict['JOB_ID'],
                                    unique_resource_name, exe))

                        # put job in executing queue

                        executing_queue.enqueue_job(mrsl_dict,
                                executing_queue.queue_length())

                        print 'executing_queue length %d'\
                             % executing_queue.queue_length()
                    else:

                        # put job in back in job queue

                        job_queue.enqueue_job(mrsl_dict,
                                job_queue.queue_length())
                        logger.error('error creating new job script')
                else:
                    logger.error('error unpickling mRSL: %s'
                                  % mrsl_filename)

        pickle(last_request_dict, last_req_file, logger)

        # Save last_request_dict to vgrid_home/vgrid_name to make
        # seperate vgrid monitors possible

        # contains names on vgrids where last_request_dict should
        # be saved unmodified

        original_last_request_dict_vgrids = []

        # contains names on vgrids where last_request_dict should
        # be overwritten with a "Executing job for another vgrid"
        # version

        executing_in_other_vgrids = []

        # if empty_job:
            # empty job, make sure this job request is seen on monitors
            # for all vgrids this resource is in
        #    original_last_request_dict_vgrids = vgrids_in_prioritized_order

        # TODO: must detect if it is a real or empty job.
        # problem: after a job has been executed in a
        # vgrid and the resource gets an empty job the monitor
        # says "executing in other vgrid" which of course should
        # be no jobs in grid queue can be executed by resource.

        if job_dict:

            # real job scheduled!

            if job_dict.has_key('VGRID'):
                original_last_request_dict_vgrids += job_dict['VGRID']
            else:

                # no vgrid specified, this means default vgrid.

                original_last_request_dict_vgrids.append([default_vgrid])

            # overwrite last_request_dict for vgrids that
            # the resource is in but not executing the job

            logger.info('job: %s' % job_dict)
            for res_vgrid in vgrids_in_prioritized_order:
                if res_vgrid not in original_last_request_dict_vgrids:
                    executing_in_other_vgrids.append(res_vgrid)
        else:

            # empty job, make sure this job request is seen on monitors
            # for all vgrids this resource is in

            original_last_request_dict_vgrids = \
                vgrids_in_prioritized_order

        # save monitor_last_request files
        # for vgrid_monitor in original_last_request_dict_vgrids:
        # loop all vgrids where this resource is taking jobs

        for vgrid_name in vgrids_in_prioritized_order:
            logger.info("vgrid_name: '%s' org '%s' exe '%s'"
                         % (vgrid_name,
                        original_last_request_dict_vgrids,
                        executing_in_other_vgrids))

            monitor_last_request_file = configuration.vgrid_home\
                 + os.sep + vgrid_name + os.sep\
                 + 'monitor_last_request_' + unique_resource_name + '_'\
                 + exe

            if vgrid_name in original_last_request_dict_vgrids:
                pickle(last_request_dict, monitor_last_request_file,
                       logger)
                logger.info('vgrid_name: %s status: %s' % (vgrid_name,
                            last_request_dict['STATUS']))
            elif vgrid_name in executing_in_other_vgrids:

                # create modified last_request_dict and save

                new_last_request_dict = copy.deepcopy(last_request_dict)
                new_last_request_dict['STATUS'] = \
                    'Executing job for another vgrid'
                logger.info('vgrid_name: %s status: %s' % (vgrid_name,
                            new_last_request_dict['STATUS']))
                pickle(new_last_request_dict,
                       monitor_last_request_file, logger)
            else:

                # we should never enter this else, vgrid_name must be in
                # original_last_request_dict_vgrids or
                # executing_in_other_vgrids

                logger.error('Entered else condition that never should be'

                              + ' entered during creation of last_request_dict in '

                              + "grid_script! vgrid_name: '%s' not in '%s' or '%s'"
                              % (vgrid_name,
                             original_last_request_dict_vgrids,
                             executing_in_other_vgrids))

        # delete requestnewjob lock

        lock_file = configuration.resource_home + '/'\
             + unique_resource_name + '/jobrequest_pending.' + exe
        try:
            os.remove(lock_file)
        except OSError, ose:
            logger.error('Error removing %s: %s' % (lock_file, ose))

        # Experimental pricing code
        # TODO: update price *after* publishing status so that price fits delay?

        if configuration.enable_server_dist:
            scheduler.update_price(resource_config)
    elif cap_line.find('RESOURCEFINISHEDJOB ') == 0:

        # *********                       *********
        # *********    RESOURCE FINISHED  *********
        # *********                       *********
        # format: RESOURCEFINISHEDJOB RESOURCE_ID/LOCALJOBNAME

        print cap_line
        logger.info(cap_line)
        logger.info('RESOURCEFINISHEDJOB: %d job(s) in the queue.',
                    job_queue.queue_length())

        if len(linelist) != 5:
            logger.error('Invalid resourcefinishedjob request')
            continue

        # read values

        res_name = linelist[1]
        exe_name = linelist[2]
        sessionid = linelist[3]
        job_id = linelist[4]

        msg = 'RESOURCEFINISHEDJOB: %s:%s finished job %s id %s'\
             % (res_name, exe_name, sessionid, job_id)
        job_dict = executing_queue.get_job_by_id(job_id)

        if not job_dict:
            msg += \
                ', but job is not in executing queue, ignoring result.'
        elif job_dict['UNIQUE_RESOURCE_NAME'] != res_name\
             or job_dict['EXE'] != exe_name:
            msg += \
                ', but job is beeing executed by %s:%s, ignoring result.'\
                 % (job_dict['UNIQUE_RESOURCE_NAME'], job_dict['EXE'])
        else:

            # Clean up the server for files associated with the finished job

            if not server_cleanup(
                job_dict['SESSIONID'],
                job_dict['IOSESSIONID'],
                job_dict['LOCALJOBNAME'],
                job_id,
                configuration,
                logger,
                ):
                logger.error('could not clean up MiG server')

            if configuration.enable_server_dist\
                 and not job_dict.has_key('EMPTY_JOB'):

                # TODO: we should probably support resources migrating and
                # handing back job as first contact with new server
                # Still not sure if we need finished handling at all, though...

                scheduler.finished_job(res_name, job_dict)

            executing_queue.dequeue_job_by_id(job_id)
            msg += '%s removed from executing queue.' % job_id

        # print msg

        logger.info(msg)
    elif cap_line.find('RESTARTEXEFAILED') == 0:

        # *********                       *********
        # *********   RESTART EXE FAILED  *********
        # *********                       *********

        print cap_line
        logger.info(cap_line)
        logger.info('Before restart exe failed: %d job(s) in the executing queue.'
                    , executing_queue.queue_length())

        if len(linelist) != 4:
            logger.error('Invalid restart exe failed request')
            continue

        # read values

        res_name = linelist[1]
        exe_name = linelist[2]
        job_id = linelist[3]

        logger.info('Restart exe failed: adding retry job for %s %s'
                     % (res_name, exe_name))
        retry_job = jobscriptgenerator.create_restart_job(
            res_name,
            exe_name,
            300,
            1,
            'RESTART-EXE-FAILED',
            0,
            configuration,
            logger,
            )
        executing_queue.enqueue_job(retry_job,
                                    executing_queue.queue_length())
        logger.info('After restart exe failed: %d job(s) in the executing queue.'
                    , executing_queue.queue_length())
    elif cap_line.find('CANCELJOB') == 0:

        # *********                       *********
        # *********      CANCEL JOB       *********
        # *********                       *********

        print cap_line
        logger.info(cap_line)
        logger.info('Cancel job: %d job(s) in the queue.',
                    job_queue.queue_length())

        if len(linelist) != 5:
            logger.error('Invalid cancel job request')
            continue

        # read values

        job_id = linelist[1]
        original_status = linelist[2]
        unique_resource_name = linelist[3]
        exe = linelist[4]

        # read resource config file

        resource_config = unpickle(configuration.resource_home
                                    + unique_resource_name + '/config',
                                   logger)

        just_dequeue_status_list = ['QUEUED', 'RETRY']
        kill_executing_status_list = ['EXECUTING']

        if original_status in just_dequeue_status_list:

            # dequeue

            job_dict = job_queue.dequeue_job_by_id(job_id)
        elif original_status in kill_executing_status_list:

            # Retrieve job_dict

            num_executing_jobs_before = executing_queue.queue_length()
            job_dict = executing_queue.dequeue_job_by_id(job_id)
            num_executing_jobs_after = executing_queue.queue_length()
            logger.info('Number of jobs in executing queue. '
                         + 'Before cancel: %s. After cancel: %s'
                         % (num_executing_jobs_before,
                        num_executing_jobs_after))

            if not job_dict:

                # We are seeing a race in the handling of executing jobs - do nothing
                # Job timeout must have just killed the job we are trying to cancel

                logger.info('Cancel job: Could not get job_dict for executing job'
                            )
                continue

            if not server_cleanup(
                job_dict['SESSIONID'],
                job_dict['IOSESSIONID'],
                job_dict['LOCALJOBNAME'],
                job_dict['JOB_ID'],
                configuration,
                logger,
                ):
                logger.error('could not clean up MiG server')

            if resource_config.get('SANDBOX', 0) == 0:
                logger.info('Killing running job with atomic_resource_exe_restart'
                            )
                (status, msg) = \
                    atomic_resource_exe_restart(unique_resource_name,
                        exe, configuration, logger)

                if status:
                    logger.info('atomic_resource_exe_restart ok: resource %s exe %s'
                                 % (unique_resource_name, exe))
                else:
                    logger.error('atomic_resource_exe_restart FAILED: reason: %s resource %s exe %s'
                                  % (msg, unique_resource_name, exe))

                    # kill_job_by_exe_restart(unique_resource_name, exe, configuration, logger)
                    # Make sure we do not loose exes even if restart fails

                    retry_message = 'RESTARTEXEFAILED %s %s %s\n'\
                         % (unique_resource_name, exe, job_id)
                    send_message_to_grid_script(retry_message, logger,
                            configuration)
    elif cap_line.find('JOBTIMEOUT') == 0:

        unique_resource_name = linelist[1]
        exe_name = linelist[2]
        jobid = linelist[3]

        msg = 'JOBTIMEOUT: %s timed out.' % jobid
        print msg
        logger.info(msg)

        # read resource config file

        resource_config = unpickle(configuration.resource_home
                                    + unique_resource_name + '/config',
                                   logger)

        # Retrieve job_dict

        job_dict = executing_queue.get_job_by_id(jobid)

        # Execution information is removed from job_dict in
        # requeue_job - save here

        exe = ''
        if job_dict:
            exe = job_dict['EXE']

        # Check if job has already been rescheduled due to resource
        # failure. Important to match both unique resource and exe
        # name to avoid problems when job is rescheduled to another
        # exe on same resource.

        # IMPORTANT: both empty and real jobs may require exe
        # restart on time out. If frontend script can't deliver
        # status file within time frame (network outage etc) the
        # session id will be invalidated resulting in rejection
        # and no automatic restart of exe.

        if job_dict and unique_resource_name\
             == job_dict['UNIQUE_RESOURCE_NAME'] and exe_name == exe:
            if job_dict.has_key('EMPTY_JOB'):

                # Empty job timed out, cleanup server and
                # remove from Executing queue

                if not server_cleanup(
                    job_dict['SESSIONID'],
                    job_dict['IOSESSIONID'],
                    job_dict['LOCALJOBNAME'],
                    job_dict['JOB_ID'],
                    configuration,
                    logger,
                    ):
                    logger.error('could not clean up MiG server')

                executing_queue.dequeue_job_by_id(job_dict['JOB_ID'])
            else:

                # Real job, requeue job

                requeue_job(
                    job_dict,
                    'JOB TIMEOUT',
                    job_queue,
                    executing_queue,
                    configuration,
                    logger,
                    )

            # Restart non-sandbox resources for all timed out jobs

            if resource_config.get('SANDBOX', 0) == 0:

                # TODO: atomic_resource_exe_restart is not always effective
                # The imada resources have been seen to hang in wait for input files loop
                # across an atomic_resource_exe_restart run (server PGID was 'starting').

                (status, msg) = \
                    atomic_resource_exe_restart(unique_resource_name,
                        exe, configuration, logger)
                if status:
                    logger.info('atomic_resource_exe_restart ok: resource %s exe %s'
                                 % (unique_resource_name, exe))
                else:
                    logger.error('atomic_resource_exe_restart FAILED: reason: %s resource %s exe %s'
                                  % (msg, unique_resource_name, exe))

                    # Make sure we do not loose exes even if restart fails

                    retry_message = 'RESTARTEXEFAILED %s %s %s\n'\
                         % (unique_resource_name, exe_name,
                            job_dict['JOB_ID'])
                    send_message_to_grid_script(retry_message, logger,
                            configuration)
                    logger.info('requested restart exe retry attempt')
    elif cap_line.find('JOBQUEUEINFO') == 0:

        logger.info('--- DISPLAYING JOB QUEUE INFORMATION ---')
        details = linelist[1:]
        if not details:
            details.append('JOB_ID')
        job_queue.show_queue(details)
    elif cap_line.find('EXECUTINGQUEUEINFO') == 0:
        logger.info('--- DISPLAYING EXECUTING QUEUE INFORMATION ---')
        details = linelist[1:]
        if not details:
            details.append('JOB_ID')
        executing_queue.show_queue(details)
    elif cap_line.find('DONEQUEUEINFO') == 0:
        logger.info('--- DISPLAYING DONE QUEUE INFORMATION ---')
        details = linelist[1:]
        if not details:
            details.append('JOB_ID')
        done_queue.show_queue(details)
    elif cap_line.find('STARTTIMEOUTTHREAD') == 0:
        logger.info('--- STARTING TIME OUT THREAD ---')
        job_time_out_stop.clear()
        job_time_out_thread = threading.Thread(target=time_out_jobs,
                args=(job_time_out_stop, ))
        job_time_out_thread.start()
    elif cap_line.find('CHECKTIMEOUTTHREAD') == 0:
        logger.info('--- CHECKING TIME OUT THREAD ---')
        logger.info('--- TIME OUT THREAD IS ALIVE: %s ---'
                     % job_time_out_thread.isAlive())
    elif cap_line.find('RELOADCONFIG') == 0:
        logger.info('--- RELOADING CONFIGURATION ---')
        configuration.reload_config(config_file, True)
    elif cap_line.find('SHUTDOWN') == 0:
        logger.info('--- SAFE SHUTDOWN INITIATED ---')
        print '--- SAFE SHUTDOWN INITIATED ---'
        graceful_shutdown()
    else:
        print 'not understood: %s' % cap_line
        logger.error('not understood: %s' % cap_line)
        time.sleep(1)

    # Experimental distributed server code

    if configuration.enable_server_dist:
        servercomm.exchange_status(configuration, scheduler,
                                   loop_counter)

    # TMP: Auto restart time out thread until we find the death cause

    if not job_time_out_thread.isAlive():
        logger.warning('--- TIME OUT THREAD DIED: %s %s %s---'
                        % (job_time_out_thread,
                       job_time_out_thread.isAlive(),
                       job_time_out_stop.isSet()))
        logger.info('ressurect time out thread with executing queue:')
        logger.info('%s' % executing_queue.show_queue(['ALL']))
        job_time_out_stop.clear()
        job_time_out_thread = threading.Thread(target=time_out_jobs,
                args=(job_time_out_stop, ))
        job_time_out_thread.start()

    sys.stdout.flush()
    loop_counter += 1
    logger.info('loop ended')

