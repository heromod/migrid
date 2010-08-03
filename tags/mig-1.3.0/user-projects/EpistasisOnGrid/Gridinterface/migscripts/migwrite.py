#!/usr/bin/python 
# 
# This MiG python script was autogenerated by the MiG User Script Generator !!!
# Any changes should be made in the generator and not here !!!

import sys
import os
import getopt

def version():
	print "MiG User Scripts: $Revision: 2506 $,$Revision: 2506 $"


def usage():

        print "Usage: migwrite.py [OPTIONS] START END SRC DST"
        print "Where OPTIONS include:"
        print "-r		recursive"
        print "-v		verbose mode"
        print "-V		display version"
        print "-h		display this help"
        print "-c CONF		read configuration from CONF instead of"
        print "		default (~/.mig/miguser.conf)."
        print "-s MIG_SERVER	force use of MIG_SERVER."

def check_var(name, var):

        if not var:
           print name + " not set! Please set in configuration file or through the command line"
           sys.exit(1)

def read_conf(conf, option):

        try:
            conf_file = open(conf, 'r')
            for line in conf_file.readlines():
                line = line.strip()
                # split on any whitespace and assure at least two parts
                parts = line.split() + ['', '']
                opt, val = parts[0], parts[1]
                if opt == option:
                    return val
            conf_file.close()
        except Exception, e:
            return ''


def write_file(first, last, src_path, dst_path):

        if not ca_cert_file:
           ca_check = '--insecure'
        else:
           ca_check = "--cacert %s" % (ca_cert_file)

        if not password:
           password_check = ''
        else:
           password_check = "--pass %s" % (password)

        timeout = ''
        if max_time:
           timeout += "--max-time %s" % (max_time)
        if connect_timeout:
           timeout += " --connect-timeout %s" % (connect_timeout)

	# import StringIO

        curl = 'curl --compressed'
        target = '--upload-file %s' % src_path
        location = "cgi-bin/rangefileaccess.py"
        post_data = ""
        query = '?output_format=txt;flags=%s;file_startpos=%s;file_endpos=%s;path=%s' % (server_flags, first, last, dst_path)
        data = ''
        if post_data:
            data = '--data "%s"' % post_data
        command = "%s --fail --silent --cert %s --key %s %s %s %s %s %s --url '%s/%s%s'" % (curl, cert_file, key_file, data, ca_check, password_check, timeout, target, mig_server, location, query)
        # TODO: should we replace popen4 call with this next section?
        #from subprocess import Popen, PIPE, STDOUT
        #proc = Popen(command, shell=True, stdout=PIPE, stderr=STDOUT,
        #                     close_fds=True)
        #out = proc.stdout.readlines()
        #proc.stdout.close()
        #exit_code = proc.returncode
        (_, all_out) = os.popen4(command, 'r', 0)
        out = all_out.readlines()
        status = all_out.close()
        if status:
            exit_code = status >> 8
        else:
            exit_code = 0

	return (exit_code, out)



# === Main ===

recursive = 0
verbose = 0
conf = os.path.expanduser("~/.mig/miguser.conf")
flags = ""
mig_server = ""
server_flags = ""
script_path = sys.argv[0]
script_name = os.path.basename(script_path)
script_dir = os.path.dirname(script_path)
arg_count = len(sys.argv) - 1
min_count = 4

if arg_count < min_count:
   print "Too few arguments: got %d, expected %d!" % (arg_count, min_count)
   usage()
   sys.exit(1)

if not os.path.isfile(conf):
   print "Failed to read configuration file: %s" % (conf)
   sys.exit(1)

if verbose:
    print "using configuration in %s" % (conf)

if not mig_server:
   mig_server = read_conf(conf, 'migserver')

cert_file = read_conf(conf, 'certfile')
key_file = read_conf(conf, 'keyfile')
ca_cert_file = read_conf(conf, 'cacertfile')
password = read_conf(conf, 'password')
connect_timeout = read_conf(conf, 'connect_timeout')
max_time = read_conf(conf, 'max_time')

check_var("migserver", mig_server)
check_var("certfile", cert_file)
check_var("keyfile", key_file)

(status, out) = write_file(*(sys.argv[1:]))
for line in out:
    print line.strip()
