#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# mrsltoxrsl: translate MiG job to ARC job
#
# (C) 2009 Jost Berthold, grid.dk
#  adapted to usage inside a MiG framework
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

"""translate a "job" from MiG format to ARC format."""

import string
import random

# MiG utilities:
from shared.conf import get_configuration_object
logger = get_configuration_object().logger

# to make this succeed: 
# install nordugrid-arc-client and nordugrid-arc-python
# set LD_LIBRARY_PATH="$NORDUGRID_LOCATION/lib:$GLOBUS_LOCATION/lib
#     PYTHONPATH="$NORDUGRID_LOCATION/lib/python2.4/site-packages"
try:
    import arclib
except:
    logger.error('problems importing arclib... trying workaround')
    try:
        logger.debug('Current sys.path is %s' % sys.path )
        sys.path.append(os.environ['NORDUGRID_LOCATION'] 
                        + '/lib/python2.4/site-packages')
        import arclib
    except:
        logger.error('arclib not found. Aborting whole execution.')
        sys.exit(255)

# translate :: Dictionary (checked) -> (Xrsl,Job Script,name for Job script)
def translate(mrsl_dict, name = None):
    """Translate an (already checked) mRSL dictionary into xRSL,
       suitable for submitting to an ARC resource. 
       
       Returns arclib.Xrsl object.
       Throws exception if errors in the xRSL generation occur."""
    try:
        # every xrsl-specified job is a conjunction at the top level
        xrsl = arclib.Xrsl(arclib.operator_and)

        if mrsl_dict.hasKey('JOB_ID'):
            j_name = mrsl_dict['JOB_ID']
        else:
            # random string. should not happen anyway...
            j_name = ''.join(random.choice(string.letters) \
                             for i in xrange(12))

        # use JOBID as ARC jobname to avoid presenting only ARC IDs
        addRel(xrsl,'jobname', 
               ''.join(mrsl_dict.get('JOBNAME',''),'(',j_name,')'))

        # inputfiles + executables, outputfiles
        # make double lists, 2nd part perhaps empty
        # output files, always including stdout
        if mrsl_dict.hasKey('OUTPUTFILES'):
            outfiles = map(file_mapping, mrsl_dict['OUTPUTFILES'])
        else:
            outfiles = []
        addRel(xrsl, 'stdout', '.'.join(j_name,'stdout'))
        outfiles.append(['.'.join(j_name,'stdout'),''])
        addRel(xrsl, 'stderr', '.'.join(j_name,'stderr'))
        outfiles.append(['.'.join(j_name,'stderr'),''])
        addRel(xrsl, 'outputfiles', outfiles)
        # do not merge stdout and stderr
        addRel(xrsl, 'join', 'no')
        
        # what we want to do: EXECUTE (should be there)
        script = mrsl_dict['EXECUTE']
        # the script is expected to be present as an input file,
        # and to have a certain name which we return.
        addRel(xrsl,'executable','/bin/sh')
        # HEADS UP: this is the script name we wire in.
        script_name = '.'.join(j_name,'sh')
        addRel(xrsl,'arguments', script_name)

        # executable input files, always including the execute script
        if mrsl_dict.hasKey('EXECUTABLES'):
            execfiles = map(file_mapping, mrsl_dict['EXECUTABLES'])
        else:
            execfiles = []
        # HEADS UP: the script name again!
        execfiles.append([script_name,''])

        # (non-executable) input files
        if mrsl_dict.hasKey('INPUTFILES'):
            infiles = map(file_mapping, mrsl_dict['INPUTFILES'])
        else:
            infiles = []

        addRel(xrsl, 'inputfiles', execfiles + infiles)

        def fst(list):
            return list[0]
        addRel(xrsl, 'executables', map(fst, execfiles))


        # more stuff...

        # requested runtime, given in minutes in (user) xrsl ...
        time = mrsl_dict.get('CPUTIME')
        if time:
            addRel(xrsl, 'cputime', str(float(time)/60))

        # simply copy the values for these:
        copy_items = ['MEMORY', 'DISK', 'NODECOUNT'] 
        xrsl_name = {'MEMORY':'memory', 'DISK':'disk', 'NODECOUNT':'count'} 
        # NB: we have to ignore CPUCOUNT, not supported by ARC xrsl

        for x in copy_items: # we ignore the ones which are not there
            if mrsl_dict.hasKey(x):
                addRel(xrsl,xrsl_name[x],mrsl_dict[x])
                # and these are all single values

        if mrsl_dict.hasKey('ARCHITECTURE'):
            addRel(xrsl,'architecture',
                   translate_arch(mrsl_dict['ARCHITECTURE']))

        if mrsl_dict.hasKey('ENVIRONMENT'):
            var_val = []
            for definition in mrsl_dict['ENVIRONMENT']:
                vv = definition.strip().split('=')
                var_val.append(vv.strip())
            addRel(xrsl,'environment',var_val)

        if mrsl_dict.hasKey('RUNTIMEENVIRONMENT'):
            for line in mrsl_dict['RUNTIMEENVIRONMENT']:
                addRel(xrsl,'runtimeenvironment', line.strip())

        if mrsl_dict.hasKey('NOTIFY'):
            addresses = []
            for line in filter(is_mail, mrsl_dict['NOTIFY'])[0:2]: # max 3
                # remove whites before, then "email:" prefix, then strip
                address = line.lstrip()[6:].strip()
                if address != 'SETTINGS':
                    addresses.append(address)
#                else:
#                    # FIXME: get it from the settings :-P
#                    addresses.append('*FROM THE SETTINGS*') 
            if addresses:
                addRel(xrsl,'notify', 'ec ' + ' '.join(addresses))

        logger.debug('translated: %s' % xrsl)
    except arclib.XrslError, err:
        logger.error( 'Error generating Xrsl: %s' % err )
    return (xrsl,script,'.'.join(j_name,'sh'))

# helper functions and constants used:

# write_pair :: (String,a)       -> arclib.XrslRelation
# and is polymorphic in a: a = String, a = List(String), a = List(List(String))
# the C version of XrslRelation is... so we emulate it here:
def write_pair(name, values):
    if instanceof(values,list):
        if instanceof(values[0],list):
            con = arclib.XrslRelationDoubleList
        else:
            con = arclib.XrslRelationList
    else:
        con = arclib.XrslRelation
    return con(name,arclib.operator_eq,values)

# used all the time...
def addRel(xrsl,name,values):
    xrsl.AddRelation(write_pair(name,values))

# architectures
architectures = [{'X86':'i686', 'AMD64':'x86-64', 'IA64':'ia64', 
                  'SPARC':'sparc64', 'SPARC64':'sparc64', 
                  'ITANIUM':'???ia64???', 
                  'SUN4U':'sun4u', 'SPARC-T1':'sparc64', 'SPARC-T2':'sparc64', 
                  'PS3':'??unknown??', 
                  'CELL':'cell'}]
def translate_arch(mig_arch):

    if architectures.hasKey(mig_arch):
        return architectures[mig_arch]

def is_mail(str):
    return str.lstrip().startswith('email:')

def file_mapping(line):
    """Splits the given line of the expected format 
          local_name <space> remote_name
       into a 2-element list [local_name,remote_name]
       If remote_name is empty, the empty string is returned as the 2nd part.
       No additional checks are performed.
       TODO should perhaps also check for valid path characters."""
    line = line.strip()
    parts = line.split()
    local = parts[0]
    if len(parts) < 2:
        remote = ''
    else:
        remote = parts[1]
    return [local,remote]


if __name__ == '__main__':
    print len(sys.argv)
    if len(sys.argv) > 1:
        fname = sys.argv[1]

