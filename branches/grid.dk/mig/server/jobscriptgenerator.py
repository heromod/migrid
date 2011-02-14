#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# jobscriptgenerator - [insert a few words of module description on this line]
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

"""Job script generator"""

import os
import time
from binascii import hexlify
from copy import deepcopy

import genjobscriptpython
import genjobscriptsh
import genjobscriptjava
from shared.fileio import write_file, pickle, make_symlink
from shared.mrslparser import expand_variables
from shared.ssh import copy_file_to_resource
from shared.useradm import client_id_dir

from shared.refunctions import zero_install_replace

try:
    import shared.mrsltoxrsl as mrsltoxrsl
    import shared.arcwrapper as arc
except Exception, exc:
    # Ignore errors and let it crash if ARC is enabled without the lib
    pass


def create_empty_job(
    unique_resource_name,
    exe,
    request_cputime,
    sleep_factor,
    localjobname,
    execution_delay,
    configuration,
    logger,
    ):

    job_dict = {'': ''}
    helper_dict_filename = os.path.join(configuration.resource_home,
                                        unique_resource_name,
                                        'empty_job_helper_dict.%s' % exe)

    max_cputime = int(request_cputime)
    scaled_cputime = int(float(configuration.cputime_for_empty_jobs)
                          * sleep_factor)
    if scaled_cputime > max_cputime:
        cputime = max_cputime
        sleep_time = int(0.8 * cputime)
    else:
        cputime = scaled_cputime
        sleep_time = \
            int(float(configuration.sleep_period_for_empty_jobs)
                 * sleep_factor)

    logger.info('request_cputime: %d, sleep_factor: %.1f, cputime: %d, sleep time: %d'
                , max_cputime, sleep_factor, cputime, sleep_time)
    job_id = configuration.empty_job_name + '.' + unique_resource_name\
         + '.' + exe + '.' + localjobname

    job_dict['JOB_ID'] = job_id

    # sessionid = configuration.empty_job_name

    sleep_cmd = 'sleep ' + str(sleep_time)
    job_dict['EXECUTE'] = [sleep_cmd]
    job_dict['INPUTFILES'] = []
    job_dict['OUTPUTFILES'] = ''
    job_dict['ARGUMENTS'] = ''
    job_dict['EXECUTABLES'] = ''
    job_dict['CPUTIME'] = str(cputime)
    job_dict['EXECUTION_DELAY'] = str(execution_delay)
    job_dict['ENVIRONMENT'] = []
    job_dict['RUNTIMEENVIRONMENT'] = []
    job_dict['MAXPRICE'] = '0'
    job_dict['JOBNAME'] = 'empty job'
    client_id = configuration.empty_job_name
    job_dict['USER_CERT'] = client_id

    # create mRSL file only containing the unique_resource_name.
    # This is used when the .status file from the empty job is
    # uploaded, to find the unique name of the resource to be able
    # to start the exe again if continuous is True
    # if not os.path.isfile(helper_dict_filename):

    helper_dict = {}
    helper_dict['JOB_ID'] = job_id
    helper_dict['UNIQUE_RESOURCE_NAME'] = unique_resource_name
    helper_dict['EXE'] = exe
    helper_dict['IS_EMPTY_JOB_HELPER_DICT'] = True
    helper_dict['LOCALJOBNAME'] = localjobname

    pickle(helper_dict, helper_dict_filename, logger)

    return job_dict


def create_restart_job(
    unique_resource_name,
    exe,
    request_cputime,
    sleep_factor,
    localjobname,
    execution_delay,
    configuration,
    logger,
    ):
    """Wrapper to create a dummy job for forcing repeated restart of dead exes"""

    empty_job = create_empty_job(
        unique_resource_name,
        exe,
        request_cputime,
        sleep_factor,
        localjobname,
        execution_delay,
        configuration,
        logger,
        )
    empty_job['UNIQUE_RESOURCE_NAME'] = unique_resource_name
    empty_job['EXE'] = exe
    empty_job['LOCALJOBNAME'] = localjobname
    empty_job['STATUS'] = 'Restart exe failed dummy'
    empty_job['EXECUTING_TIMESTAMP'] = time.gmtime()
    empty_job['RESOURCE_CONFIG'] = None
    empty_job['SESSIONID'] = 'RESTARTFAILEDDUMMYID'
    empty_job['IOSESSIONID'] = 'RESTARTFAILEDDUMMYID'
    empty_job['EMPTY_JOB'] = True
    return empty_job


# Returns sessionid if successfull, None if NON-successfull


def create_job_script(
    unique_resource_name,
    exe,
    job,
    resource_config,
    localjobname,
    configuration,
    logger,
    ):

    sessionid = hexlify(open('/dev/urandom').read(32))
    iosessionid = hexlify(open('/dev/urandom').read(32))
    helper_dict_filename = os.path.join(configuration.resource_home,
                                        unique_resource_name,
                                        'empty_job_helper_dict.%s' % exe)

    logger.debug('create Job script, session ID: %s' % sessionid)
    logger.debug('Job is this: %s' % job)

    # Deep copy job for local changes
    job_dict = deepcopy(job)

    job_dict['MIGSESSIONID'] = sessionid
    job_dict['MIGIOSESSIONID'] = iosessionid
    if not job_dict.has_key('MAXPRICE'):
        job_dict['MAXPRICE'] = '0'

    # replace requested REs by env. variables if zero-install configured
    if configuration.zero_install_re:
        (zi_env, real_res) = zero_install_replace(job['RUNTIMEENVIRONMENT'],
                                         resource_config['RUNTIMEENVIRONMENT'],
                                         configuration)
        job_dict['RUNTIMEENVIRONMENT'] = real_res
        job_dict['ENVIRONMENT'].extend(zi_env)

    # Finally expand reserved job variables like +JOBID+ and +JOBNAME+
    job_dict = expand_variables(job_dict)
    # ... no more changes to job_dict from here on
    client_id = str(job_dict['USER_CERT'])
    client_dir = client_id_dir(client_id)

    logger.debug('Modified Job dict: %s' % job_dict)

    # if not job:

    if client_id == configuration.empty_job_name:

        # create link to empty job

        linkdest_empty_job = helper_dict_filename
        linkloc_empty_job = configuration.sessid_to_mrsl_link_home\
             + sessionid + '.mRSL'
        make_symlink(linkdest_empty_job, linkloc_empty_job, logger)
    else:

        # link sessionid to mrsl file

        linkdest1 = configuration.mrsl_files_dir + client_dir + '/'\
             + str(job_dict['JOB_ID']) + '.mRSL'
        linkloc1 = configuration.sessid_to_mrsl_link_home + sessionid\
             + '.mRSL'
        make_symlink(linkdest1, linkloc1, logger)

    # link sessionid to job owners home directory

    linkdest2 = configuration.user_home + client_dir
    linkloc2 = configuration.webserver_home + sessionid
    make_symlink(linkdest2, linkloc2, logger)

    # link iosessionid to job owners home directory

    linkdest3 = configuration.user_home + client_dir
    linkloc3 = configuration.webserver_home + iosessionid
    make_symlink(linkdest3, linkloc3, logger)

    # link sessionid to .job file

    linkdest4 = configuration.mig_system_files + str(job_dict['JOB_ID'])\
         + '.job'
    linkloc4 = configuration.webserver_home + sessionid + '.job'
    make_symlink(linkdest4, linkloc4, logger)

    # link sessionid to .getupdatefiles file

    linkdest5 = configuration.mig_system_files + str(job_dict['JOB_ID'])\
         + '.getupdatefiles'
    linkloc5 = configuration.webserver_home + sessionid\
         + '.getupdatefiles'
    make_symlink(linkdest5, linkloc5, logger)

    # link sessionid to .sendoutputfiles file

    linkdest4 = configuration.mig_system_files + str(job_dict['JOB_ID'])\
         + '.sendoutputfiles'
    linkloc4 = configuration.webserver_home + sessionid\
         + '.sendoutputfiles'
    make_symlink(linkdest4, linkloc4, logger)

    # link sessionid to .sendupdatefiles file

    linkdest5 = configuration.mig_system_files + str(job_dict['JOB_ID'])\
         + '.sendupdatefiles'
    linkloc5 = configuration.webserver_home + sessionid\
         + '.sendupdatefiles'
    make_symlink(linkdest5, linkloc5, logger)

    path_without_extension = os.path.join(configuration.resource_home,
                                          unique_resource_name, localjobname)
    gen_res = gen_job_script(
        job_dict,
        resource_config,
        configuration,
        localjobname,
        path_without_extension,
        client_dir,
        exe,
        logger,
        )
    if not gen_res:
        msg = \
            'job scripts were not generated. Perhaps you have specified an invalid SCRIPTLANGUAGE ? '
        print msg
        logger.error(msg)
        return (msg, None)

    inputfiles_path = path_without_extension + '.getinputfiles'

    # hack to ensure that a resource has a sandbox keyword

    if resource_config.get('SANDBOX', False):

        # Move file to webserver_home for download as we can't push it to sandboxes

        try:

            # RA TODO: change download filename to something that
            # includes sessionid

            webserver_path = os.path.join(configuration.webserver_home,
                    localjobname + '.getinputfiles')
            os.rename(inputfiles_path, webserver_path)

            # ########## ATTENTION HACK TO MAKE JVM SANDBOXES WORK ########################################
            # This should be changed to use the (to be developed) RE pre/post processing framework       #
            # For now the user must have a jvm dir in his home dir where the classfiles is located       #
            # this should be changed so that the execution homepath can be specified in the mRSL jobfile #
            #                                                                                            #
            # Martin Rehr 08/09/06                                                                       #

            # If this is a oneclick job link the users jvm dir to
            # webserver_home/sandboxkey.oneclick
            # This is done because the client applet uses the
            # codebase from which it is originaly loaded
            # Therefore the codebase must be dynamicaly changed
            # for every job

            if resource_config.has_key('PLATFORM')\
                 and resource_config['PLATFORM'] == 'ONE-CLICK':

                # A two step link is made.
                # First sandboxkey.oneclick is made to point to
                # sessiondid.jvm
                # Second sessionid.jvm is set to point to
                # USER_HOME/jvm
                # This is done for security and easy cleanup,
                # sessionid.jvm is cleaned up
                # by the server upon job finish/timeout and
                # thereby leaving no open entryes to the users
                # jvm dir.

                linkintermediate = configuration.webserver_home\
                     + sessionid + '.jvm'

                if client_dir == configuration.empty_job_name:
                    linkdest = \
                        os.path.abspath(configuration.javabin_home)
                else:
                    linkdest = configuration.user_home + client_dir\
                         + os.sep + 'jvm'

                # Make link sessionid.jvm -> USER_HOME/jvm

                make_symlink(linkdest, linkintermediate, logger)

                linkloc = configuration.webserver_home\
                     + resource_config['SANDBOXKEY'] + '.oneclick'

                # Remove previous symlink
                # This must be done in a try/catch as the symlink,
                # may be a dead link and 'if os.path.exists(linkloc):'
                # will then return false, even though the link exists.

                try:
                    os.remove(linkloc)
                except:
                    pass

                # Make link sandboxkey.oneclick -> sessionid.jvm

                make_symlink(linkintermediate, linkloc, logger)
        except Exception, err:

                # ######### End JVM SANDBOX HACK ###########

            msg = "File '%s' was not copied to the webserver home."\
                 % inputfiles_path
            print '\nERROR: ' + str(err)
            logger.error(msg)
            return (msg, None)

        return (sessionid, iosessionid)

    # Copy file to the resource

    if not copy_file_to_resource(inputfiles_path,
                                 os.path.basename(inputfiles_path),
                                 resource_config, logger):
        logger.error('File was not copied to the resource: '
                      + inputfiles_path)
    else:

        # file was sent, delete it

        try:
            os.remove(inputfiles_path)
        except:
            logger.error('could not remove ' + inputfiles_path)
    return (sessionid, iosessionid)


def create_arc_job(
    job,
    configuration,
    logger,
    ):
    """Analogon to create_job_script for ARC jobs:
    Creates symLinks for receiving result files, translates job dict to ARC xrsl,
    and stores resulting job script (xrsl + sh script) for submitting.
    
    We do _not_ create a separate job_dict with copies and SESSIONID inside,
    as opposed to create_job_script, all we need is the link from 
    webserver_home / sessionID into the user's home directory 
    ("job_output/job['JOB_ID']" is added to the result upload URLs in the 
    translation). 
    
    Returns message (ARC job ID if no error) and sessionid (None if error)
    """

    if not configuration.arc_clusters:
        return ('No ARC support!', None)
    if not job['JOBTYPE'] == 'arc':
        return ('Error. This is not an ARC job', None)

    client_id = str(job['USER_CERT'])

    # we do not want to see empty jobs here. Test as done in create_job_script.
    if client_id == configuration.empty_job_name:
        return ('Error. empty job for ARC?', None)


    # generate random session ID:
    sessionid = hexlify(open('/dev/urandom').read(32))
    logger.debug('session ID (for creating links): %s' % sessionid)

    client_dir = client_id_dir(client_id)

    # Deep copy job for local changes
    job_dict = deepcopy(job)

    # replace requested REs by env.var.s if zero-install configured.

    if configuration.zero_install_re:

        # ARC resources do not provide any MiG-style runtime env.s.
        # Especially, they do not provide the ZI runtime env. as we
        # expect. So we make a fake entry for the replacement.

        (zi_re, zi_launch_var) = configuration.zero_install_re

        # The following are HARDCODED STRINGS which needs to be
        # consistent with the real ARC runtime env. We assume that ARC
        # will use ENV/ZEROINSTALL and adjust the path to make
        # "0launch" work (unless in scope anyway).

        arc_zi_re = 'ENV/ZERO-INSTALL'
        arc_provides = [(zi_re,[(zi_launch_var, '0launch')])]

        # end of HARDCODED STRINGS

        (zi_env, real_res) = \
             zero_install_replace(job_dict['RUNTIMEENVIRONMENT'],
                                  arc_provides,
                                  configuration)

        # in the ARC case, real_res should not contain anything except
        # zi_re (or nothing, if no zi software is required).
        if real_res and real_res != [zi_re]:
            return ('Cannot satisfy runtime env. requirements (ARC+ZI)',
                    None)
        if real_res == [zi_re]:
            real_res = [arc_zi_re]

        job_dict['RUNTIMEENVIRONMENT'] = real_res
        job_dict['ENVIRONMENT'].extend(zi_env)

    # Finally expand reserved job variables like +JOBID+ and +JOBNAME+
    job_dict = expand_variables(job_dict)

    # make symbolic links inside webserver_home:
    #  
    # we need: link to owner's dir. to receive results, 
    #          job mRSL inside sessid_to_mrsl_link_home
    linklist = [(configuration.user_home + client_dir, 
                 configuration.webserver_home + sessionid),
                (configuration.mrsl_files_dir + client_dir + '/' + \
                 str(job_dict['JOB_ID']) + '.mRSL',
                 configuration.sessid_to_mrsl_link_home + sessionid + '.mRSL')
               ]

    def symlink ((dest,loc)): make_symlink(dest,loc,logger)
    map(symlink, linklist)

    # the translation generates an xRSL object which specifies to execute
    # a shell script with script_name. If sessionid != None, results will
    # be uploaded to sid_redirect/sessionid/job_output/job_id  

    try:
        (xrsl, script, script_name) = mrsltoxrsl.translate(job_dict, sessionid)

    except Exception, err:
        # error during translation, pass a message
        logger.error('Error during xRSL translation: %s' % err.__str__())
        return (err.__str__(), None)
    
        # we submit directly from here (the other version above does 
        # copyFileToResource and gen_job_script generates all files)

    # we have to put the generated script somewhere..., and submit from there.
    # inputfiles are given by the user as relative paths from his home,
    # so we should use that location (and clean up afterwards).

    # write script (to user home)
    user_home = os.path.join(configuration.user_home, client_dir)
    script_path = os.path.abspath(os.path.join(user_home, script_name))
    write_file(script, script_path, logger)

    os.chdir(user_home)

    try:
        logger.debug('submitting job to ARC')
        session = arc.Ui(user_home)
        arc_job_ids = session.submit(xrsl)

        # if no exception occurred, we are done:

        msg = arc_job_ids[0]
        result = sessionid

    # when errors occurred, pass a message to the caller.
    except arc.ARCWrapperError, err:
        msg = err.what()
        result = None # unsuccessful
    except arc.NoProxyError, err:
        msg = 'No Proxy found: %s' % err.what()
        result = None # unsuccessful
    except Exception, err:
        msg = err.__str__()
        result = None # unsuccessful

    # always remove the generated script
    os.remove(script_name)
    # and remove the created links immediately if failed
    if not result:
        map(os.remove, [link for (_,link) in linklist] )
        logger.error('Unsuccessful ARC job submission: %s' % msg)
    else:
        logger.debug('submitted to ARC as job %s' % msg)
    return (msg, result)

    # errors are handled inside grid_script. For ARC jobs, set status = FAILED
    # on errors, and include the message
    # One potential error is that the proxy is invalid,
    # which should be checked inside the parser, before informing 
    # grid_script about the new job.

def gen_job_script(
    job_dictionary,
    resource_config,
    configuration,
    localjobname,
    path_without_extension,
    client_dir,
    exe,
    logger,
    ):

    script_language = resource_config['SCRIPTLANGUAGE']
    if not script_language in configuration.scriptlanguages:
        print 'Unknown script language! (conflict with configuration.scriptlanguages?) %s not in %s'\
             % (script_language, configuration.scriptlanguages)
        return False

    if script_language == 'python':
        generator = genjobscriptpython.GenJobScriptPython(
            job_dictionary,
            resource_config,
            exe,
            configuration.migserver_https_sid_url,
            localjobname,
            path_without_extension,
            )
    elif script_language == 'sh':
        generator = genjobscriptsh.GenJobScriptSh(
            job_dictionary,
            resource_config,
            exe,
            configuration.migserver_https_sid_url,
            localjobname,
            path_without_extension,
            )
    elif script_language == 'java':
        generator = genjobscriptjava.GenJobScriptJava(job_dictionary,
                resource_config, configuration.migserver_https_sid_url,
                localjobname, path_without_extension)
    else:
        print 'Unknown script language! (is in configuration.scriptlanguages but not in jobscriptgenerator) %s '\
             % script_language
        return False

    # String concatenation in python: [X].join is much faster
    # than repeated use of s += strings

    getinputfiles_array = []
    getinputfiles_array.append(generator.script_init())
    getinputfiles_array.append(generator.comment('print start'))
    getinputfiles_array.append(generator.print_start('get input files'))
    getinputfiles_array.append(generator.comment('init log'))
    getinputfiles_array.append(generator.init_io_log())
    getinputfiles_array.append(generator.comment('get special inputfiles'
                               ))
    getinputfiles_array.append(generator.get_special_input_files('get_special_status'
                               ))
    getinputfiles_array.append(generator.log_io_status('get_special_input_files'
                               , 'get_special_status'))
    getinputfiles_array.append(generator.print_on_error('get_special_status'
                               , '0',
                               'failed to fetch special input files!'))
    getinputfiles_array.append(generator.comment('get input files'))
    getinputfiles_array.append(generator.get_input_files('get_input_status'
                               ))
    getinputfiles_array.append(generator.log_io_status('get_input_files'
                               , 'get_input_status'))
    getinputfiles_array.append(generator.print_on_error('get_input_status'
                               , '0', 'failed to fetch input files!'))
    getinputfiles_array.append(generator.comment('get executables'))
    getinputfiles_array.append(generator.get_executables('get_executables_status'
                               ))
    getinputfiles_array.append(generator.log_io_status('get_executables'
                               , 'get_executables_status'))
    getinputfiles_array.append(generator.print_on_error('get_executables_status'
                               , '0',
                               'failed to fetch executable files!'))

    # client_dir equals empty_job_name for sleep jobs

    getinputfiles_array.append(generator.generate_output_filelists(client_dir
                                != configuration.empty_job_name,
                               'generate_output_filelists'))
    getinputfiles_array.append(generator.print_on_error('generate_output_filelists'
                               , '0',
                               'failed to generate output filelists!'))
    getinputfiles_array.append(generator.generate_input_filelist('generate_input_filelist'
                               ))
    getinputfiles_array.append(generator.print_on_error('generate_input_filelist'
                               , '0',
                               'failed to generate input filelist!'))
    getinputfiles_array.append(generator.generate_iosessionid_file('generate_iosessionid_file'
                               ))
    getinputfiles_array.append(generator.print_on_error('generate_iosessionid_file'
                               , '0',
                               'failed to generate iosessionid file!'))

    getinputfiles_array.append(generator.total_status(['get_special_status'
                               , 'get_input_status',
                               'get_executables_status',
                               'generate_output_filelists'],
                               'total_status'))
    getinputfiles_array.append(generator.exit_on_error('total_status',
                               '0', 'total_status'))
    getinputfiles_array.append(generator.comment('exit script'))
    getinputfiles_array.append(generator.exit_script('0',
                               'get input files'))

    job_array = []
    job_array.append(generator.script_init())
    job_array.append(generator.set_core_environments())
    job_array.append(generator.print_start('job'))
    job_array.append(generator.comment('TODO: switch to job directory here'
                     ))
    job_array.append(generator.comment('make sure job status files exist'
                     ))
    job_array.append(generator.create_files([job_dictionary['JOB_ID']
                      + '.stdout', job_dictionary['JOB_ID'] + '.stderr'
                     , job_dictionary['JOB_ID'] + '.status']))
    job_array.append(generator.init_status())
    job_array.append(generator.comment('chmod +x'))
    job_array.append(generator.chmod_executables('chmod_status'))
    job_array.append(generator.print_on_error('chmod_status', '0',
                     'failed to make one or more EXECUTABLES executable'
                     ))
    job_array.append(generator.comment('set environments'))
    job_array.append(generator.set_environments('env_status'))
    job_array.append(generator.print_on_error('env_status', '0',
                     'failed to initialize one or more ENVIRONMENTs'))
    job_array.append(generator.comment('set runtimeenvironments'))
    job_array.append(generator.set_runtime_environments(resource_config['RUNTIMEENVIRONMENT'
                     ], 're_status'))
    job_array.append(generator.print_on_error('re_status', '0',
                     'failed to initialize one or more RUNTIMEENVIRONMENTs'
                     ))
    job_array.append(generator.comment('execute!'))
    job_array.append(generator.execute('EXECUTING: ', '--Exit code:'))
    job_array.append(generator.comment('exit script'))
    job_array.append(generator.exit_script('0', 'job'))

    getupdatefiles_array = []

    # We need to make sure that curl failures lead to retry while
    # missing output (from say a failed job) is logged but
    # ignored in relation to getupdatefiles success.

    getupdatefiles_array.append(generator.print_start('get update files'
                                 ))
    getupdatefiles_array.append(generator.init_io_log())

    getupdatefiles_array.append(generator.comment('get io files'))
    getupdatefiles_array.append(generator.get_io_files('get_io_status'))
    getupdatefiles_array.append(generator.log_io_status('get_io_files'
                                 , 'get_io_status'))
    getupdatefiles_array.append(generator.print_on_error('get_io_status'
                                 , '0',
                                 'failed to get one or more IO files'))
    getupdatefiles_array.append(generator.exit_on_error('get_io_status'
                                 , '0', 'get_io_status'))

    getupdatefiles_array.append(generator.comment('exit script'))
    getupdatefiles_array.append(generator.exit_script('0',
                                 'get update files'))

    sendoutputfiles_array = []

    # We need to make sure that curl failures lead to retry while
    # missing output (from say a failed job) is logged but
    # ignored in relation to sendoutputfiles success.

    sendoutputfiles_array.append(generator.print_start('send output files'
                                 ))
    sendoutputfiles_array.append(generator.init_io_log())
    sendoutputfiles_array.append(generator.comment('check output files'
                                 ))
    sendoutputfiles_array.append(generator.output_files_missing('missing_counter'
                                 ))
    sendoutputfiles_array.append(generator.log_io_status('output_files_missing'
                                 , 'missing_counter'))
    sendoutputfiles_array.append(generator.print_on_error('missing_counter'
                                 , '0', 'missing output files'))
    sendoutputfiles_array.append(generator.comment('send output files'))
    sendoutputfiles_array.append(generator.send_output_files('send_output_status'
                                 ))
    sendoutputfiles_array.append(generator.log_io_status('send_output_files'
                                 , 'send_output_status'))
    sendoutputfiles_array.append(generator.print_on_error('send_output_status'
                                 , '0',
                                 'failed to send one or more outputfiles'
                                 ))
    sendoutputfiles_array.append(generator.exit_on_error('send_output_status'
                                 , '0', 'send_output_status'))

    sendoutputfiles_array.append(generator.comment('send io files'))
    sendoutputfiles_array.append(generator.send_io_files('send_io_status'))
    sendoutputfiles_array.append(generator.log_io_status('send_io_files'
                                 , 'send_io_status'))
    sendoutputfiles_array.append(generator.print_on_error('send_io_status'
                                 , '0',
                                 'failed to send one or more IO files'))
    sendoutputfiles_array.append(generator.exit_on_error('send_io_status'
                                 , '0', 'send_io_status'))
    sendoutputfiles_array.append(generator.comment('send status files'))
    sendoutputfiles_array.append(generator.send_status_files([job_dictionary['JOB_ID'
                                 ] + '.io-status'],
                                 'send_io_status_status'))
    sendoutputfiles_array.append(generator.print_on_error('send_io_status_status'
                                 , '0', 'failed to send io-status file'
                                 ))
    sendoutputfiles_array.append(generator.exit_on_error('send_io_status_status'
                                 , '0', 'send_io_status_status'))

    # Please note that .status upload marks the end of the
    # session and thus it must be the last uploaded file.

    sendoutputfiles_array.append(generator.send_status_files([job_dictionary['JOB_ID'
                                 ] + '.status'], 'send_status_status'))
    sendoutputfiles_array.append(generator.print_on_error('send_status_status'
                                 , '0', 'failed to send status file'))
    sendoutputfiles_array.append(generator.exit_on_error('send_status_status'
                                 , '0', 'send_status_status'))

    # Note that ID.sendouputfiles is called from frontend_script
    # so exit on failure can be handled there.

    sendoutputfiles_array.append(generator.comment('exit script'))
    sendoutputfiles_array.append(generator.exit_script('0',
                                 'send output files'))

    sendupdatefiles_array = []

    # We need to make sure that curl failures lead to retry while
    # missing output (from say a failed job) is logged but
    # ignored in relation to sendupdatefiles success.

    sendupdatefiles_array.append(generator.print_start('send update files'
                                 ))
    sendupdatefiles_array.append(generator.init_io_log())

    sendupdatefiles_array.append(generator.comment('send io files'))
    sendupdatefiles_array.append(generator.send_io_files('send_io_status'))
    sendupdatefiles_array.append(generator.log_io_status('send_io_files'
                                 , 'send_io_status'))
    sendupdatefiles_array.append(generator.print_on_error('send_io_status'
                                 , '0',
                                 'failed to send one or more IO files'))
    sendupdatefiles_array.append(generator.exit_on_error('send_io_status'
                                 , '0', 'send_io_status'))

    sendupdatefiles_array.append(generator.comment('exit script'))
    sendupdatefiles_array.append(generator.exit_script('0',
                                 'send update files'))

    # clean up must be done with SSH (when the .status file
    # has been uploaded): Job script can't safely/reliably clean up
    # after itself because of possible user interference.

    if job_dictionary.has_key('JOBTYPE') and job_dictionary['JOBTYPE'
            ].lower() == 'interactive':

        # interactive jobs have a .job file just containing a curl
        # call to the MiG servers cgi-sid/requestinteractivejob
        # and the usual .job is instead called .interactivejob and
        # is SCP'ed and started by SSH in the requestinteractive.py
        # script

        logger.error('jobtype: interactive')
        interactivejobfile = generator.script_init() + '\n'\
             + generator.request_interactive() + '\n'\
             + generator.exit_script('0', 'interactive job')

        # write the small file containing the requestinteractivejob.py
        # call as .job

        write_file(interactivejobfile, configuration.mig_system_files
                    + job_dictionary['JOB_ID'] + '.job', logger)

        # write the usual .job file as .interactivejob

        write_file('\n'.join(job_array), configuration.mig_system_files
                    + job_dictionary['JOB_ID'] + '.interactivejob',
                   logger)
        print interactivejobfile
    else:

        # write files

        write_file('\n'.join(job_array), configuration.mig_system_files
                    + job_dictionary['JOB_ID'] + '.job', logger)

    write_file('\n'.join(getinputfiles_array), path_without_extension
                + '.getinputfiles', logger)
    write_file('\n'.join(getupdatefiles_array),
               configuration.mig_system_files + job_dictionary['JOB_ID']
                + '.getupdatefiles', logger)
    write_file('\n'.join(sendoutputfiles_array),
               configuration.mig_system_files + job_dictionary['JOB_ID']
                + '.sendoutputfiles', logger)
    write_file('\n'.join(sendupdatefiles_array),
               configuration.mig_system_files + job_dictionary['JOB_ID']
                + '.sendupdatefiles', logger)

    return True

