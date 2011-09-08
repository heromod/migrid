#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# useradm - User administration functions
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

"""User administration functions"""

import os
import sys
import shutil
import fnmatch

from shared.base import client_id_dir, old_id_format, sandbox_resource
from shared.conf import get_configuration_object
from shared.configuration import Configuration
from shared.fileio import filter_pickled_list, filter_pickled_dict
from shared.serial import load, dump

db_name = 'MiG-users.db'
mrsl_template = '.default.mrsl'
css_template = '.default.css'
cert_field_order = [
    ('country', 'C'),
    ('state', 'ST'),
    ('locality', 'L'),
    ('organization', 'O'),
    ('organizational_unit', 'OU'),
    ('full_name', 'CN'),
    ('email', 'emailAddress'),
    ]
cert_field_map = dict(cert_field_order)


def init_user_adm():
    """Shared init function for all user administration scripts"""

    args = sys.argv[1:]
    app_dir = os.path.dirname(sys.argv[0])
    if not app_dir:
        app_dir = '.'
    db_path = os.path.join(app_dir, db_name)
    return (args, app_dir, db_path)


def fill_user(target):
    """Fill target user dictionary with all expected fields"""

    for (key, val) in cert_field_order:
        target[key] = target.get(key, '')
    return target


def fill_distinguished_name(user):
    """Fill distinguished_name field from other fields if not already set.

    Please note that MiG certificates get empty fields set to NA, so this
    is translated here, too.
    """

    if user.get('distinguished_name', ''):
        return user
    else:
        user['distinguished_name'] = ''
    for (key, val) in cert_field_order:
        setting = user.get(key, '')
        if not setting:
            setting = 'NA'
        user['distinguished_name'] += '/%s=%s' % (val, setting)
    return user


def distinguished_name_to_user(distinguished_name):
    """Build user dictionary from distinguished_name string on the form:
    /X=abc/Y=def/Z=ghi

    Please note that MiG certificates get empty fields set to NA, so this
    is translated back here, too.
    """

    user_dict = {'distinguished_name': distinguished_name}
    parts = distinguished_name.split('/')
    for field in parts:
        if not field:
            continue
        (key, val) = field.split('=', 1)
        if 'NA' == val:
            val = ''
        if not key in cert_field_map.values():
            user_dict[key] = val
        else:
            for (name, short) in cert_field_order:
                if key == short:
                    user_dict[name] = val
    return user_dict


def load_user_db(db_path):
    """Load pickled user DB"""

    return load(db_path)


def save_user_db(user_db, db_path):
    """Save pickled user DB"""

    dump(user_db, db_path)


def delete_dir(path, verbose=False):
    """Recursively remove path:
    first remove all files and subdirs, then remove dir tree.
    """

    if verbose:
        print 'removing: %s' % path
    shutil.rmtree(path)


def create_user(
    user,
    conf_path,
    db_path,
    force=False,
    verbose=False,
    ask_renew=True
    ):
    """Add user"""

    user_db = {}
    if conf_path:

        # has been checked for accessibility above...

        configuration = Configuration(conf_path)
    else:
        configuration = get_configuration_object()

    fill_distinguished_name(user)
    client_id = user['distinguished_name']
    client_dir = client_id_dir(client_id)

    renew = False

    if verbose:
        print 'User ID: %s\n' % client_id
    if os.path.exists(db_path):
        try:
            user_db = load(db_path)
            if verbose:
                print 'Loaded existing user DB from: %s' % db_path
        except Exception, err:
            if not force:
                raise Exception('Failed to load user DB!')

        if user_db.has_key(client_id):
            if ask_renew:
                renew_answer = \
                             raw_input('User DB entry already exists - renew? [Y/n] '
                                       )
                renew = not renew_answer.lower().startswith('n')
            else:
                renew = False
            if renew:
                if verbose:
                    print 'Renewing existing user'
            elif not force:
                if verbose:
                    print 'Nothing more to do for existing user'
                return

    try:
        user_db[client_id] = user
        dump(user_db, db_path)
        if verbose:
            print 'User %s was successfully added/updated in user DB!'\
                  % client_id
    except Exception, err:
        if not force:
            raise Exception('Error: Failed to add %s to user DB: %s' % \
                            (client_id, err))

    home_dir = os.path.join(configuration.user_home, client_dir)
    cache_dir = os.path.join(configuration.user_cache, client_dir)
    mrsl_dir = os.path.join(configuration.mrsl_files_dir, client_dir)
    pending_dir = os.path.join(configuration.resource_pending,
                               client_dir)
    htaccess_path = os.path.join(home_dir, '.htaccess')
    css_path = os.path.join(home_dir, css_template)
    if not renew:
        if verbose:        
            print 'Creating dirs and files for new user: %s' % client_id
        try:
            os.mkdir(home_dir)
        except:
            if not force:
                raise Exception('Error: could not create home dir: %s' % \
                                home_dir)
        try:
            os.mkdir(cache_dir)
        except:
            if not force:
                raise Exception('Error: could not create cache dir: %s' % \
                                cache_dir)

        try:
            os.mkdir(mrsl_dir)
        except:
            if not force:
                raise Exception('Error: could not create mrsl dir: %s' % \
                                mrsl_dir)
        try:
            os.mkdir(pending_dir)
        except:
            if not force:
                raise Exception('Error: could not create resource dir: %s' % \
                                pending_dir)
    else:

        # Allow temporary write access

        os.chmod(htaccess_path, 0644)

    # Always write htaccess to catch any updates

    try:
        filehandle = open(htaccess_path, 'w')

        # Match all known fields or require the client to come from a SID path.
        #
        # IMPORTANT:
        # The fall back to explicitly allow no client certificate is necessary
        # with apache2, where symlink target directories are checked against all
        # Directory directives and thus preventing SID links to user homes from
        # being used without a certificate, if htaccess doesn't explicitly allow
        # it.
        # As this is the required SID behaviour used to hand in job results, the
        # fallback is needed to avoid breaking all job handling.
        # With apache 1.x the symlink was not further checked and thus the
        # htaccess requirement was simply ignored from those SID paths.
        # It is *critical* that all other access to user homes are secured with
        # SID or cert requirement to prevent unauthorized access.

        access = 'SSLRequire ('
        access += '%%{SSL_CLIENT_S_DN} eq "%(distinguished_name)s"'
        access += ')\n'

        filehandle.write(access % user)
        filehandle.close()

        # try to prevent further user modification

        os.chmod(htaccess_path, 0444)
    except:
        if not force:
            raise Exception('Error: could not create htaccess file: %s' % \
                            htaccess_path)

    # Always write default css to avoid apache error log entries

    try:
        filehandle = open(css_path, 'w')
        filehandle.write(get_default_css(css_path))
        filehandle.close()
    except:
        
        if not force:
            raise Exception('Error: could not create custom css file: %s' % \
                            css_path)


def delete_user(
    user,
    conf_path,
    db_path,
    force=False,
    verbose=False,
    ):
    """Delete user"""

    user_db = {}
    if conf_path:
        configuration = Configuration(conf_path)
    else:
        configuration = get_configuration_object()

    fill_distinguished_name(user)
    client_id = user['distinguished_name']
    client_dir = client_id_dir(client_id)

    if verbose:
        print 'User ID: %s\n' % client_id

    if os.path.exists(db_path):
        try:
            user_db = load_user_db(db_path)
            if verbose:
                print 'Loaded existing user DB from: %s' % db_path
        except Exception, err:
            if not force:
                raise Exception('Failed to load user DB: %s' % err)

        if not user_db.has_key(client_id):
            if not force:
                raise Exception("Error: User DB entry '%s' doesn't exist!" % \
                                client_id)

    try:
        del user_db[client_id]
        save_user_db(user_db, db_path)
        if verbose:
            print 'User %s was successfully removed from user DB!'\
                  % client_id
    except Exception, err:
        if not force:
            raise Exception('Error: Failed to remove %s from user DB: %s'\
                            % (client_id, err))

    # Remove user dirs recursively

    for base_dir in (configuration.user_home,
                     configuration.user_cache,
                     configuration.mrsl_files_dir,
                     configuration.resource_pending):

        user_path = os.path.join(base_dir, client_dir)
        try:
            delete_dir(user_path)
        except Exception, exc:
            if not force:
                raise Exception('Error: could not remove %s: %s' % \
                                (user_path, exc))
    if verbose:
        print 'User dirs for %s was successfully removed!'\
                  % client_id


def migrate_users(
    conf_path,
    db_path,
    force=False,
    verbose=False,
    prune_dupes=False,
    ):
    """Migrate all user data for possibly old format users to new format:

    update entry in user DB
    move user_home dir and symlink
    move mrsl_files_dir dir and symlink
    move resource_pending dir and symlink
    update USER_CERT field in all jobs
    update CREATOR field in all REs
    update owner files for all owned resources
    update owner files for all owned vgrids
    update member files for all membership vgrids
    """

    user_db = {}
    if conf_path:
        configuration = Configuration(conf_path)
    else:
        configuration = get_configuration_object()

    if os.path.exists(db_path):
        try:
            user_db = load_user_db(db_path)
            if verbose:
                print 'Loaded existing user DB from: %s' % db_path
        except Exception, err:
            if not force:
                raise Exception('Failed to load user DB: %s' % err)

    targets = {}
    for (client_id, user) in user_db.items():
        fill_distinguished_name(user)
        old_id = user['full_name']
        new_id = user['distinguished_name']
        if client_id == new_id:
            if verbose:
                print 'user %s is already updated to new format' % client_id
            continue
        targets[client_id] = user

    # Make sure there are no collisions in old user IDs

    latest = {}
    for (client_id, user) in targets.items():
        old_id = user['full_name'].replace(' ', '_')
        new_id = user['distinguished_name']        
        if new_id in user_db.keys():
            if not prune_dupes:
                if not force:
                    raise Exception('Error: new ID %s already exists in user DB!' % \
                                    new_id)
            else:
                if verbose:
                    print 'Pruning old duplicate user %s from user DB' % client_id
                del user_db[client_id]
        elif old_id in latest.keys():
            if not prune_dupes:
                if not force:
                    raise Exception('Error: old ID %s is not unique in user DB!' % \
                                    old_id)
            else:
                (latest_id, latest_user) = latest[old_id]
                # expire may be int, unset or None: try with fall back
                try:
                    latest_expire = int(latest_user['expire'])
                except:
                    latest_expire = 0
                try:
                    current_expire = int(user['expire'])
                except:
                    current_expire = 0
                if latest_expire < current_expire:
                    prune_id = latest_id
                    latest[old_id] = (client_id, user)
                else:
                    prune_id = client_id
                if verbose:
                    print 'Pruning duplicate user %s from user DB' % prune_id
                del user_db[prune_id]
        else:
            latest[old_id] = (client_id, user)
    save_user_db(user_db, db_path)

    # Now update the remaining users, i.e. those in latest
    for (client_id, user) in latest.values():
        old_id = user['full_name'].replace(' ', '_')
        new_id = user['distinguished_name']        
        if verbose:
            print 'updating user %s on old format %s to new format %s' % (client_id,
                                                                          old_id,
                                                                          new_id)

        old_name = client_id_dir(old_id)
        new_name = client_id_dir(new_id)

        # Move user dirs

        for base_dir in (configuration.user_home,
                         configuration.mrsl_files_dir,
                         configuration.resource_pending):

            try:
                old_path = os.path.join(base_dir, old_name)
                new_path = os.path.join(base_dir, new_name)
                shutil.move(old_path, new_path)
            except Exception, exc:

                # os.symlink(new_path, old_path)

                if not force:
                    raise Exception('Error: could not move %s to %s: %s' % \
                                    (old_path, new_path, exc))

        mrsl_base = os.path.join(configuration.mrsl_files_dir, new_name)
        for mrsl_name in os.listdir(mrsl_base):
            try:
                mrsl_path = os.path.join(mrsl_base, mrsl_name)
                if not os.path.isfile(mrsl_path):
                    continue
                filter_pickled_dict(mrsl_path, {old_id: new_id})
            except Exception, exc:
                if not force:
                    raise Exception('Error: could not update saved mrsl user in %s: %s'\
                                    % (mrsl_path, exc))

        re_base = configuration.re_home
        for re_name in os.listdir(re_base):
            try:
                re_path = os.path.join(re_base, re_name)
                if not os.path.isfile(re_path):
                    continue
                filter_pickled_dict(re_path, {old_id: new_id})
            except Exception, exc:
                if not force:
                    raise Exception('Error: could not update RE user in %s: %s'\
                                    % (re_path, exc))

        for base_dir in (configuration.resource_home,
                         configuration.vgrid_home):
            for entry_name in os.listdir(base_dir):
                for kind in ('members', 'owners'):
                    kind_path = os.path.join(base_dir, entry_name, kind)
                    if not os.path.isfile(kind_path):
                        continue
                    try:
                        filter_pickled_list(kind_path, {old_id: new_id})
                    except Exception, exc:
                        if not force:
                            raise Exception('Error: could not update saved %s in %s: %s'\
                                            % (kind, kind_path, exc))

        # Finally update user DB now that file system was updated

        try:
            del user_db[client_id]
            user_db[new_id] = user
            save_user_db(user_db, db_path)
            if verbose:
                print 'User %s was successfully updated in user DB!'\
                      % client_id
        except Exception, err:
            if not force:
                raise Exception('Error: Failed to update %s in user DB: %s'\
                                % (client_id, err))


def fix_entities(
    conf_path,
    db_path,
    force=False,
    verbose=False,
    ):
    """Update owners/members for all resources and vgrids to use new format IDs
    where possible"""

    user_db = {}
    if conf_path:
        configuration = Configuration(conf_path)
    else:
        configuration = get_configuration_object()

    if os.path.exists(db_path):
        try:
            user_db = load_user_db(db_path)
            if verbose:
                print 'Loaded existing user DB from: %s' % db_path
        except Exception, err:
            if not force:
                raise Exception('Failed to load user DB: %s' % err)

    for (client_id, user) in user_db.items():
        fill_distinguished_name(user)
        old_id = user['full_name'].replace(' ', '_')
        new_id = user['distinguished_name']        
        if verbose:
            print 'updating user %s on old format %s to new format %s' % (client_id,
                                                                          old_id,
                                                                          new_id)

        for base_dir in (configuration.resource_home, configuration.vgrid_home):
            for entry_name in os.listdir(base_dir):
                for kind in ('members', 'owners'):
                    kind_path = os.path.join(base_dir, entry_name, kind)
                    if not os.path.isfile(kind_path):
                        continue
                    if sandbox_resource(entry_name):
                        continue
                    if verbose:
                        print 'updating %s in %s' % (client_id, kind_path)
                    try:
                        filter_pickled_list(kind_path, {old_id: new_id})
                    except Exception, exc:
                        if not force:
                            raise Exception('Error: could not update saved %s in %s: %s'\
                                            % (kind, kind_path, exc))


def default_search():
    """Default search filter to match all users"""

    search_filter = {}
    for (key, val) in cert_field_order:
        search_filter[key] = '*'
    return search_filter


def search_users(search_filter, conf_path, db_path, verbose=False):
    """Search for matching users"""

    try:
        user_db = load_user_db(db_path)
        if verbose:
            print 'Loaded existing user DB from: %s' % db_path
    except Exception, err:
        print 'Failed to load user DB: %s' % err
        return []

    hits = []
    for (uid, user_dict) in user_db.items():
        match = True
        for (key, val) in search_filter.items():
            if not fnmatch.fnmatch(str(user_dict.get(key, '')), val):
                match = False
                break
        if not match:
            continue
        hits.append((uid, user_dict))
    return hits


def get_default_mrsl(template_path):
    """Return the default mRSL template from template_path"""

    try:
        template_fd = open(template_path, 'rb')
        default_mrsl = template_fd.read()
        template_fd.close()
    except:

        # Use default hello grid example

        default_mrsl = \
            """::EXECUTE::
echo 'hello grid!'
echo '...each line here is executed'

::NOTIFY::
email: SETTINGS
jabber: SETTINGS

::INPUTFILES::

::OUTPUTFILES::

::EXECUTABLES::

::MEMORY::
1

::DISK::
1

::CPUTIME::
30

::RUNTIMEENVIRONMENT::

"""
    return default_mrsl


def get_default_css(template_path):
    """Return the default css template template_path"""

    try:
        template_fd = open(template_path, 'rb')
        default_css = template_fd.read()
        template_fd.close()
    except:

        # Use default style - i.e. do not override anything

        default_css = '/* No changes - use default */'

    return default_css

