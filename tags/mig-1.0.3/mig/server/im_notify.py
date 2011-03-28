#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# im_notify - IM notifier daemon
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

# This module was inspired by an example program by Joel Rosdahl with the
# following license header:
# Example program using irclib.py.
# # This program is free without restrictions; do anything you like with
# it.
# Joel Rosdahl <joel@rosdahl.net>


# MiG: This script makes it easy to interact with a bitlbee irc server
# Call the send_msg function to send a message to an IM user
# TODO: better online/offline detection and handling?

"""IM daemon actually passing requested messages to a suitable
notification handler: At the moment this is an IRC server with
multiprotocol transports.
"""

import sys
import time
import thread
import datetime
import irclib
import os

from shared.conf import get_configuration_object

nick_counter = 1
getting_buddy_list = False
protocol_online_dict = {
    'jabber': False,
    'msn': False,
    'yahoo': False,
    'icq': False,
    'aol': False,
    }
nick_and_id_dict = {}


def send_msg(
    connection,
    dest,
    im_network,
    msg,
    ):
    """Send IM request through connection"""

    print 'send msg called'
    global getting_buddy_list
    global nick_counter
    global latest_contact_online
    global protocol_online_dict
    global nick_and_id_dict
    dest = dest.lower()
    # try going online
    got_online = False
    for _ in range(30):
        if not protocol_online_dict[im_network]:
            print 'waiting for protocol %s to get online (status for all protocols: %s)'\
                  % (im_network, protocol_online_dict)
            time.sleep(2)
        else:
            got_online = True
            break

    if not got_online:
        raise Exception("gave up waiting to get online")

    # Fetch buddy list and let any exceptions pass to caller
    
    getting_buddy_list = True
    got_buddy_list = False
    nick_and_id_dict = {}
    for _ in range(3):
        if not getting_buddy_list:
            got_buddy_list = True
            break
        connection.privmsg('root', 'blist all')
        for _ in range(30):
            if not getting_buddy_list:
                break
            print 'waiting while buddy list is generated'
            time.sleep(2)
            
    if not got_buddy_list:
        raise Exception("gave up waiting for buddy list")

    replaced_im_network = im_network
    if replaced_im_network == 'aol':
        dest += '@login.oscar.aol.com'
        replaced_im_network = 'osc'
    elif replaced_im_network == 'icq':
        dest += '@login.icq.com'
        replaced_im_network = 'osc'
    if im_network == 'yahoo':
        if not dest.endswith('@yahoo'):
            dest += '@yahoo'
    print 'looking for %s_%s in %s' % (replaced_im_network, dest,
            nick_and_id_dict)
    if nick_and_id_dict.has_key('%s_%s' % (replaced_im_network, dest)):

        # nick was found in buddy dict. Get the nickname.

        id_dict = nick_and_id_dict['%s_%s' % (replaced_im_network,
                                   dest)]
        nickname = id_dict['nick']
    else:

        # nick was not found in buddy dict, add user

        print 'account %s_%s not found in buddy list, adding..'\
             % (im_network, dest)
        account_number = get_account_number(im_network)

        # find highest "integer" nick

        for ele in nick_and_id_dict.keys():
            dict = nick_and_id_dict[ele]
            try:
                if int(dict['nick']) > nick_counter:
                    print 'found: %s' % int(dict['nick'])
                    nick_counter = int(dict['nick'])
            except Exception:

                # not integer? doesnt matter, we're looking for a unique id
                # and the highest id+1 should be unique even though some contacts
                # have a non-integer nickname

                pass
        
        nick_counter += 1
        nickname = 'nick%s' % nick_counter

        # give contact a second to get online

        time.sleep(3)

        # add contact

        print 'add %s %s %s' % (account_number, dest, nickname)
        connection.privmsg('root', 'add %s %s %s' % (account_number,
                           dest, nickname))

    # actually send the message

    for m in msg.split('<BR>'):
        connection.privmsg(nickname, m)

        # sleep a bit to keep messages in correct order

        time.sleep(0.3)


def on_connect(connection, event):
    print 'on_connect'
    if irclib.is_channel(target):
        connection.join(target)
    else:
        print 'target should be a channel!'


def get_account_number(im_network):

    # TODO: automatically get account numbers by calling and parsing an "account list" call

    if im_network == 'msn':
        return 0
    elif im_network == 'jabber':
        return 4
    elif im_network == 'yahoo':
        return 1
    elif im_network == 'icq':
        return 2
    elif im_network == 'aol':
        return 3


def on_privmsg(connection, event):
    global protocol_online_dict
    global nick_and_id_dict

    if event.source() != 'root!root@%s' % server:

        # message should never be accepted if it is not sent by "root"

        return

    recvd = event.arguments()[0]
    print '%s' % recvd
    recvd_split = recvd.split()

    if recvd == 'Password accepted':
        pass
    elif recvd.startswith('msn - Logging in: Logged in'):
        protocol_online_dict['msn'] = True
    elif recvd.startswith('jabber - Logging in: Logged in'):
        protocol_online_dict['jabber'] = True
    elif recvd.startswith('YAHOO - Logged in'):
        protocol_online_dict['yahoo'] = True
    elif recvd.startswith('ICQ(275655718) - Logged in'):
        protocol_online_dict['icq'] = True
    elif recvd.startswith('TOC(migdaemon) - Logged in'):
        protocol_online_dict['aol'] = True
    elif len(recvd_split) >= 4 and recvd_split[1].find('@') >= 0:

        # "blist all" reply. Create a small dict containing info about this single contact
        # TODO: make the if check more specific to be sure wrong messages are never accepted
        # recvd_split[2] is on the form: jabber(mig_daemon@jab

        im_network_tmp_split = recvd_split[2].split('(')  # rstrip(")").lstrip("(").lower() # (YAHOO) -> yahoo
        im_network = im_network_tmp_split[0]
        if im_network.startswith('osc'):
            im_network = 'osc'
        im_id = recvd_split[1]  # henrik_karlsen@hotmail.com
        id_dict = {}
        id_dict['nick'] = recvd_split[0]  # henrik_karlsen
        id_dict['status'] = recvd_split[3]  # (Online) (verify format)

        # unique id is im_network_im_id, eg. msn_henrik_karlsen@hotmail.com

        nick_and_id_dict['%s_%s' % (im_network, im_id.lower())] = \
            id_dict
        print 'new dict entry: %s_%s' % (im_network, im_id.lower())
    elif len(recvd_split) > 2:

        if recvd_split[1] == 'buddies':

            # end of buddy list

            global getting_buddy_list
            getting_buddy_list = False
            print 'buddy list end..'
    else:
        print 'Unknown message: %s' % recvd


def on_pubmsg(connection, event):
    print 'pubmsg: %s' % event.arguments()[0]


def on_join(connection, event):

    # someone has entered the channel (might be ourselves)

    if irclib.nm_to_n(event.source()) == nickname:

        # login to bitlbee

        login_msg = 'identify %s' % bitlbee_password
        print login_msg
        connection.privmsg('root', login_msg)
    else:
        print 'someone joined channel: %s'\
             % irclib.nm_to_n(event.source())


def on_disconnect(connection, event):
    sys.exit(0)


def irc_process_forever(*args):
    irc.process_forever()


# ## MAIN ###
print '''This script should only be started by MiG admins and only on the main
MiG server. Multiple running instances - even on separate servers - results in
conflicts!

Please use dummy IM deamon in im_notify_stdout.py instead if *not* running on
main MiG server!
'''
if len(sys.argv) < 2 or sys.argv[1] != 'i_am_admin_and_on_main_mig_server':
    print '''
To start dummy deamon run:
python im_notify_stdout.py

To really start this daemon run:
python im_notify.py i_am_admin_and_on_main_mig_server
'''
    sys.exit(1)

port = 6667
server = 'im.bitlbee.org'
nickname = 'migdaemon'
target = '#bitlbee'
bitlbee_password = 'klapHaT1'
configuration = get_configuration_object()
stdin_path = configuration.im_notify_stdin
irc = None

try:
    if not os.path.exists(stdin_path):
        print 'im_notify_stdin %s does not exists, creating it with mkfifo!'
        try:
            os.mkfifo(stdin_path, mode=0600)
        except Exception, err:
            print 'Could not create missing IM stdin fifo: %s exception: %s '\
                 % (stdin_path, err)
except:
    print 'error opening IM stdin! %s' % sys.exc_info()[0]
    sys.exit(1)

keep_running = True

print 'Starting Real IM daemon - Ctrl-C to quit'

print 'Reading commands from %s' % stdin_path
try:
    im_notify_stdin = open(stdin_path, 'r')
except KeyboardInterrupt:
    keep_running = False
except Exception, err:
    print 'could not open IM stdin %s, exception: %s'\
          % (stdin_path, err)
    sys.exit(1)

while keep_running:
    try:
        if not irc:
            print 'Initialising IRC access to %s' % server
            irc = irclib.IRC()
            try:
                irc_server = irc.server().connect(server, port, nickname)
            except irclib.ServerConnectionError, exc:
                print "Could not connect to irc server: %s" % exc
                irc = None
                time.sleep(30)
                continue

            irc_server.add_global_handler('connect', on_connect)
            irc_server.add_global_handler('join', on_join)
            irc_server.add_global_handler('disconnect', on_disconnect)
            irc_server.add_global_handler('privmsg', on_privmsg)
            irc_server.add_global_handler('pubmsg', on_pubmsg)
            thread.start_new_thread(irc_process_forever, ())
            
        # Handle messages

        # Examples:
        # send_msg(irc_server, "henrik_karlsen@hotmail.com", "msn", "hej du")
        # send_msg(irc_server, "karlsen@jabbernet.dk", "jabber", "hej du")
        # send_msg(irc_server, "henrik_karlsen@hotmail.com", "msn", "hej du")
        # send_msg(irc_server, "migtestaccount@YAHOO", "yahoo", "hej du")
        # send_msg(irc_server, "8961036", "icq", "hej du")
        # send_msg(irc_server, "henrikkarlsen2@login.oscar.aol.com", "aol", "hej du")

        line = im_notify_stdin.readline()
        if line.upper().startswith('SENDMESSAGE '):

            # The received line should be on a format similar to:
            # SENDMESSAGE PROTOCOL TO MESSAGE ex:
            # SENDMESSAGE jabber account@jabber.org this is the message
            
            # split string

            split_line = line.split(' ', 3)
            if len(split_line) != 4:
                print 'received SENDMESSAGE not on correct format %s' % line
                continue

            protocol = split_line[1]
            recipient = split_line[2]
            message = split_line[3]

            print 'Sending message: protocol: %s to: %s message: %s'\
                  % (protocol, recipient, message)
            send_msg(irc_server, recipient, protocol, message)
        elif line:
            print 'unknown message received: %s' % line

        # Throttle down
        time.sleep(1)
    except KeyboardInterrupt:
        keep_running = False
    except Exception, exc:
        print 'Caught unexpected exception: %s' % exc
        irc = None
        
print 'Real IM daemon shutting down'
sys.exit(0)