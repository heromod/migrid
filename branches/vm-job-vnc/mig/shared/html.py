#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# html - html helper functions
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
import sys

"""HTML formatting functions"""


def html_print(formatted_text, html=True):
    print html_add(formatted_text, html)


def html_add(formatted_text, html=True):
    """Convenience function to only append html formatting to a text
    string in html mode"""

    if html:
        return formatted_text
    else:
        return ''


def renderMenu(menu_class='navmenu', menu_items='', current_element='Unknown'):
  
  menu_lines  = '<div class="%s">' % menu_class +\
                ' <ul>'
        
  for menu_line in menu_items:
    selected = ''
    
    attr = ''
    if (menu_line.has_key('attr')):
      attr = menu_line['attr']
    if menu_line['url'].find(current_element) > -1:
      selected = ' class="selected" '+current_element
    menu_lines += '   <li %s class="%s"><a href="%s" %s>%s</a></li>' % (attr, menu_line['class'], menu_line['url'], selected, menu_line['title'])
            
  menu_lines += ' </ul>'
  menu_lines += '</div>'
  
  return menu_lines

# TODO: scripts variable is only last in var list for
# backward-compatibility


def get_cgi_html_header(
    title,
    header,
    html=True,
    scripts='',
    bodyfunctions='',
    menu=True,
    ):
    """Return the html tags to mark the beginning of a page."""

    if not html:
        return ''
    menu_lines = ''
    if menu:
        
        current_page = os.path.basename(sys.argv[0]).replace('.py', '')
        menu_items  = (
                        {
                        'class'    : 'dashboard',
                        'url'       : '/cgi-bin/dashboard.py',
                        'title'     : 'Dashboard'
                        },
                        {
                        'class'    : 'submitjob',
                        'url'       : '/cgi-bin/submitjob.py',
                        'title'     : 'Submit Job'
                        },
                        {
                        'class'    : 'files',
                        'url'       : '/cgi-bin/ls.py?flags=a',
                        'title'     : 'Files'
                        },
                        {
                        'class'    : 'jobs',
                        'url'       : '/cgi-bin/managejobs.py',
                        'title'     : 'Jobs'
                        },
                        {
                        'class'    : 'vgrids',
                        'url'       : '/cgi-bin/vgridadmin.py',
                        'title'     : 'VGrids'
                        },
                        {
                        'class'    : 'vmachines',
                        'url'       : '/cgi-bin/vmachines.py',
                        'title'     : 'VMachines'
                        },
                        {
                        'class'    : 'resources',
                        'url'       : '/cgi-bin/resadmin.py',
                        'title'     : 'Resources'
                        },
                        {
                        'class'    : 'downloads',
                        'url'       : '/cgi-bin/downloads.py',
                        'title'     : 'Downloads'
                        },
                        {
                        'class'    : 'runtimeenvs',
                        'url'       : '/cgi-bin/redb.py',
                        'title'     : 'Runtime Envs'
                        },
                        {
                        'class'    : 'settings',
                        'url'       : '/cgi-bin/settings.py',
                        'title'     : 'Settings'
                        },
                        {
                        'class'    : 'shell',
                        'url'       : '/cgi-bin/shell.py',
                        'title'     : 'Shell'
                        },
                        
        )
        
        menu_lines = renderMenu('navmenu', menu_items, current_page)
        
        """'<div class="navmenu">' +\
                     '<ul>'
        
        for menu_line in menu_items:
            selected = ''
            if menu_line['url'].find(current_page) > -1:
                selected = ' class="selected" '+current_page
            menu_lines += '<li class="%s"><a href="%s" %s>%s</a></li>' % (menu_line['class'], menu_line['url'], selected, menu_line['title'])
            
        menu_lines += '</ul>'
        menu_lines += '</div>'"""

    return '''<?xml version="1.0" encoding="iso-8859-1"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
<link rel="stylesheet" type="text/css" href="/images/migcss.css" media="screen"/>
<link rel="icon" type="image/vnd.microsoft.icon" href="/images/favicon.ico">
<title>
 %s
 </title>
 %s
 <SCRIPT TYPE="text/javascript" SRC="/images/backlink.js"></SCRIPT>
 </head>
<body %s>
<div id="toplogo">Minimum Intrusion Grid</div>
<!--<div id="toplogo"><div>&nbsp;</div></div>-->
%s
<div id="migheader">
%s
</div>
<div id="content">
    '''\
         % (title, scripts, bodyfunctions, menu_lines, header)


def get_cgi_html_footer(footer='', html=True):
    """Return the html tags to mark the end of a page. If a footer string
    is supplied it is inserted at the bottom of the page.
    """

    if not html:
        return ''

    out = footer
    out += \
        '''
        
<div id="credits">
Copyright 2009 - <a href="http://www.migrid.org">The MiG project</a>
</div>
</body>
</html>
'''
    return out


# Wrappers used during transition phase - replace with
# get_cgi_html_X contents when cgi-scripts all use add_cgi_html_X
# instead of if printhtml: print get_cgi_html_X


def add_cgi_html_header(
    title,
    header,
    html=True,
    scripts='',
    ):

    if html:
        print get_cgi_html_header(title, header, html, scripts)


def add_cgi_html_footer(footer, html=True):
    if html:
        print get_cgi_html_footer(footer, html)


def html_encode(raw_string):
    result = raw_string.replace("'", '&#039;')
    result = result.replace('"', '&#034;')
    return result


# TODO: remove these backwards compatibility names

addMiGhtmlHeader = add_cgi_html_header
addMiGhtmlFooter = add_cgi_html_footer
htmlEncode = html_encode