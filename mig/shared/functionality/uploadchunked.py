#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# uploadchunked - Chunked and efficient file upload back end
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

"""Chunked file upload back end"""

import os

import shared.returnvalues as returnvalues
from shared.base import client_id_dir
from shared.defaults import max_upload_files, max_upload_chunks, \
     upload_block_size, upload_tmp_dir
from shared.fileio import strip_dir, write_chunk, delete_file, move, \
     get_file_size
from shared.functional import validate_input_and_cert
from shared.handlers import correct_handler
from shared.init import initialize_main_variables
from shared.safeinput import valid_path
from shared.validstring import valid_user_path

# The input argument for fileupload files

files_field = 'files[]'
filename_field = '%sfilename' % files_field
manual_validation = [files_field, filename_field]

def signature():
    """Signature of the main function"""

    defaults = {'action': ['put'], 'current_dir': ['.'],
        }
    return ['html_form', defaults]

def extract_chunk_region(configuration):
    """Read chunk range from HTTP headers in os.environ.

    Example range declaration from os.environ:
    'HTTP_CONTENT_RANGE': 'bytes 8000000-14145972/14145973'
    """
    content_length = int(os.environ.get("CONTENT_LENGTH", -1))
    content_range = os.environ.get("HTTP_CONTENT_RANGE", '').strip()
    configuration.logger.info("found content_range: '%s'" % content_range)
    if content_range.startswith("bytes "):
        raw_range = content_range.replace("bytes ", "").split('/')[0]
        range_parts = raw_range.split('-')
        chunk_first, chunk_last = int(range_parts[0]), int(range_parts[1])
    else:
        configuration.logger.info("No valid content range found - using 0")
        if content_length > upload_block_size:
            configuration.logger.error("Should have range!\n%s" % os.environ)
        chunk_first, chunk_last = 0, -1
    return (chunk_first, chunk_last)

def parse_form_upload(user_args, client_id, configuration):
    """Parse upload file and chunk entries from user_args. Chunk limits are
    extracted from content-range http header in environment.
    """
    files, rejected = [], []

    # TMP! only support single filename and chunk for now
    #for name_index in xrange(max_upload_files):
    #    if user_args.has_key(filename_field) and \
    #           len(user_args[filename_field]) > name_index:
    for name_index in [0]:
        if user_args.has_key(filename_field):
            if isinstance(user_args[filename_field], basestring):
                filename = user_args[filename_field]
            else:
                filename = user_args[filename_field][name_index]
            configuration.logger.info('found name: %s' % filename)
        else:
            # No more files
            break
        if not filename.strip():
            continue
        try:
            filename = strip_dir(filename)
            valid_path(filename)
        except Exception, exc:
            configuration.logger.error('invalid filename: %s' % filename)
            rejected.append((filename, 'invalid filename: %s (%s)' % \
                             (filename, exc)))
            continue
        #for chunk_index in xrange(max_upload_chunks):
        #    if user_args.has_key(files_field) and \
        #           len(user_args[files_field]) > chunk_index:
        for chunk_index in [0]:
            if user_args.has_key(files_field):
                chunk = user_args[files_field][chunk_index]
            else:
                break
            configuration.logger.debug('find chunk range: %s' % filename)
            (chunk_first, chunk_last) = extract_chunk_region(configuration)
            if len(chunk) > upload_block_size:
                configuration.logger.error('skip bigger than allowed chunk')
                continue
            elif chunk_last < 0:
                chunk_last = len(chunk) - 1
            files.append((filename, (chunk, chunk_first, chunk_last)))
    return (files, rejected)

def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(client_id, op_header=False)
    logger.debug('Extracting input in %s' % op_name)
    client_dir = client_id_dir(client_id)
    status = returnvalues.OK
    defaults = signature()[1]
    
    logger.info('Extracted input in %s: %s' % (op_name,
                                               user_arguments_dict.keys()))

    # All non-file fields must be validated
    validate_args = dict([(key, user_arguments_dict.get(key, val)) for \
                         (key, val) in user_arguments_dict.items() if not key \
                          in manual_validation])
    (validate_status, accepted) = validate_input_and_cert(
        validate_args,
        defaults,
        output_objects,
        client_id,
        configuration,
        allow_rejects=False,
        )
    if not validate_status:
        logger.error('%s validation failed: %s (%s)' % \
                     (op_name, validate_status, accepted))
        return (accepted, returnvalues.CLIENT_ERROR)

    logger.debug('validated input in %s: %s' % (op_name, validate_args.keys()))

    if not correct_handler('POST'):
        output_objects.append(
            {'object_type': 'error_text', 'text'
             : 'Only accepting POST requests to prevent unintended updates'})
        return (output_objects, returnvalues.CLIENT_ERROR)

    action = accepted['action'][-1]
    current_dir = accepted.get('current_dir', ['.'])[-1]
    output_format = accepted['output_format'][-1]

    uploaded = []
    # Always include a files reply even if empty
    output_objects.append({'object_type': 'uploadfiles', 'files': uploaded})

    logger.info('parsing upload form in %s' % op_name)

    # Now parse and validate files to archive

    for name in defaults.keys():
        if user_arguments_dict.has_key(name):
            del user_arguments_dict[name]

    (upload_files, upload_rejected) = parse_form_upload(user_arguments_dict,
                                                        client_id,
                                                        configuration)
    if upload_rejected:
        logger.error('Rejecting upload with: %s' % upload_rejected)
        output_objects.append({'object_type': 'error_text', 'text'
                              : 'Errors parsing upload files: %s' % \
                               '\n '.join(["%s %s" % pair for pair in \
                                           upload_rejected])})
        for (rel_path, err) in upload_rejected:
            uploaded.append(
                {'object_type': 'uploadfile', 'name': rel_path, 'size': -1,
                 "error": err})
        return (output_objects, returnvalues.CLIENT_ERROR)
    if not upload_files:
        output_objects.append({'object_type': 'error_text', 'text'
                              : 'No files included to upload!'})
        return (output_objects, returnvalues.CLIENT_ERROR)

    logger.info('Filtered input validated with result: %s' % accepted)

    # Please note that base_dir must end in slash to avoid access to other
    # user dirs when own name is a prefix of another user name

    base_dir = os.path.abspath(os.path.join(configuration.user_home,
                               client_dir)) + os.sep
    cache_dir = os.path.join(base_dir, upload_tmp_dir) + os.sep

    if not os .path.isdir(cache_dir):
        try:
            os.makedirs(cache_dir)
        except Exception, exc:
            logger.error('%s could not create upload tmp dir %s ! (%s)'
                         % (op_name, cache_dir, exc))
            output_objects.append(
                {'object_type': 'error_text', 'text'
                 : "Problem creating temporary upload dir"})
            return (output_objects, returnvalues.SYSTEM_ERROR)

    output_objects.append({'object_type': 'header', 'text'
                          : 'Uploading file chunk(s)'})

    # Check directory traversal attempts before actual handling to avoid
    # leaking information about file system layout while allowing consistent
    # error messages

    logger.info('Looping through files: %s' % \
                ' '.join([i[0] for i in upload_files]))

    # Please refer to https://github.com/blueimp/jQuery-File-Upload/wiki/Setup
    # for details about the status reply format in the uploadfile output object
    
    if action == 'delete':
        for (rel_path, chunk_tuple) in upload_files:
            real_path = os.path.abspath(os.path.join(cache_dir, rel_path))
            if not valid_user_path(real_path, base_dir, True):
                logger.error('%s tried to %s delete restricted path %s !'
                             % (client_id, op_name, real_path))
                output_objects.append(
                    {'object_type': 'error_text', 'text'
                     : "Invalid destination (%s expands to an illegal path)" \
                     % rel_path})
                deleted = False
            else:
                deleted = delete_file(real_path, logger)
            uploaded.append({'object_type': 'uploadfile', rel_path: deleted})
        logger.info('delete done: %s' % ' '.join([i[0] for i in upload_files]))
        return (output_objects, status)
    elif action == 'status':
        for (rel_path, chunk_tuple) in upload_files:
            real_path = os.path.abspath(os.path.join(cache_dir, rel_path))
            file_entry = {'object_type': 'uploadfile', 'name': rel_path}
            if not valid_user_path(real_path, base_dir, True):
                logger.error('%s tried to %s status restricted path %s !'
                             % (client_id, op_name, real_path))
                output_objects.append(
                    {'object_type': 'error_text', 'text'
                     : "Invalid destination (%s expands to an illegal path)" \
                     % rel_path})
                file_entry.update({'size': -1, 'error': 'invalid path'})
            else:
                file_entry['size'] = get_file_size(real_path, logger)
            uploaded.append(file_entry)
        logger.info('status done: %s' % ' '.join([i[0] for i in upload_files]))
        return (output_objects, status)
    elif action == 'move':
        for (rel_path, chunk_tuple) in upload_files:
            real_path = os.path.abspath(os.path.join(cache_dir, rel_path))
            dest_path = os.path.abspath(os.path.join(base_dir, current_dir,
                                                      rel_path))
            if not valid_user_path(dest_path, base_dir, True):
                logger.error('%s tried to %s move to restricted path %s ! (%s)'
                             % (client_id, op_name, dest_path, current_dir))
                output_objects.append(
                    {'object_type': 'error_text', 'text'
                     : "Invalid destination (%s expands to an illegal path)" \
                     % current_dir})
                moved = False
            else:
                try: 
                    move(real_path, dest_path)
                    moved = True
                except Exception, exc:
                    logger.error('could not move %s to %s: %s' % (real_path,
                                                              dest_path, exc))
                    moved = False
            uploaded.append({'object_type': 'uploadfile', rel_path: moved})
        logger.info('move done: %s' % ' '.join([i[0] for i in upload_files]))
        return (output_objects, status)
    elif action != 'put':
        output_objects.append({'object_type': 'error_text', 'text'
                              : 'Invalid action: %s!' % action})
        return (output_objects, returnvalues.CLIENT_ERROR)

    # Handle actual uploads (action == 'put')
        
    for (rel_path, chunk_tuple) in upload_files:
        logger.info('handling %s chunk %s' % (rel_path, chunk_tuple[1:]))
        (chunk, offset, chunk_last) = chunk_tuple
        chunk_size = len(chunk)
        range_size = 1 + chunk_last - offset
        real_path = os.path.abspath(os.path.join(cache_dir, rel_path))

        if not valid_user_path(real_path, cache_dir, True):
            logger.warning('%s tried to %s restricted path %s ! (%s)'
                           % (client_id, op_name, real_path, rel_path))
            output_objects.append(
                {'object_type': 'error_text', 'text'
                 : "Invalid destination (%s expands to an illegal path)" % \
                 rel_path})
            return (output_objects, returnvalues.CLIENT_ERROR)

        if not os.path.isdir(os.path.dirname(real_path)):
            output_objects.append({'object_type': 'error_text', 'text'
                                   : "cannot write: no such file or directory:"
                                   " %s)" % rel_path})
            return (output_objects, returnvalues.CLIENT_ERROR)

        logger.debug('write %s chunk of size %d' % (rel_path, chunk_size))
        if chunk_size == range_size and \
               write_chunk(real_path, chunk, offset, logger, 'r+b'):
            output_objects.append({'object_type': 'text', 'text'
                                   : 'wrote chunk %s at %d' % \
                                   (chunk_tuple[1:], offset)})
            logger.info('wrote %s chunk at %s' % (real_path, chunk_tuple[1:]))
            uploaded.append(
                {'object_type': 'uploadfile', 'name': rel_path,
                 "size": os.path.getsize(real_path), "url": 
                 os.path.join("/cert_redirect", upload_tmp_dir, rel_path),
                 "deleteUrl":
                 "uploadchunked.py?output_format=%s;action=delete;%s=%s;%s=%s"
                 % (output_format, files_field, rel_path, filename_field,
                    "dummy"),
                 'deleteType': 'POST',
                 })
        else:
            logger.error('could not write %s chunk %s (%d vs %d)' % \
                         (real_path, chunk_tuple[1:], chunk_size, range_size))
            output_objects.append({'object_type': 'error_text', 'text'
                                   : 'failed to write chunk %s at %d' % \
                                   (chunk_tuple[1:], offset)})
            uploaded.append(
                {'object_type': 'uploadfile', 'name': rel_path,
                 "error": "failed to write chunk %s - try again" % \
                 (chunk_tuple[1:], )})

    logger.info('put done: %s' % ' '.join([i[0] for i in upload_files]))
    return (output_objects, status)