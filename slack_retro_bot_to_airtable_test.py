#!/usr/bin/env python
"""Test /retro commands."""

import textwrap
import unittest
from os import environ

import airtablemock
import mock

import slack_retro_bot_to_airtable


@mock.patch(slack_retro_bot_to_airtable.__name__ + '._STEPS_TO_FINISH_SETUP', None)
@mock.patch(slack_retro_bot_to_airtable.__name__ + '._SLACK_RETRO_TOKEN', 'meowser_token')
class TestBot(unittest.TestCase):
    """Test /retro commands."""

    def setUp(self):
        environ['DATABASE_URL'] = 'postgres:///retrospective-bot-test'
        environ['SLACK_TOKEN'] = 'meowser_token'
        environ['SLACK_WEBHOOK_URL'] = 'http://hooks.example.com/services/HELLO/LOVELY/WORLD'

        self.app = slack_retro_bot_to_airtable.app.test_client()

        airtablemock.clear()
        self.airtable_client = airtablemock.Airtable('retro-base-id')
        patcher = mock.patch(
            slack_retro_bot_to_airtable.__name__ + '._AIRTABLE_CLIENT',
            self.airtable_client)
        patcher.start()

        self.airtable_client.create('Items', {'sprint': 'old'})
        self.airtable_client.create_view('Items', 'Current View', 'sprint != "old"')
        self.airtable_client.create('Moods', {'sprint': 'old'})
        self.airtable_client.create_view('Moods', 'Current View', 'sprint != "old"')

    def _post_command(self, text, slash_command='/retro'):

        return self.app.post('/handle_slack_command', data={
            'token': 'meowser_token',
            'text': text,
            'user_name': 'retroman',
            'channel_id': '123456',
            'command': slash_command,
            'response_url': 'https://lambda-to-slack.com',
        })

    # As the name of the tests are self-explanatory, we don't need docstrings for them
    # pylint: disable=missing-docstring
    def test_app_exists(self):
        """The app exists."""

        self.assertTrue(self.app)

    # def test_unauthorized_access(self):
    #     """The app rejects unauthorized access."""
    #     robo_response = self.client.post('/', data={'token': 'woofer_token'})
    #     self.assertEqual(robo_response.status_code, 401)

    # def test_authorized_access(self):
    #     """The app accepts authorized access."""
    #     robo_response = self.post_command(text='')
    #     self.assertEqual(robo_response.status_code, 200)

    def test_set_retrospective_item_with_good_command(self):
        return self._test_set_retrospective_item(
            'good', 'good', 'The coffee was great', is_using_direct_command=True)

    def test_set_retrospective_item_with_bad_command(self):
        return self._test_set_retrospective_item(
            'bad', 'danger', 'The coffee was bad', is_using_direct_command=True)

    def test_set_retrospective_item_with_weird_case(self):
        return self._test_set_retrospective_item(
            'bad', 'danger', 'the coffee was bad, because of Cyrille',
            is_using_direct_command=True, expected_text='The coffee was bad, because of Cyrille')

    # def test_set_retrospective_item_with_try_command(self):
    #     return self._test_set_retrospective_item(
    #         'try', 'warning', 'Make more coffee', is_using_direct_command=True)

    def test_set_retrospective_item_with_retrospective_good_command(self):
        return self._test_set_retrospective_item(
            'good', 'good', 'The tea was great', is_using_direct_command=False)

    def test_set_retrospective_item_with_quotes(self):
        return self._test_set_retrospective_item(
            'good', 'good', 'It\'s possible to use "quotes"')

    def test_set_retrospective_item_with_retrospective_bad_command(self):
        return self._test_set_retrospective_item(
            'bad', 'danger', 'The tea was bad', is_using_direct_command=False)

    # def test_set_retrospective_item_with_retrospective_try_command(self):
    #     return self._test_set_retrospective_item(
    #         'try', 'warning', 'Make more tea', is_using_direct_command=False)

    def _test_set_retrospective_item(
            self, category, color, text,
            is_using_direct_command=False, expected_text=None):
        """ A retrospective item set via a POST is recorded in the database."""

        if is_using_direct_command:
            # '/good Bla bla'
            robo_response = self._post_command(text=text, slash_command=category)
        else:
            # '/retrospective good Bla bla'
            robo_response = self._post_command(
                text='{} {}'.format(category, text), slash_command='retro')

        if expected_text is None:
            expected_text = text

        self.assertEqual(
            {
                'text': 'New retrospective item:',
                'response_type': 'in_channel',
                'attachments': [
                    {'title': category.capitalize(), 'color': color},
                    {'color': color, 'text': expected_text},
                ],
            },
            robo_response.json,
        )
        items = self.airtable_client.get('Items', view='Current View')
        self.assertEqual(1, len(items['records']), msg=items)
        item = items['records'][0]['fields']
        self.assertEqual(category, item['Category'])
        self.assertEqual('retroman', item['Creator'])
        self.assertEqual(expected_text, item['Object'])

    def test_list(self):
        """ Test getting the list of all items with POST."""

        # Check list is empty at first
        robo_response = self._post_command(text='list', slash_command='retro')
        self.assertEqual(200, robo_response.status_code, msg=robo_response.data)
        expected_list = {
            'text': 'No retrospective items yet.',
            'response_type': 'in_channel',
            'attachments': [],
        }
        self.assertEqual(robo_response.json, expected_list)

        check = self._post_command(text='The coffee was great', slash_command='good')
        self.assertEqual(200, check.status_code, msg=check.data)
        self._post_command(text='The coffee was bad', slash_command='bad')
        self._post_command(text='The tea was great', slash_command='good')

        # Check list is filled later
        robo_response = self._post_command(text='list', slash_command='retro')
        expected_list = {
            'text': 'Retrospective items:',
            'response_type': 'in_channel',
            'attachments': [
                {'color': 'good', 'title': 'Good'},
                {'color': 'good', 'text': 'The coffee was great'},
                {'color': 'good', 'text': 'The tea was great'},
                {'color': 'danger', 'title': 'Bad'},
                {'color': 'danger', 'text': 'The coffee was bad'},
            ],
        }
        self.assertEqual(expected_list, robo_response.json)

    def test_list_good(self):
        """ Test getting the list of all good items with POST."""

        self._post_command(text='The coffee was great', slash_command='good')
        self._post_command(text='The coffee was bad', slash_command='bad')
        self._post_command(text='The tea was great', slash_command='good')
        self._post_command(text='Improve the coffee', slash_command='try')

        robo_response = self._post_command(text='list good', slash_command='retro')
        expected_list = {
            'text': 'Retrospective items:',
            'response_type': 'in_channel',
            'attachments': [
                {'color': 'good', 'title': 'Good'},
                {'color': 'good', 'text': 'The coffee was great'},
                {'color': 'good', 'text': 'The tea was great'},
            ],
        }
        self.assertEqual(expected_list, robo_response.json)

    def test_list_wrong_category(self):
        """ Test listing by an unknown category."""

        self._post_command(text='The coffee was great', slash_command='good')
        self._post_command(text='The coffee was bad', slash_command='bad')
        self._post_command(text='The tea was great', slash_command='good')
        self._post_command(text='Improve the coffee', slash_command='try')

        robo_response = self._post_command(text='list maybe good', slash_command='retro')
        expected_list = {
            'text': 'Wrong category "maybe good", should be "good", "bad", "try" or empty.',
            'response_type': 'in_channel',
            'attachments': [],
        }
        self.assertEqual(expected_list, robo_response.json)

    def test_mood(self):
        """Test listing the mood for everyone."""

        self.airtable_client.create('Moods', {
            'Name': 'Cyrille',
            'How are you feeling at Bayes': "I don't know, \nI'm ok",
            'Feeling at bayes free text': 'NTD',
            'How is your work going': "I'm doing a good job",
        })
        robo_response = self._post_command(text='mood', slash_command='retro')
        expected_response = textwrap.dedent('''\
            :mag: Dear team, here is the weekly check in of this week :mag_right:

            *Cyrille*
            • _Feeling_
            :face_with_rolling_eyes: I don't know
            :no_mouth: I'm ok
            > NTD
            • _Work at Bayes_
            :relaxed: I'm doing a good job

            ''')
        self.assertEqual(
            {
                'attachments': [],
                'response_type': 'in_channel',
                'text': expected_response,
            },
            robo_response.json)

    # def test_help(self):
    #     """ Test getting the help for the command.
    #     """
    #     robo_response = self.post_command(text='help', slash_command='retro')
    #     self.assertTrue('to see this message' in robo_response.data)

    # def test_start_new_sprint(self):
    #     """ Test starting a new sprint with POST.
    #     """
    #     date = self._get_sprint_date()

    #     # Test first sprint logs 'good' item correctly
    #     robo_response = self.post_command(
    #         text='The coffee was great', slash_command='good')
    #     robo_response = self.post_command(text='list', slash_command='retro')
    #     expected_list = \
    #         '{{"text": "Retrospective items for *Sprint 1, started on {}*:", '.format(date) +\
    #         '"response_type": "in_channel", "attachments": [' +\
    #         '{"color": "good", "text": "The coffee was great", "title": "Good"}]}'
    #     self.assertEqual(robo_response.data, expected_list)

    #     # Start a new sprint and check that no item is in it
    #     robo_response = self.post_command(text='new', slash_command='retro')
    #     robo_response = self.post_command(text='list', slash_command='retro')
    #     expected_list = '{"text": "' +\
    #         'No retrospective items yet for *Sprint 2, started on {}*.'.format(date) +\
    #         '", "response_type": "in_channel", "attachments": []}'
    #     self.assertEqual(robo_response.data, expected_list)

    #     # Test second sprint logs another 'good' item correctly
    #     robo_response = self.post_command(
    #         text='The coffee was great again', slash_command='good')
    #     robo_response = self.post_command(text='list', slash_command='retro')
    #     expected_list = \
    #         '{{"text": "Retrospective items for *Sprint 2, started on {}*:", '.format(date) +\
    #         '"response_type": "in_channel", "attachments": [' +\
    #         '{"color": "good", "text": "The coffee was great again", "title": "Good"}]}'
    #     self.assertEqual(robo_response.data, expected_list)

    # def test_reset_current_sprint(self):
    #     """ Test deleting all retrospective items in the current sprint with POST.
    #     """
    #     # Test first sprint logs 'good' item correctly
    #     date = self._get_sprint_date()
    #     robo_response = self.post_command(
    #         text='The coffee was great', slash_command='good')
    #     robo_response = self.post_command(text='list', slash_command='retro')
    #     expected_list = \
    #         '{{"text": "Retrospective items for *Sprint 1, started on {}*:", '.format(date) +\
    #         '"response_type": "in_channel", "attachments": [' +\
    #         '{"color": "good", "text": "The coffee was great", "title": "Good"}]}'
    #     self.assertEqual(robo_response.data, expected_list)

    #     # Reset sprint
    #     robo_response = self.post_command(text='reset', slash_command='retro')
    #     expected_response = '{{"text": ' +\
    #         '"All retrospective items have been deleted for *Sprint 1, started on {}*.", '\
    #         .format(date) +\
    #         '"response_type": "in_channel", "attachments": []}'
    #     self.assertEqual(robo_response.data, expected_response)

    #     # And check that no items are found anymore
    #     date = self._get_sprint_date()
    #     robo_response = self.post_command(text='list', slash_command='retro')
    #     expected_list = '{"text": "' +\
    #         'No retrospective items yet for *Sprint 1, started on {}*.'.format(date) +\
    #         '", "response_type": "in_channel", "attachments": []}'
    #     self.assertEqual(robo_response.data, expected_list)

    # def _get_sprint_date(self):
    #     sprint = Sprint.get_current_sprint('test_user')
    #     date = sprint.creation_date.date()
    #     return date


if __name__ == '__main__':
    unittest.main()
