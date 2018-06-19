#!/usr/bin/env python
"""Test \retro commands."""
# import json
import unittest
from os import environ

from flask import current_app
# from slack_retro_bot_to_airtable import handle_slack_notification


class TestBot(unittest.TestCase):
    """Test \retro commands."""

    def setUp(self):
        environ['DATABASE_URL'] = 'postgres:///retrospective-bot-test'
        environ['SLACK_TOKEN'] = 'meowser_token'
        environ['SLACK_WEBHOOK_URL'] = 'http://hooks.example.com/services/HELLO/LOVELY/WORLD'

        # self.app = create_app(environ)
        # self.app_context = self.app.app_context()
        # self.app_context.push()

        # self.db = db
        # self.client = self.app.test_client()

    def tearDown(self):
        pass
        # self.db.session.close()
        # self.db.drop_all()
        # drop_all doesn't drop the alembic_version table
        # self.db.session.execute('DROP TABLE IF EXISTS alembic_version')
        # self.db.session.commit()
        # self.app_context.pop()

    # def post_command(self, text, slash_command='/retro'):
    #     return self.client.post('/', data={
    #         'token': 'meowser_token',
    #         'text': text,
    #         'user_name': 'retroman',
    #         'channel_id': '123456',
    #         'command': slash_command,
    #     })

    # As the name of the tests are self-explanatory, we don't need docstrings for them
    # pylint: disable=missing-docstring
    def test_app_exists(self):
        """The app exists."""
        self.assertFalse(current_app is None)

    # def test_unauthorized_access(self):
    #     """The app rejects unauthorized access."""
    #     robo_response = self.client.post('/', data={'token': 'woofer_token'})
    #     self.assertEqual(robo_response.status_code, 401)

    # def test_authorized_access(self):
    #     """The app accepts authorized access."""
    #     robo_response = self.post_command(text='')
    #     self.assertEqual(robo_response.status_code, 200)

    # def test_set_retrospective_item_with_good_command(self):
    #     return self._test_set_retrospective_item('good', 'The coffee was great',
    #                                              is_using_direct_command=True)

    # def test_set_retrospective_item_with_bad_command(self):
    #     return self._test_set_retrospective_item('bad', 'The coffee was bad',
    #                                              is_using_direct_command=True)

    # def test_set_retrospective_item_with_try_command(self):
    #     return self._test_set_retrospective_item('try', 'Make more coffee',
    #                                              is_using_direct_command=True)

    # def test_set_retrospective_item_with_retrospective_good_command(self):
    #     return self._test_set_retrospective_item('good', 'The tea was great',
    #                                              is_using_direct_command=False)

    # def test_set_retrospective_item_with_retrospective_bad_command(self):
    #     return self._test_set_retrospective_item('bad', 'The tea was bad',
    #                                              is_using_direct_command=False)

    # def test_set_retrospective_item_with_retrospective_try_command(self):
    #     return self._test_set_retrospective_item('try', 'Make more tea',
    #                                              is_using_direct_command=False)

    # def _test_set_retrospective_item(self, category, text, is_using_direct_command):
    #     """ A retrospective item set via a POST is recorded in the database.
    #     """
    #     if is_using_direct_command:
    #         # '/good Bla bla'
    #         robo_response = self.post_command(
    #             text=text, slash_command=category)
    #     else:
    #         # '/retrospective good Bla bla'
    #         robo_response = self.post_command(text='{} {}'.format(category, text),
    #                                           slash_command='retro')

    #     date = self._get_sprint_date()
    #     expected_colors_by_category = {
    #         'good': 'good', 'bad': 'danger', 'try': 'warning'}
    #     expected_color = expected_colors_by_category[category]
    #     self.assertEqual(
    #         robo_response.data,
    #         '{{"text": "New retrospective item for *Sprint 1, started on {}*:", '.format(date) +
    #         '"response_type": "in_channel", "attachments": [' +
    #         '{{"color": "{}", "text": "{}", "title": "{}"}}]}}'.format(
    #             expected_color, text, category.capitalize())
    #     )
    #     filters = (RetrospectiveItem.category == category,
    #                RetrospectiveItem.text == text)
    #     # retrospective_item_check = self.db.session.query(
    #         # RetrospectiveItem).filter(*filters).first()
    #     # self.assertIsNotNone(retrospective_item_check)
    #     # self.assertEqual(retrospective_item_check.category, category)
    #     # self.assertEqual(retrospective_item_check.text, text)

    # def test_list(self):
    #     """ Test getting the list of all items with POST.
    #     """
    #     date = self._get_sprint_date()

    #     # Check list is empty at first
    #     robo_response = self.post_command(text='list', slash_command='retro')
    #     expected_list = '{"text": "' +\
    #         'No retrospective items yet for *Sprint 1, started on {}*.'.format(date) +\
    #         '", "response_type": "in_channel", "attachments": []}'
    #     self.assertEqual(robo_response.data, expected_list)

    #     # Check list is filled later
    #     robo_response = self.post_command(
    #         text='The coffee was great', slash_command='good')
    #     robo_response = self.post_command(
    #         text='The coffee was bad', slash_command='bad')
    #     robo_response = self.post_command(
    #         text='Make more coffee', slash_command='try')
    #     robo_response = self.post_command(
    #         text='The tea was great', slash_command='good')
    #     robo_response = self.post_command(text='list', slash_command='retro')
    #     expected_list = \
    #         '{{"text": "Retrospective items for *Sprint 1, started on {}*:", '.format(date) +\
    #         '"response_type": "in_channel", "attachments": [' +\
    #         '{"color": "danger", "text": "The coffee was bad", "title": "Bad"}, ' +\
    #         '{"color": "good", "text": "The coffee was great\\nThe tea was great", ' +\
    #         '"title": "Good"}, ' +\
    #         '{"color": "warning", "text": "Make more coffee", "title": "Try"}]}'
    #     self.assertEqual(robo_response.data, expected_list)

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
