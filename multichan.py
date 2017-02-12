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

def form_response(context, word, word_eol):
    try:
        response = {}
        nick = word[0].split('!')[0].split(':')[1]
        chan = word[2]
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

hexchat.hook_server("PRIVMSG", read_msg) # this tied right into the function I already had
hexchat.hook_print("Your Message", send_msg)
