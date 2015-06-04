#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# freezefunctions - freeze archive helper functions
# Copyright (C) 2003-2014  The MiG Project lead by Brian Vinter
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

"""Freeze archive functions"""

import base64
import datetime
import os
import time

from shared.defaults import freeze_meta_filename, wwwpublic_alias, \
     public_archive_dir, public_archive_index
from shared.fileio import md5sum_file, write_file, copy_file, copy_rec, move_file, \
     move_rec, remove_rec, makedirs_rec, make_symlink, make_temp_dir
from shared.html import get_cgi_html_preamble, get_cgi_html_footer
from shared.serial import load, dump

freeze_flavors = {
    'freeze': {'adminfreeze_title': 'Freeze Archive',
               'createfreeze_title': 'Create Frozen Archive',
               'showfreeze_title': 'Show Frozen Archive Details',
               'deletefreeze_title': 'Delete Frozen Archive'},
    'phd': {'adminfreeze_title': 'PhD Thesis Archival',
            'createfreeze_title': 'Create Thesis Archive',
            'showfreeze_title': 'Show Archived Thesis Details',
            'deletefreeze_title': 'Delete Archived Thesis'}
    }

def public_freeze_id(freeze_dict):
    """Translate internal freeze_id to a public identifier used when publishing
    frozen archives. In the future we may want to map to a global DOI but we
    just map to to url safe base64 version of the freeze ID for now.
    """
    return base64.urlsafe_b64encode(freeze_dict['ID'])

def published_dir(freeze_dict, configuration):
    """Translate internal freeze_id to a published archive dir"""
    return os.path.join(configuration.wwwpublic, public_archive_dir,
                        public_freeze_id(freeze_dict))

def published_url(freeze_dict, configuration):
    """Translate internal freeze_id to a published archive URL"""
    return os.path.join(configuration.migserver_http_url, 'public',
                        public_archive_dir, public_freeze_id(freeze_dict),
                        public_archive_index)

def build_freezeitem_object(configuration, freeze_dict):
    """Build a frozen archive object based on input freeze_dict"""

    freeze_files = []
    for file_item in freeze_dict['FILES']:
        freeze_files.append({
                'object_type': 'frozenfile',
                'name': file_item['name'],
                'size': file_item['size'],
                'md5sum': file_item['md5sum'],
                })
    freeze_obj = {
        'object_type': 'frozenarchive',
        'id': freeze_dict['ID'],
        'name': freeze_dict['NAME'],
        'description': freeze_dict['DESCRIPTION'],
        'creator': freeze_dict['CREATOR'],
        'created': time.asctime(freeze_dict['CREATED_TIMESTAMP'
                                ].timetuple()),
        'frozenfiles': freeze_files,
        }
    for field in ('author', 'department', 'organization', 'publish',
                  'publish_url', 'flavor'):
        if not freeze_dict.get(field.upper(), None) is None:
            freeze_obj[field] = freeze_dict[field.upper()]
    return freeze_obj

def list_frozen_archives(configuration, client_id):
    """Find all frozen_archives owned by user"""
    logger = configuration.logger
    frozen_list = []
    dir_content = []

    try:
        dir_content = os.listdir(configuration.freeze_home)
    except Exception:
        if not makedirs_rec(configuration.freeze_home, configuration):
            logger.error(
                'freezefunctions.py: not able to create directory %s'
                % configuration.freeze_home)
            return (False, "archive setup is broken")
        dir_content = []

    for entry in dir_content:

        # Skip dot files/dirs

        if entry.startswith('.'):
            continue
        if is_frozen_archive(entry, configuration):

            # entry is a frozen archive - check ownership

            (meta_status, meta_out) = get_frozen_meta(entry, configuration)
            if meta_status and meta_out['CREATOR'] == client_id:
                frozen_list.append(entry)
        else:
            logger.warning(
                '%s in %s is not a directory, move it?'
                % (entry, configuration.freeze_home))
    return (True, frozen_list)

def is_frozen_archive(freeze_id, configuration):
    """Check that freeze_id is an existing frozen archive"""
    freeze_path = os.path.join(configuration.freeze_home, freeze_id)
    if os.path.isdir(freeze_path) and \
           os.path.isfile(os.path.join(freeze_path, freeze_meta_filename)):
        return True
    else:
        return False

def get_frozen_meta(freeze_id, configuration):
    """Helper to fetch dictionary of metadata for a frozen archive"""
    frozen_path = os.path.join(configuration.freeze_home, freeze_id,
                               freeze_meta_filename)
    freeze_dict = load(frozen_path)
    if not freeze_dict:
        return (False, 'Could not open metadata for frozen archive %s' % \
                freeze_id)
    else:
        return (True, freeze_dict)

def get_frozen_files(freeze_id, configuration):
    """Helper to list names and stats for files in a frozen archive"""
    frozen_dir = os.path.join(configuration.freeze_home, freeze_id)
    if not os.path.isdir(frozen_dir):
        return (False, 'Could not open frozen archive %s' % freeze_id)
    files = []
    for (root, _, filenames) in os.walk(frozen_dir):
        for name in filenames:
            if name in [freeze_meta_filename]:
                continue
            frozen_path = os.path.join(root, name)
            rel_path = os.path.join(root.replace(frozen_dir, '', 1), name)
            files.append({'name': rel_path,
                          'timestamp': os.path.getctime(frozen_path),
                          'size': os.path.getsize(frozen_path),
                          # Checksum first 32 MB of files
                          'md5sum': md5sum_file(frozen_path)})
    return (True, files)

def get_frozen_archive(freeze_id, configuration):
    """Helper to extract all details for a frozen archive"""
    if not is_frozen_archive(freeze_id, configuration):
        return (False, 'no such frozen archive id: %s' % freeze_id)
    (meta_status, meta_out) = get_frozen_meta(freeze_id, configuration)
    if not meta_status:
        return (False, 'failed to extract meta data for %s' % freeze_id)
    (files_status, files_out) = get_frozen_files(freeze_id, configuration)
    if not files_status:
        return (False, 'failed to extract files for %s' % freeze_id)
    freeze_dict = {'ID': freeze_id, 'FILES': files_out}
    freeze_dict.update(meta_out)
    return (True, freeze_dict)

def create_frozen_archive(freeze_meta, freeze_copy, freeze_move,
                          freeze_upload, client_id, configuration):
    """Create a new frozen archive with meta data fields and provided
    freeze_copy files from user home, freeze_move from temporary upload dir
    and freeze_upload files from form.
    """
    logger = configuration.logger
    try:
        frozen_dir = make_temp_dir(prefix='archive-',
                                   dir=configuration.freeze_home)
    except Exception, err:
        return (False, 'Error preparing new frozen archive: %s' % err)

    freeze_id = os.path.basename(frozen_dir)
    
    freeze_dict = {
        'ID': freeze_id,
        'CREATED_TIMESTAMP': datetime.datetime.now(),
        'CREATOR': client_id,
        }
    freeze_dict.update(freeze_meta)
    if freeze_meta['PUBLISH']:
        real_pub_dir = published_dir(freeze_dict, configuration)
        real_pub_index = os.path.join(real_pub_dir, public_archive_index)
        freeze_dict['PUBLISH_URL'] = published_url(freeze_dict, configuration)
    frozen_files = []
    logger.info("create_frozen_archive: save meta for %s" % freeze_id)
    try:
        dump(freeze_dict, os.path.join(frozen_dir, freeze_meta_filename))
    except Exception, err:
        logger.error("create_frozen_archive: failed: %s" % err)
        remove_rec(frozen_dir, configuration)
        return (False, 'Error writing frozen archive info: %s' % err)

    logger.info("create_frozen_archive: copy %s for %s" % \
                              (freeze_copy, freeze_id))
    for (real_source, rel_dst) in freeze_copy:
        freeze_path = os.path.join(frozen_dir, rel_dst)
        frozen_files.append(rel_dst)
        logger.debug("create_frozen_archive: copy %s" % freeze_path)
        if os.path.isdir(real_source):
            (status, msg) = copy_rec(real_source, freeze_path, configuration)
            if not status:
                logger.error("create_frozen_archive: failed: %s" % msg)
                remove_rec(frozen_dir, configuration)
                return (False, 'Error writing frozen archive')
        else:
            (status, msg) = copy_file(real_source, freeze_path, configuration)
            if not status:
                logger.error("create_frozen_archive: failed: %s" % msg)
                remove_rec(frozen_dir, configuration)
                return (False, 'Error writing frozen archive')
    logger.info("create_frozen_archive: move %s for %s" % \
                              (freeze_move, freeze_id))
    for (real_source, rel_dst) in freeze_move:
        # Strip relative dir from move targets
        freeze_path = os.path.join(frozen_dir, os.path.basename(rel_dst))
        frozen_files.append(os.path.basename(rel_dst))
        logger.debug("create_frozen_archive: move %s" % freeze_path)
        if os.path.isdir(real_source):
            (status, msg) = move_rec(real_source, freeze_path, configuration)
            if not status:
                logger.error("create_frozen_archive: failed: %s" % msg)
                remove_rec(frozen_dir, configuration)
                return (False, 'Error writing frozen archive')
        else:
            (status, msg) = move_file(real_source, freeze_path, configuration)
            if not status:
                logger.error("create_frozen_archive: failed: %s" % msg)
                remove_rec(frozen_dir, configuration)
                return (False, 'Error writing frozen archive')
    logger.info("create_frozen_archive: save %s for %s" % \
                              ([i[0] for i in freeze_upload], freeze_id))
    for (filename, contents) in freeze_upload:
        freeze_path = os.path.join(frozen_dir, filename)
        frozen_files.append(filename)
        logger.debug("create_frozen_archive: write %s" % freeze_path)
        if not write_file(contents, freeze_path, logger):
            logger.error("create_frozen_archive: failed: %s" % err)
            remove_rec(frozen_dir, configuration)
            return (False, 'Error writing frozen archive')

    if freeze_dict['PUBLISH']:
        published_id = public_freeze_id(freeze_dict)
        public_meta = [('CREATOR', 'Owner'), ('NAME', 'Name'),
                       ('DESCRIPTION', 'Description'),
                       ('CREATED_TIMESTAMP', 'Date')]
        contents = get_cgi_html_preamble(configuration, "Public Archive: %s" % \
                                         published_id, "", widgets=False)
        contents += """
<body class='fixedwidth'>
<div id='topspace'>
</div>
<div class='fixedwidth' id='toplogo'>
<img src='%s/banner-logo.jpg' id='logoimage'
     class='fixedwidth' alt='site logo'/>
</div>

<div class='contentblock fixedwidth' id='nomenu'>
<div id='migheader'>
</div>
<div class='fixedwidth' id='content'>
<div>
<h1 class='fixedwidth'>Public Archive</h1>
This is the public archive with unique ID %s .<br/>
The user supplied meta data and files are available below.

<h2>Archive Meta Data</h2>
        """ % (configuration.site_skin_base, published_id)
        for (meta_key, meta_label) in public_meta:
            meta_value = freeze_dict.get(meta_key, '')
            if meta_value:
                contents += """%s: %s<br/>
""" % (meta_label, meta_value)
        contents += """
<h2>Archive Files</h2>
        """
        for rel_path in frozen_files:
            contents += """<a href='%s'>%s</a><br/>
""" % (rel_path, rel_path)
        contents += """
</div>
%s
        """ % get_cgi_html_footer(configuration, widgets=False)
        if not make_symlink(frozen_dir, real_pub_dir, logger) or \
               not write_file(contents, real_pub_index, configuration.logger):
            logger.error("create_frozen_archive: publish failed")
            remove_rec(frozen_dir, configuration)
            return (False, 'Error publishing frozen archive')
    return (True, freeze_id)

def delete_frozen_archive(freeze_id, configuration):
    """Delete an existing frozen archive without checking ownership or
    persistance of frozen archives.
    """
    frozen_dir = os.path.join(configuration.freeze_home, freeze_id)
    if remove_rec(frozen_dir, configuration):
        return (True, '')
    else:
        return (False, 'Error deleting frozen archive "%s"' % freeze_id)


