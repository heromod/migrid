#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# settings - [insert a few words of module description on this line]
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
import datetime

import parser
from settingskeywords import get_keywords_dict
from shared.fileio import pickle, unpickle
from shared.useradm import client_id_dir

settings_filename = '.settings'


def parse_and_save_settings(filename, client_id, configuration):
    client_dir = client_id_dir(client_id)
    result = parser.parse(filename)
    external_dict = get_keywords_dict()

    (status, parsemsg) = parser.check_types(result, external_dict,
            configuration)

    try:
        os.remove(filename)
    except Exception, err:
        msg = 'Exception removing temporary settings file %s, %s'\
             % (filename, err)

        # should we exit because of this? o.reply_and_exit(o.ERROR)

    if not status:
        msg = 'Parse failed (typecheck) %s' % parsemsg
        return (False, msg)

    new_dict = {}

    # move parseresult to a dictionary

    for (key, value_dict) in external_dict.iteritems():
        new_dict[key] = value_dict['Value']

    new_dict['CREATOR'] = client_id
    new_dict['CREATED_TIMESTAMP'] = datetime.datetime.now()

    pickle_filename = os.path.join(configuration.user_home, client_dir,
                                   settings_filename)

    if not pickle(new_dict, pickle_filename, configuration.logger):
        msg = 'Error saving settings!'
        return (False, msg)

    # everything ok

    return (True, '')


def load_settings(client_id, configuration):
    """Load settings from pickled settings file"""

    client_dir = client_id_dir(client_id)
    settings_path = os.path.join(configuration.user_home, client_dir,
                                 settings_filename)
    settings_dict = unpickle(settings_path, configuration.logger)
    return settings_dict

