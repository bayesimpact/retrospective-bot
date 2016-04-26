from flask import abort, current_app, request, Response
from . import gloss as app
from . import db
from itertools import groupby
from models import Sprint, RetrospectiveItem
from sqlalchemy import func, distinct, sql
from re import compile, match, search, sub, UNICODE
from requests import post
from datetime import datetime
import json
import random

GOOD_CMDS = (u'good',)
BAD_CMDS = (u'bad',)
TRY_CMDS = (u'try',)
CATEGORY_CMDS = GOOD_CMDS + BAD_CMDS + TRY_CMDS
NEW_CMDS = (u'new',)
LIST_CMDS = (u'list',)
HELP_CMDS = (u'help', u'?')
RESET_CMDS = (u'reset',)
ALL_CMDS = CATEGORY_CMDS + NEW_CMDS + LIST_CMDS + HELP_CMDS + RESET_CMDS

BOT_NAME = u'Retrospective Bot'


def get_command_action_and_params(command_text):
    ''' Parse the passed string for a command action and parameters
    '''
    command_components = command_text.split(' ')
    command_action = command_components[0].lower()
    command_params = u' '.join(command_components[1:])
    return command_action, command_params

def add_retrospective_item_and_get_response(slash_command, category, text, user_name):
    ''' Set the retrospective item for the passed parameters and return the approriate responses
    '''
    # reject attempts to set reserved terms
    if text.lower() in ALL_CMDS:
        return u'Sorry, but *{}* can\'t save *{}* because it\'s a reserved term.'.format(BOT_NAME, text)

    sprint = Sprint.get_current_sprint(user_name)
    category = category.lower()

    # save the item in the database
    retrospective_item = RetrospectiveItem(
        sprint_id=sprint.id,
        category=category,
        text=text,
        user_name=user_name)

    try:
        db.session.add(retrospective_item)
        db.session.commit()
    except Exception as e:
        return u'Sorry, but *{}* was unable to save that retrospective item: {}, {}.'.format(BOT_NAME, e.message, e.args)

    response = u'New retrospective item for *{}*:'.format(sprint)
    attachments = get_retrospective_items_attachments([retrospective_item])
    return (response, attachments)

def get_retrospective_items_response(slash_command, user_name):
    ''' Get all the retrospective item for the current sprint
    '''
    sprint = Sprint.get_current_sprint(user_name)
    items = RetrospectiveItem.get_retrospective_items_for_sprint(sprint)
    if items.count() == 0:
        return 'No retrospective items yet for *{}*.'.format(sprint)

    response = u'Retrospective items for *{}*:'.format(sprint)
    attachments = get_retrospective_items_attachments(items)
    return (response, attachments)

def get_retrospective_items_attachments(retrospective_items):
    ''' Return Slack message attachements to show the given retrospective items
    '''
    retrospective_items = sorted(retrospective_items, key=lambda i: i.category)
    items_by_category = groupby(retrospective_items, lambda i: i.category)
    colors_by_category = {'good': 'good', 'bad': 'danger', 'try': 'warning'}
    attachments = [
        {
            'title': category.capitalize(),
            'text': '\n'.join([item.text for item in items_in_category]),
            'color': colors_by_category[category],
        }
        for category, items_in_category in items_by_category
    ]
    return attachments

def start_new_sprint(slash_command, user_name):
    ''' Start a new sprint with a new empty retrospective item list.
    '''
    try:
        sprint = Sprint.create_new_sprint(user_name)
    except Exception as e:
        return u'Sorry, but *{}* was unable to create new sprint: {}, {}.'.format(BOT_NAME, e.message, e.args)

    return u'New sprint: *{}*.'.format(sprint)

def reset_current_sprint(slash_command, user_name):
    ''' Delete all retrospective items in current sprint.
    '''
    sprint = Sprint.get_current_sprint(user_name)
    items = RetrospectiveItem.get_retrospective_items_for_sprint(sprint)
    try:
        items.delete()
        db.session.commit()
    except Exception as e:
        return u'Sorry, but *{}* was unable to delete retrospective items: {}, {}.'.format(BOT_NAME, e.message, e.args)

    return u'All retrospective items have been deleted for *{}*.'.format(sprint)

def format_json_response(response, in_channel=True):
    ''' Format response for Slack
    '''
    if isinstance(response, basestring):
        text = response
        attachments = None
    else:
        text = response[0]
        attachments = response[1]

    response_dict = {
        'response_type': 'in_channel' if in_channel else 'ephemeral',
        'text': text,
        'attachments': attachments if attachments else []
    }

    response_json = json.dumps(response_dict)
    return Response(response_json, status=200, mimetype='application/json')

#
# ROUTES
#

@app.route('/', methods=['POST'])
def index():
    # verify that the request is authorized
    if request.form['token'] != current_app.config['SLACK_TOKEN']:
        abort(401)

    # get the user name and channel ID
    user_name = unicode(request.form['user_name'])
    channel_id = unicode(request.form['channel_id'])

    # get the slash command
    slash_command = unicode(request.form['command'])

    # strip excess spaces from the text
    full_text = unicode(request.form['text'].strip())
    full_text = sub(u' +', u' ', full_text)
    command_text = full_text

    # The bot can be called in Slack with:
    if slash_command in CATEGORY_CMDS:
        # '/good Bla Bla'
        command_action = slash_command
        command_params = command_text
    else:
        # or '/retrospective good Bla Bla'
        command_action, command_params = get_command_action_and_params(command_text)

    # If the command does not exist, show help
    if command_action not in ALL_CMDS:
        command_action = HELP_CMDS[0]


    # Call different actions:

    # ADD GOOD, BAD or TRY
    if command_action in CATEGORY_CMDS:
        category = command_action
        text = command_params
        response = add_retrospective_item_and_get_response(slash_command, category, text, user_name)
        return format_json_response(response)

    # LIST
    if command_action in LIST_CMDS:
        response = get_retrospective_items_response(slash_command, user_name)
        return format_json_response(response)

    # NEW SPRINT
    if command_action in NEW_CMDS:
        response = start_new_sprint(slash_command, user_name)
        return format_json_response(response)

    # RESET
    if command_action in RESET_CMDS:
        response = reset_current_sprint(slash_command, user_name)
        return format_json_response(response)

    # HELP
    if command_action in HELP_CMDS or command_text == u'' or command_text == u' ':
        response = '\n'.join([
            u'*{command} good <item>* to save an item in the "good" list',
            u'*{command} bad <item>* to save an item in the "bad" list',
            u'*{command} try <item>* to save an item in the "try" list',
            u'*{command} list* to see the different lists saved for the current sprint',
            u'*{command} new* to start a fresh list for the new scrum sprint',
            u'*{command} reset* to delete retrospective items in the current sprint (use when you created a mess)',
            u'*{command} help* to see this message',
        ]).format(command=slash_command)
        # Don't show help to other users in th channel
        return format_json_response(response, in_channel=False)
