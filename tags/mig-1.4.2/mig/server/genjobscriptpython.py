#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# genjobscriptpython - [insert a few words of module description on this line]
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

"""Python job script generator and functions"""

import os

from shared.job import output_dir

def curl_cmd_send(resource_filename, mig_server_filename,
                  https_sid_url_arg):
    """Upload files"""

    return "curl --location --fail --silent --insecure --upload-file '"\
         + resource_filename + "' -X SIDPUT '" + https_sid_url_arg\
         + '/sid_redirect/' + job_dict['MIGSESSIONID'] + '/'\
         + mig_server_filename + "'"


def curl_cmd_get(mig_server_filename, resource_filename,
                 https_sid_url_arg):
    """Download files"""

    dest_path = os.path.split(resource_filename)[0]
    cmd = ''
    if dest_path != '':
        cmd += "mkdir -p '%s' && \\" % dest_path
        cmd += '\n'
    cmd += "curl --location --fail --silent --insecure -o '" + resource_filename\
         + "' '" + https_sid_url_arg + '/sid_redirect/'\
         + job_dict['MIGSESSIONID'] + '/' + mig_server_filename + "'"
    return cmd


def curl_cmd_get_special(file_extension, resource_filename,
                         https_sid_url_arg):
    """Download internal job files"""

    dest_path = os.path.split(resource_filename)[0]
    cmd = ''
    if dest_path != '':
        cmd += 'mkdir -p %s && \\' % dest_path
        cmd += '\n'
    cmd += "curl --location --fail --silent --insecure -o '" + resource_filename\
         + "' '" + https_sid_url_arg + '/sid_redirect/'\
         + job_dict['MIGSESSIONID'] + file_extension + "'"
    return cmd


def curl_cmd_request_interactive(https_sid_url_arg):
    """CGI request for interactive job"""

    int_command = "curl --location --fail --silent --insecure '"\
         + https_sid_url_arg\
         + '/cgi-sid/requestinteractivejob.py?sessionid='\
         + job_dict['MIGSESSIONID'] + '&jobid=' + job_dict['JOB_ID']\
         + '&exe=' + exe + '&unique_resource_name='\
         + resource_conf['RESOURCE_ID'] + '&localjobname='\
         + localjobname + "'\n"
    int_command += '# wait until interactive command is done\n'
    int_command += 'while [ 1 ]; do\n'
    int_command += '   if [ -f .interactivejobfinished ]; then\n'
    int_command += '        break\n'
    int_command += '   else\n'
    int_command += '        sleep 3\n'
    int_command += '   fi\n'
    int_command += 'done\n'
    return int_command


class GenJobScriptPython:

    """Python job script generator"""

    def __init__(
        self,
        job_dictionary,
        resource_config,
        exe_unit,
        https_sid_url,
        localjobnam,
        filename_without_ext,
        ):

        # TODO: this is damn ugly!

        global job_dict
        job_dict = job_dictionary
        global resource_conf
        resource_conf = resource_config
        global exe
        exe = exe_unit
        global https_sid_url_arg
        https_sid_url_arg = https_sid_url
        global filename_without_extension
        filename_without_extension = filename_without_ext
        global localjobname
        localjobname = localjobnam
        global io_log
        io_log = '%s.io-status' % job_dict['JOB_ID']

        print """Python resource scripts are *not* fully supported!
Please use Sh as SCRIPTLANGUAGE on your resources if this fails!"""

    def comment(self, string):
        """Insert comment"""

        return '""" ' + string + ' """ \n'

    def script_init(self):
        """initialize script"""

        return '''#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# ??? - one of the python scripts running on resources
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

import os
import stat
from os.path import join, getsize
'''

    def print_start(self, name='job'):
        """print 'starting new job'"""

        return "print 'Starting new %s with JOB_ID: %s'\n" % (name,
                job_dict['JOB_ID'])

    def create_files(self, files):
        """Create supplied files"""

        cmd = ''
        for path in files:

            # Create/truncate files by opening in 'w' mode

            cmd += "open('%s', 'w').close()\n" % path
        return cmd

    def init_status(self):
        """Initialize status file"""

        return """status_fd = open('%s.status', 'r+')
status_fd.write('Internal job setup failed!
')
status_fd.close()
"""\
             % job_dict['JOB_ID']

    def init_io_log(self):
        """Open IO status log"""

        return "io_log = open(%s, 'w')" % io_log

    def log_io_status(self, io_type, result='ret'):
        """Write to IO status log"""

        return '''io_log.write("%s " + %s)
io_log.flush()'''\
             % (io_type, result)

    def create_job_directory(self):
        """if directory with name JOB_ID doesnt exists, then create.
        cd into it."""

        cmd = 'if os.path.isdir("' + job_dict['JOB_ID'] + '")==False:\n'
        cmd += '   os.mkdir("' + job_dict['JOB_ID'] + '")\n'
        return cmd

    def cd_to_job_directory(self):
        """Enter execution directory"""

        return 'os.chdir("' + job_dict['JOB_ID'] + '")'

    def get_input_files(self, result='get_input_status'):
        """get the inputfiles from the grid server"""

        cmd = ''

        for infile in job_dict['INPUTFILES']:

            # "filename" or "mig_server_filename resource_filename"

            parts = infile.split()
            mig_server_filename = str(parts[0])
            try:
                resource_filename = str(parts[1])
            except:
                resource_filename = mig_server_filename

            # Source may be external in which case implicit destination needs attention

            if resource_filename.find('://') != -1:

                # Strip any protocol prefixes in destination for external sources

                resource_filename = resource_filename.split('://', 1)[1]

            # Always strip leading slashes to avoid absolute paths

            resource_filename = resource_filename.lstrip('/')

            cmd += 'os.popen("%s", "r")\n' % curl_cmd_get(mig_server_filename,
                                                          resource_filename,
                                                          https_sid_url_arg)
        return cmd

    def get_special_input_files(self, result='get_special_status'):
        """get the internal job files from the grid server"""

        cmd = ''
        cmd += curl_cmd_get_special('.job', localjobname + '.job',
                                    https_sid_url_arg) + ' && \\'\
             + '\n'

        cmd += '''
%s
''' % curl_cmd_get_special('.getupdatefiles',
                localjobname + '.getupdatefiles',
                https_sid_url_arg)
        cmd += '''
%s
''' % curl_cmd_get_special('.sendupdatefiles',
                localjobname + '.sendupdatefiles',
                https_sid_url_arg)
        cmd += '''
%s
''' % curl_cmd_get_special('.sendoutputfiles',
                localjobname + '.sendoutputfiles',
                https_sid_url_arg)
        return cmd

    def get_executables(self, result='get_executables_status'):
        """Get EXECUTABLES (inputfiles and +x)"""

        cmd = ''
        for executables in job_dict['EXECUTABLES']:

            # "filename" or "mig_server_filename resource_filename"

            parts = executables.split()
            mig_server_filename = str(parts[0])
            try:
                resource_filename = str(parts[1])
            except:
                resource_filename = mig_server_filename

            # Source may be external in which case implicit destination needs attention

            if resource_filename.find('://') != -1:

                # Strip any protocol prefixes in destination for external sources

                resource_filename = resource_filename.split('://', 1)[1]

            # Always strip leading slashes to avoid absolute paths

            resource_filename = resource_filename.lstrip('/')

            cmd += 'os.popen("%s", "r")\n' % curl_cmd_get(mig_server_filename,
                                                          resource_filename,
                                                          https_sid_url_arg)
        return cmd

    def get_io_files(self, result='get_io_status'):
        """Get live files from server during job execution"""

        cmd = ''
        cmd += 'dst = sys.argv[-1]\n'
        cmd += 'for name in sys.argv[1:-1]:\n'
        cmd += '  name_on_resource = os.path.join(dst, os.path.basename(name))\n'
        cmd += '  os.popen("' + curl_cmd_get('name',
                                             'name_on_resource',
                                             https_sid_url_arg)\
                                             + '")\n'
        return cmd

    def generate_input_filelist(self, result='generate_input_filelist'):
        """Generate filelist (user/system) of which files 
        should be transfered from FE to EXE before job execution."""

        cmd = \
            '# Create files used by master_node_script (input/executables/systemfiles)\n'
        fe_move_dict = {}

        for infile in job_dict['INPUTFILES']:

            # "filename" or "mig_server_filename resource_filename"

            parts = infile.split()
            mig_server_filename = str(parts[0])
            try:
                resource_filename = str(parts[1])
            except:
                resource_filename = mig_server_filename

            # Source may be external in which case implicit destination needs attention

            if resource_filename.find('://') != -1:

                # Strip any protocol prefixes in destination for external sources

                resource_filename = resource_filename.split('://', 1)[1]

            # Always strip leading slashes to avoid absolute paths

            resource_filename = resource_filename.lstrip('/')

            # move entire top dir if resource_filename is a nested path

            fe_move = resource_filename.split('/', 1)[0]

            if not fe_move_dict.has_key(fe_move):
                fe_move_dict[fe_move] = True

        for executables in job_dict['EXECUTABLES']:

            # "filename" or "mig_server_filename resource_filename"

            parts = executables.split()
            mig_server_filename = str(parts[0])
            try:
                resource_filename = str(parts[1])
            except:
                resource_filename = mig_server_filename

            # Source may be external in which case implicit destination needs attention

            if resource_filename.find('://') != -1:

                # Strip any protocol prefixes in destination for external sources

                resource_filename = resource_filename.split('://', 1)[1]

            # Always strip leading slashes to avoid absolute paths

            resource_filename = resource_filename.lstrip('/')

            # move entire top dir if resource_filename is a nested path

            fe_move = resource_filename.split('/', 1)[0]

            if not fe_move_dict.has_key(fe_move):
                fe_move_dict[fe_move] = True

        cmd += 'input_fd = open("%s.inputfiles", "w")\n' % localjobname
        for filename in fe_move_dict.keys():
            cmd += '''
if os.path.isfile("%s"):
    input_fd.write("%s ")
''' % (filename, filename)
        cmd += 'input_fd.close()\n'

        # Systemfiles

        cmd += 'output_fd = open("%s.outputfiles", "w")\n' % localjobname
        cmd += 'output_fd.write("%s.user.outputfiles ")\n' % localjobname
        cmd += 'output_fd.write("%s.system.outputfiles ")\n' % localjobname
        cmd += 'output_fd.write("%s.job")\n' % localjobname
        cmd += 'output_fd.close()\n'
        return cmd

    def generate_output_filelists(self, real_job,
                                  result='generate_output_filelists'):
        """Generate filelists (user/system) of which files
        should be transfered from EXE to FE upon job finish."""

        exe_move_dict = {}
        cmd = \
            '# Create files used by master_node_script to determine which output files to transfer to FE\n'

        cmd += 'output_fd = open("%s.user.outputfiles", "w")\n' % localjobname
        for outputfile in job_dict['OUTPUTFILES']:

            # "filename" or "resource_filename mig_server_filename"

            parts = outputfile.split()
            resource_filename = str(parts[0])

            # We don't need mig_server_filename here so just skip mangling

            # Always strip leading slashes to avoid absolute paths

            resource_filename = resource_filename.lstrip('/')

            # move entire top dir if resource_filename is a nested path

            exe_move = resource_filename.split('/', 1)[0]

            if not exe_move_dict.has_key(exe_move):
                exe_move_dict[exe_move] = True

        for filename in exe_move_dict.keys():
            cmd += 'output_fd.write("%s ")\n' % filename
        cmd += 'output_fd.close()\n'
        cmd += 'output_fd = open("%s.system.outputfiles", "w")\n' % localjobname

        # Sleep jobs only generate .status

        if real_job:
            cmd += 'output_fd.write("%s.stderr ")\n' % job_dict['JOB_ID']
            cmd += 'output_fd.write("%s.stdout ")\n' % job_dict['JOB_ID']
            cmd += 'output_fd.write("%s.status ")\n' % job_dict['JOB_ID']
        cmd += 'output_fd.close()\n'
        return cmd

    def generate_iosessionid_file(self,
                                  result='generate_iosessionid_file'):
        """Generate file containing io-sessionid."""

        cmd = '# Create file used containing io-sessionid.\n'
        cmd += 'iosid_fd = open("%s.iosessionid", "w")\n' % localjobname
        cmd += 'iosid_fd.write("%s")\n' % job_dict['MIGIOSESSIONID']
        cmd += 'iosid_fd.close()\n'
        return cmd

    def chmod_executables(self, result='chmod_status'):
        """Make sure EXECUTABLES are actually executable"""

        cmd = ''
        for executables in job_dict['EXECUTABLES']:
            cmd += 'os.chmod("' + executables + '", stat.S_IRWXU)'
        return cmd

    def set_core_environments(self):
        """Set missing core environments: LRMS may strip them during submit"""
        requested = {'CPUTIME': job_dict['CPUTIME']}
        requested['NODECOUNT'] = job_dict.get('NODECOUNT', 1)
        requested['CPUCOUNT'] = job_dict.get('CPUCOUNT', 1)
        requested['MEMORY'] = job_dict.get('MEMORY', 1)
        requested['DISK'] = job_dict.get('DISK', 1)
        requested['JOBID'] = job_dict.get('JOB_ID', 'UNKNOWN')
        requested['LOCALJOBNAME'] = localjobname
        requested['EXE'] = exe
        requested['EXECUTION_DIR'] = ''
        exe_list = resource_conf.get('EXECONFIG', [])
        for exe_conf in exe_list:
            if exe_conf['name'] == exe:
                requested['EXECUTION_DIR'] = exe_conf['execution_dir']
                break
        requested['JOBDIR'] = '%(EXECUTION_DIR)s/job-dir_%(LOCALJOBNAME)s' % \
                              requested
        cmd = '''
if not os.environ.get("MIG_JOBNODES", ""):
  os.putenv("MIG_JOBNODES", "%(NODECOUNT)s")
if not os.environ.get("MIG_JOBNODECOUNT", ""):
  os.putenv("MIG_JOBNODECOUNT", "%(NODECOUNT)s")
if not os.environ.get("MIG_JOBCPUTIME", ""):
  os.putenv("MIG_JOBCPUTIME", "%(CPUTIME)s")
if not os.environ.get("MIG_JOBCPUCOUNT", ""):
  os.putenv("MIG_JOBCPUCOUNT", "%(CPUCOUNT)s")
if not os.environ.get("MIG_JOBMEMORY", ""):
  os.putenv("MIG_JOBMEMORY", "%(MEMORY)s")
if not os.environ.get("MIG_JOBDISK", ""):
  os.putenv("MIG_JOBDISK", "%(DISK)s")
if not os.environ.get("MIG_JOBID", ""):
  os.putenv("MIG_JOBID", "%(JOBID)s")
if not os.environ.get("MIG_LOCALJOBNAME", ""):
  os.putenv("MIG_LOCALJOBNAME", "%(LOCALJOBNAME)s")
if not os.environ.get("MIG_EXEUNIT", ""):
  os.putenv("MIG_EXEUNIT", "%(EXE)s")
if not os.environ.get("MIG_EXENODE", ""):
  os.putenv("MIG_EXENODE", "%(EXE)s")
if not os.environ.get("MIG_JOBDIR", ""):
  os.putenv("MIG_JOBDIR", "%(JOBDIR)s")
''' % requested
        return cmd

    def set_environments(self, result='env_result'):
        """Set environments"""

        cmd = ''

        for env in job_dict['ENVIRONMENT']:
            key_and_value = env.split('=', 1)
            cmd += 'os.putenv("' + key_and_value[0] + '","'\
                 + key_and_value[1] + '")\n'

        return cmd

    def set_limits(self):
        """Set local resource limits to prevent fork bombs, OOM and such"""
        # TODO: implement limits!
        return ''

    def set_runtime_environments(self, resource_runtimeenvironment,
                                 result='re_result'):
        """Set Runtimeenvironments"""

        cmd = ''

        # loop the runtimeenvs that the job require

        for env in job_dict['RUNTIMEENVIRONMENT']:

            # set the envs as specified in the resources config file

            for res_env in resource_runtimeenvironment:

                # check if this is the right env in resource config

                if env == res_env[0]:

                    # this is the right list of envs. Loop the entire list and set all the envs

                    for single_env in res_env[1]:
                        key_and_value = single_env.split('=', 1)
                        cmd += 'os.putenv("' + key_and_value[0] + '","'\
                             + key_and_value[1] + '")\n'

        return cmd

    def execute(self, pretext, posttext):
        """Command execution"""

        stdout = job_dict['JOB_ID'] + '.stdout'
        stderr = job_dict['JOB_ID'] + '.stderr'
        status = job_dict['JOB_ID'] + '.status'
        cmd = ''

        cmd += 'status_handle = open("' + status + '","w")\n'

        for exe in job_dict['EXECUTE']:
            exe = exe.replace('"', '\\"')
            cmd += 'print "' + pretext + exe + '"\n'

            cmd += 'if "' + exe + '".find(" >> ") != -1:\n'
            cmd += '   filehandle = os.popen("' + exe + ' 2>> ' + stdout\
                 + '", "r")\n'
            cmd += 'else:\n'
            cmd += '   filehandle = os.popen("' + exe + ' >> ' + stdout\
                 + ' 2>> ' + stderr + '", "r")\n'
            cmd += 'status = filehandle.close()\n'
            cmd += 'if status == None:\n'
            cmd += '  status = "0"\n'
            cmd += 'else:\n'
            cmd += '  status = str(status)\n'
            cmd += 'status_handle.write("' + exe\
                 + ' " + str(status) + "\\n")\n'
            cmd += 'print "' + posttext + '" + str(status)\n'

        cmd += 'status_handle.close()\n'

        return cmd

    def output_files_missing(self, result='missing_counter'):
        """Check availability of outputfiles:
        Return number of missing files.
        """

        cmd = '%s = 0\n' % result
        for outputfile in job_dict['OUTPUTFILES']:
            cmd += 'if not os.path.isfile("' + outputfile + '":\n'
            cmd += '  %s += 1\n' % result
        return cmd

    def send_output_files(self, result='send_output_status'):
        """Send outputfiles"""

        cmd = ''

        for outputfile in job_dict['OUTPUTFILES']:

            # "filename" or "resource_filename mig_server_filename"

            parts = outputfile.split()
            resource_filename = str(parts[0])
            try:
                mig_server_filename = str(parts[1])
            except:
                mig_server_filename = resource_filename

            # External destinations will always be explicit so no
            # need to mangle protocol prefix here as in get inputfiles

            # Always strip leading slashes to avoid absolute paths

            mig_server_filename = mig_server_filename.lstrip('/')

            cmd += 'if (os.path.isfile("' + resource_filename\
                 + '") and os.path.getsize("' + resource_filename\
                 + '") > 0):\n'
            cmd += '  os.popen("%s")\n' % curl_cmd_send(resource_filename,
                                                        mig_server_filename,
                                                        https_sid_url_arg)
        return cmd

    def send_io_files(self, result='send_io_status'):
        """Send IO files:
        Existing files must be transferred with status 0, while
        non-existing files shouldn't lead to error.
        Only react to curl transfer errors, not MiG put errors
        since we can't handle the latter consistently anyway.
        """

        cmd = ''
        cmd += 'dst = sys.argv[-1]\n'
        cmd += 'for src in sys.argv[1:-1]:\n'
        cmd += '  # stored in flat structure on FE\n'
        cmd += '  name = os.path.basename(src)\n'
        cmd += '  name_on_mig_server = os.path.join(dst, name)\n'
        cmd += '  if (os.path.isfile(name) and os.path.getsize(name) > 0):\n'
        cmd += '    os.popen("' + curl_cmd_send('name',
                    'name_on_mig_server', https_sid_url_arg)\
                 + '")\n'
        return cmd

    def send_status_files(self, files, result='send_status_status'):
        """Send .status"""

        # Missing files must raise an error status

        cmd = ''
        for name in files:
            name_on_mig_server = os.path.join(output_dir, job_dict['JOB_ID'],
                                              name)

            # cmd += "os.popen(\"%s\")\n" % curl_cmd_send(name)

            cmd += 'os.popen("' + curl_cmd_send(name,
                    name_on_mig_server, https_sid_url_arg)\
                 + '")\n'
        return cmd

    def request_interactive(self):
        """Request interactive job"""

        # return curl_cmd_request_interactive(https_sid_url_arg, job_dict, resource_conf, exe)

        return curl_cmd_request_interactive(https_sid_url_arg)

    def save_status(self, variable='ret'):
        """Save exit code"""

        return '''
%s = status >> 8
''' % variable

    def total_status(self, variables, result='total_status'):
        """Logically 'and' variables and save result"""

        cmd = '''
%s = True
''' % result
        for var in variables:
            cmd += 'if %s:\n' % var
            cmd += '  %s = False\n' % result
        return cmd

    def print_on_error(
        self,
        variable='ret',
        successcode='0',
        msg='ERROR: unexpected exit code!',
        ):
        """Print msg unless last command exitted with successcode"""

        cmd = 'if ' + variable + ' != ' + successcode + ':\n'
        cmd += '\tprint "WARNING: ' + msg + "\(\" + " + variable\
             + " + \"\)\"\n"
        cmd += '\n'
        return cmd

    def exit_on_error(
        self,
        variable='ret',
        successcode='0',
        exitcode='ret',
        ):
        """exit with exitcode unless last command exitted with
        success code"""

        cmd = 'if ' + variable + ' != ' + successcode + ':\n'
        cmd += '\tsys.exit(' + exitcode + ')\n'
        cmd += '\n'
        return cmd

    def exit_script(self, exitcode='0', name=''):
        """Please note that frontend_script relies on the
        '### END OF SCRIPT ###' string to check that getinputfiles
        script is fully received. Thus changes here should be
        reflected in frontend_script!
        """

        return 'print "' + name + ' script end reached '\
             + job_dict['JOB_ID'] + '" \nsys.exit(' + exitcode + ')\n'\
             + '### END OF SCRIPT ###\n'

    def clean_up(self):
        """Clean up"""

        # cd .., rm -rf "job id"

        cmd = 'os.chdir("..")\n'
        cmd += 'top = "' + job_dict['JOB_ID'] + '"\n'
        cmd += 'for root, dirs, files in os.walk(top, topdown=False):\n'
        cmd += '  for name in files:\n'
        cmd += '     os.remove(join(root, name))\n'
        cmd += '  for name in dirs:\n'
        cmd += '     os.rmdir(join(root, name))\n'
        cmd += 'os.rmdir(top)'
        return cmd


