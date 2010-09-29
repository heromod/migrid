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

        print "Usage: migtest.py [OPTIONS] [OPERATION ...]"
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


def put_file(src_path, dst_path, submit_mrsl, extract_package):

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

        content_type = "''"
        if submit_mrsl and extract_package:
           content_type = 'Content-Type:submitandextract'
        elif submit_mrsl:
           content_type = 'Content-Type:submitmrsl'
        elif extract_package:
           content_type = 'Content-Type:extractpackage'

	# import StringIO

        curl = 'curl --compressed'
        target = '--upload-file %s --header %s -X CERTPUT' % (src_path, content_type)
        location = "%s" % dst_path.lstrip("/")
        post_data = ""
        query = ""
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


def test_op(op):

        print "running %s test" % (op)



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
opt_args = "c:hrs:vV"

# preserve arg 0
arg_zero = sys.argv[0]
args = sys.argv[1:]
try:
        opts, args = getopt.getopt(args, opt_args)
except getopt.GetoptError, e:
        print "Error: ", e.msg
        usage()
        sys.exit(1)

for (opt, val) in opts:
        if opt == "-r":
                recursive = True
                server_flags += "r"
        elif opt == "-s":
                mig_server = val
        elif opt == "-v":
                verbose = True
        elif opt == "-V":
                version()
                sys.exit(0)
        elif opt == "-h":
                usage()
                sys.exit(0)
        elif opt == "-c":
                conf = val

        else:
                print "Error: %s not supported!" % (opt)

        # Drop options while preserving original sys.argv[0] 
        sys.argv = [arg_zero] + args
arg_count = len(sys.argv) - 1

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

if len(sys.argv) - 1 == 0:
   op_list = ['cancel', 'cat', 'doc', 'get', 'head', 'ls', 'mkdir', 'mv', 'put', 'read', 'rm', 'rmdir', 'stat', 'status', 'submit', 'tail', 'touch', 'truncate', 'wc', 'write', 'liveoutput']
else:   
   op_list = sys.argv[1:]

for op in op_list:
   test_op(op)
