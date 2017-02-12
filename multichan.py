#!/usr/bin/python

__module_name__ = "MultiChan"
__module_version__ = "1.0"
__module_description__ = "Monitor and interact with multiple channels"

__module_author__ = 'mickers'
__module_inspiration__ = 'sebastian'
__module_gordan_ramsey__ = 'zippy'

import hexchat

MULTICHAN_TAB = '$multichan'
LOCAL_NICK = hexchat.get_info('nick')
CHAN_COLORS = {}
IGNORE_PREFS = "mc_ignore"

# HELPER FUNCTIONS

# i could probably use globals to avoid running this on every hook
# but no one is calling me out yet and im not experiencing severe
# performance kicks
def find_multichan_context():
    context = hexchat.find_context(channel=MULTICHAN_TAB)
    if not context:
        hexchat.command('QUERY -nofocus %s' % (MULTICHAN_TAB))
        context = hexchat.find_context(channel=MULTICHAN_TAB)
    return context

# just like above, this probably shouldnt get called on every hook.
# i'm not entirely sure another way to handle a new channel getting
# joined though
# actually i can create a hook for channel joins, duh
def assign_colors():
    CHAN_COLORS[LOCAL_NICK] = '\00301' # for our messages
    channels = hexchat.get_list('channels')
    index = 3
    for chan in channels:
        try:
            chan.channel[0].startswith('#')
        except (IndexError): # happens after a kick
            continue
        if chan.channel not in CHAN_COLORS.keys():
            if chan.channel[0].startswith('#'):
                while True:
                    if len(str(index)) == 1:
                        color = '0' + str(index)
                    else:
                        color = str(index)
                    color_string = '\003' + color
                    if color_string not in CHAN_COLORS.values():
                        CHAN_COLORS[chan.channel] = color_string
                        break
                    else:
                        index += 1

def in_ignores(chan, nick):
    ignore_prefs = hexchat.get_pluginpref(IGNORE_PREFS)
    if not ignore_prefs:
        return False
    ignored_list = ignore_prefs.split(' ')
    ignored_matches = [chan, nick, '%s/%s' % (chan, nick)]
    for ignored in ignored_list:
        for matched in ignored_matches:
            if ignored == matched:
                return True
    return False

# FUNCTIONS FOR CREATING STRINGS TO SEND TO CLIENT

def form_response(context, word, word_eol):
    try:
        response = {}
        nick = word[0].split('!')[0].split(':')[1]
        chan = word[2]
        if in_ignores(chan, nick):
            return None
        msg = word_eol[3][1:]
        if 'ACTION' in msg:
            left_indent = '{}{}/{}'.format(CHAN_COLORS[chan], chan, '*')
            right_indent = '{} {}'.format(nick, msg[1:-1].replace("ACTION ", ""))
        else:
            left_indent = '{}{}/{}'.format(CHAN_COLORS[chan], chan, nick)
            right_indent = msg
        if LOCAL_NICK in msg:
            context.command('GUI COLOR 3')
            response['left'] = '\002\035{}'.format(left_indent)
            response['right'] = '\002\035{}'.format(right_indent)
        else:
            context.command('GUI COLOR 2')
            response['left'] = '{}'.format(left_indent)
            response['right'] = '{}'.format(right_indent)
        return response
    except (IndexError, KeyError): # no msg was there
        return None

def form_usermsg(channel, message):
    try:
        response = {}
        left_indent = '{}{}/{}'.format(CHAN_COLORS[LOCAL_NICK], channel, LOCAL_NICK)
        right_indent = '{}{}'.format(CHAN_COLORS[LOCAL_NICK], message)
        response['left'] = '{}'.format(left_indent)
        response['right'] = '{}'.format(right_indent)
        return response
    except (IndexError, KeyError):
        return None 

# HOOK FUNCTIONS

def read_msg(word, word_eol, userdata):
    assign_colors()
    context = find_multichan_context()
    response = form_response(context, word, word_eol)
    if response:
        context.emit_print('Channel Message', response['left'], response['right'])
    return hexchat.EAT_NONE

def send_msg(word, word_eol, userdata):
    assign_colors()
    try:
        channel, message = word[1].split(" ", 1)
        if channel.startswith('#'):
            context = hexchat.find_context(channel=channel)
            if context == None:
                print("%s not found." % channel)
            else:
                context.command("say %s" % message)
                context = find_multichan_context()
                response = form_usermsg(channel, message) 
                if response:
                    context.emit_print('Channel Message', response['left'], response['right'])
            return hexchat.EAT_HEXCHAT
        else:
            return hexchat.EAT_NONE
    except ValueError:
        return hexchat.EAT_NONE

def set_ignore(word, word_eol, userdata):
    context = hexchat.get_context()
    try:
        ignore_prefs = hexchat.get_pluginpref(IGNORE_PREFS)
        if not ignore_prefs:
            prefs = str(word_eol[1])
        else:
            prefs = str(ignore_prefs) + ' ' + str(word_eol[1])
        hexchat.set_pluginpref(IGNORE_PREFS, prefs)
        context.emit_print('Channel Message', 'multichan', "You are now ignoring %s" % (prefs))
        return hexchat.EAT_HEXCHAT
    except IndexError:
        context.emit_print('Channel Message', 'multichan', 'No arguments given')
        return hexchat.EAT_HEXCHAT

def unset_ignore(word, word_eol, userdata):
    context = hexchat.get_context()
    try:
        ignore_prefs = hexchat.get_pluginpref(IGNORE_PREFS)
        if not ignore_prefs:
            context.emit_print('Channel Message', 'multichan', "You aren't ignoring anyone stupid")
            return hexchat.EAT_HEXCHAT
        else:
            prefs = str(ignore_prefs).split(' ')
            new_prefs = []
            deletions = str(word_eol[1]).split(' ')
            for pref in prefs:
                for deletion in deletions:
                    if str(deletion) == str(pref):
                        pass
                    else:
                        if str(pref) not in new_prefs:
                            new_prefs.append(str(pref))
            new_ignore_prefs = ' '.join(new_prefs)
            hexchat.set_pluginpref(IGNORE_PREFS, new_ignore_prefs)
            context.emit_print('Channel Message', 'multichan', 'Unignoring %s' % (word_eol[1]))
            if new_ignore_prefs == '':
                new_ignore_prefs = 'nobody. Such a kind faggot you are.'
            context.emit_print('Channel Message', 'multichan', 'You are now ignoring %s' % (new_ignore_prefs))
            return hexchat.EAT_HEXCHAT
    except IndexError:
        context.emit_print('Channel Message', 'multichan', 'No arguments given')
        return hexchat.EAT_HEXCHAT


# HOOK INITS
hexchat.hook_server("PRIVMSG", read_msg) # this tied right into the function I already had
hexchat.hook_server("NOTICE", read_msg) # this tied right into the function I already had
hexchat.hook_print("Your Message", send_msg)
hexchat.hook_command("mc_ignore", set_ignore, help="/mc_ignore <channel|nick|channel/nick>")
hexchat.hook_command("mc_unignore", unset_ignore, help="/mc_unignore <channel|nick|channel/nick")
