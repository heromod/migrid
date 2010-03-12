#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# showvgridprivatefile - [insert a few words of module description on this line]
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

# Minimum Intrusion Grid

"""Show the requested file located in a given vgrids private_base dir"""

import cgi
import cgitb
cgitb.enable()
import os
import re
import subprocess
import sys
import time

from shared.validstring import valid_dir_input
from shared.cgishared import init_cgi_script_with_cert
from shared.vgrid import vgrid_is_owner_or_member


def scale_bytes(bytes):

    """Scale bytes to an appropriate size, returning the scaled number
       and an appropriate suffix as one string for pretty printing"""

    # factors/letters have to be descending.

    factors = zip( [30,20,10], ['G','M','K'])

    for (k,s) in factors:

        x = bytes*1.0 / pow(2,k)
        if x > 1:

            return ( ("%.3f" % x) + ' ' + s+'B')

    # if not successful, we reach here. Return Bytes.

    return (str(bytes) + ' B')


# ## Main ###

# will print the content type later when we have inspected the file
(logger, configuration, client_id, o) = \
          init_cgi_script_with_cert(print_header=False)

fieldstorage = cgi.FieldStorage()
if not fieldstorage.getfirst('vgrid_name', '') == '':

    # using web form
    # htmlquery = "false" #changed!

    vgrid_name = fieldstorage.getfirst('vgrid_name', '')

specified_filename = fieldstorage.getfirst('file', 'index.html')

# No owner check here so we need to specifically check for illegal
# directory traversals

private_base_dir = os.path.abspath(configuration.vgrid_private_base)\
     + os.sep

if not valid_dir_input(configuration.vgrid_home, vgrid_name):
    o.out('Illegal vgrid_name: %s' % vgrid_name)
    logger.warning("showvgridprivatefile registered possible illegal directory traversal attempt by '%s': vgrid name '%s'"
                    % (client_id, vgrid_name))
    print 'Content-type: text/plain\n'
    o.reply_and_exit(o.CLIENT_ERROR)

filename = private_base_dir + vgrid_name + os.sep + specified_filename

if not valid_dir_input(private_base_dir, specified_filename):
    o.out('Illegal file: %s' % specified_filename)
    logger.warning("showvgridprivatefile registered possible illegal directory traversal attempt by '%s': vgrid name '%s', file '%s'"
                    % (client_id, vgrid_name, specified_filename))
    print 'Content-type: text/plain\n'
    o.reply_and_exit(o.CLIENT_ERROR)

if not vgrid_is_owner_or_member(vgrid_name, client_id, configuration):
    o.client('Failure: You (%s) must be an owner or member of %s vgrid to access the entry page.'
              % (client_id, vgrid_name))
    print 'Content-type: text/plain\n'
    o.reply_and_exit(o.CLIENT_ERROR)

if not (os.path.isfile(filename) or os.path.isdir(filename)):
    o.out("%s: No such file in private section of '%s' vgrid"
           % (specified_filename, vgrid_name))
    print 'Content-type: text/plain\n'
    o.reply_and_exit(o.CLIENT_ERROR)

if os.path.isdir(filename):
    print ('''Content-type: text/html

<html>
 <head>
  <title>%(name)s: directory index of %(file)s
  </title>
<!-- <link rel="stylesheet" type="text/css" href="/images/default.css" media="screen"/> -->
<script type="text/javascript" src="/images/js/jquery-1.3.2.min.js"></script>
<script type="text/javascript" src="/images/js/jquery.tablesorter.js"></script>

<style type="text/css">
table {
  background: #eef;
  color: #000;
  margin-right: auto;
  margin-left: auto;
  text-align: left;
  border: 1px solid #000;
}
// tablesorter...
#filetable .header { 
    background-image: url('/images/icons/small.gif'); 
    cursor: pointer; 
    font-weight: bold; 
    background-repeat: no-repeat; 
    background-position: center left; 
    padding-left: 20px; 
    border-right: 1px solid #dad9c7; 
    margin-left: -1px; 		
} 
#filetable .headerSortDown{ 
    background-image: url('/images/icons/asc.gif'); 
    background-repeat: no-repeat; 
    background-color: #3399FF; 
}
#filetable .headerSortUp { 
    background-image: url('/images/icons/desc.gif'); 
    background-repeat: no-repeat; 
    background-color: #3399FF; 
}
.odd {
  background-color: white;
}
.even {
  background-color: #ccc;
}
.sortkey { display:none; }
</style>

<script type="text/javascript" >

$(document).ready(function() {
          var getsortkey = function(contents) {
              var key = $(contents).find(".sortkey").text();
              if (key == null) {
                   key = $(contents).html();
              }
              return key;
          }
          $("#filetable").tablesorter({widgets: ["zebra"],
                                        sortList: [[0,0],[1,0]],
                                        textExtraction: getsortkey
                                       });
});
</script>

  <body>
  <div style="text-align:center">
  <h3>%(name)s: directory index of %(file)s</h3>
  </div>
  <div style="text-align:center;margin-left:100px;margin-right:100px">
    <table id="filetable">
     <thead>
      <th style="text-align:left"><!-- symbol --></th>
      <th style="text-align:left">Name</th>
      <th style="width:120px; text-align:right">Size</th>
      <th style="width:200px; text-align:left">Last Modified</th>
     </thead>
     <tbody>
''' % {'name':vgrid_name, 'file':specified_filename})

    # always there: link to upper level
    print '''
      <tr><td><img src="/images/icons/arrow_redo.png">
          <td><a href="%s?vgrid_name=%s&file=%s">
                 Up to higher level directory</a>
          <td><td></tr><tr/>
''' % (os.path.basename(sys.argv[0]),
       vgrid_name,os.path.dirname(specified_filename))


    # read and sort file names
    contents = os.listdir(filename)
    contents.sort()

    # recognising some suffixes
    html = re.compile("^.*(html|htm)$",re.I)
    pic  = re.compile("^.*(jpg|gif|png|ppm)$",re.I)

    for f in contents:
        # for file in dir: get info, print it...
        path = os.path.join(filename, f)
        link = "%s?vgrid_name=%s&file=%s" % \
               (os.path.basename(sys.argv[0]),
                vgrid_name, os.path.join(specified_filename,f))
        info = os.stat(path)
        size = scale_bytes(info.st_size)
        #size = str(info.st_size)
        key  = 'file:' + f
        date = time.strftime("%Y-%m-%d %H:%M:%S",
                             time.localtime(info.st_mtime))
        if os.path.isdir(path):
            type = 'directory'
            key  = 'dir:' + f
            size = '-'
        elif html.match(f):
            type = 'html'
        elif pic.match(f):
            type = 'picture'
        else:
            type = 'file'

        print '''
      <tr><td><img src="/images/icons/%s.png">
              <div class="sortkey">%s</div>
          <td><div class="sortkey">%s</div><a href="%s">%s</a>
      <td style="text-align:right"><div class="sortkey">%s</div>%s
      <td><div class="sortkey">%s</div>%s</tr>
''' % (type, key, f, link, f, size[-2:] + size, size, date, date)

    print ("\n</div>\n  </body>\n</html>\n")
    sys.exit(0)

# do not use CGIOutput if everything is ok, since we do not want a 0 (return code) on the first line

try:

    # determine mime type of file to serve. This is done by calling
    # the "file" command, with apache's magic file (option -m). -b for
    # brief output.
    # TODO: hard-coded paths to "file" and "magic"

    cmd = ['/usr/bin/file', '-b', \
           '-m', '/etc/httpd/conf/magic', filename]
    file_p = subprocess.Popen(cmd,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    (out,err) = file_p.communicate()

    if err:
        # raise Exception(str(err))
        # default to html (behaviour before this change)
        out = 'text/html\n'

    # mangle output in case of ascii text (file outputs "ascii english
    # text", "utf-8 unicode text" and such instead of a mime string)

    if re.search('(ascii|unicode).*text', out, re.I):

        out = 'text/plain\n' # ignore charset, automatic in most browsers

    # returned value already contains the newlines we need
    print "Content-Type: " + out

    file = open(filename, 'r')

    print str(file.read())
    file.close()
except Exception, e:
    o.out("Error reading or printing file '%s' from private section of vgrid '%s'"
           % (specified_filename, vgrid_name), str(e))
    #debug
    o.out("%s" % e)
    print 'Content-type: text/plain\n'
    o.reply_and_exit(o.ERROR)

# o.reply_and_exit(o.OK)
