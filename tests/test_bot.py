#!/usr/bin/env python
# -*- coding: utf8 -*-
import datetime
import unittest
import json
from httmock import response, HTTMock
from flask import current_app
from retro.models import Sprint, RetrospectiveItem
from datetime import datetime, timedelta
from tests.test_base import TestBase


class TestBot(TestBase):

    def setUp(self):
        super(TestBot, self).setUp()
        self.db.create_all()

    def test_app_exists(self):
        ''' The app exists
        '''
        self.assertFalse(current_app is None)

    def test_unauthorized_access(self):
        ''' The app rejects unauthorized access
        '''
        robo_response = self.client.post('/', data={'token': 'woofer_token'})
        self.assertEqual(robo_response.status_code, 401)

    def test_authorized_access(self):
        ''' The app accepts authorized access
        '''
        robo_response = self.post_command(text=u'')
        self.assertEqual(robo_response.status_code, 200)

    def test_set_retrospective_item_with_good_command(self):
        return self._test_set_retrospective_item(u'good', u'The coffee was great', is_using_direct_command=True)

    def test_set_retrospective_item_with_bad_command(self):
        return self._test_set_retrospective_item(u'bad', u'The coffee was bad', is_using_direct_command=True)

    def test_set_retrospective_item_with_try_command(self):
        return self._test_set_retrospective_item(u'try', u'Make more coffee', is_using_direct_command=True)

    def test_set_retrospective_item_with_retrospective_good_command(self):
        return self._test_set_retrospective_item(u'good', u'The tea was great', is_using_direct_command=False)

    def test_set_retrospective_item_with_retrospective_bad_command(self):
        return self._test_set_retrospective_item(u'bad', u'The tea was bad', is_using_direct_command=False)

    def test_set_retrospective_item_with_retrospective_try_command(self):
        return self._test_set_retrospective_item(u'try', u'Make more tea', is_using_direct_command=False)

    def _test_set_retrospective_item(self, category, text, is_using_direct_command):
        ''' A retrospective item set via a POST is recorded in the database.
        '''
        if is_using_direct_command:
            # '/good Bla bla'
            robo_response = self.post_command(text=text, slash_command=category)
        else:
            # '/retrospective good Bla bla'
            robo_response = self.post_command(text=u'{} {}'.format(category, text), slash_command=u'retro')

        date = self._get_sprint_date()
        expected_colors_by_category = {'good': 'good', 'bad': 'danger', 'try': 'warning'}
        expected_color = expected_colors_by_category[category]
        self.assertEqual(robo_response.data, u'{{"text": "New retrospective item for *Sprint 1, started on {}*:", '.format(date) +\
            u'"response_type": "in_channel", "attachments": [' +\
            u'{{"color": "{}", "text": "\\u2022 {}", "title": "{}"}}]}}'.format(expected_color, text, category.capitalize())
        )
        filters = (RetrospectiveItem.category == category, RetrospectiveItem.text == text)
        retrospective_item_check = self.db.session.query(RetrospectiveItem).filter(*filters).first()
        self.assertIsNotNone(retrospective_item_check)
        self.assertEqual(retrospective_item_check.category, category)
        self.assertEqual(retrospective_item_check.text, text)

    def test_list(self):
        ''' Test getting the list of all items with POST.
        '''
        date = self._get_sprint_date()

        # Check list is empty at first
        robo_response = self.post_command(text=u'list', slash_command=u'retro')
        expected_list = u'{"text": "' +\
            u'No retrospective items yet for *Sprint 1, started on {}*.'.format(date) +\
            u'", "response_type": "in_channel", "attachments": []}'
        self.assertEqual(robo_response.data, expected_list)

        # Check list is filled later
        robo_response = self.post_command(text=u'The coffee was great', slash_command=u'good')
        robo_response = self.post_command(text=u'The coffee was bad', slash_command=u'bad')
        robo_response = self.post_command(text=u'Make more coffee', slash_command=u'try')
        robo_response = self.post_command(text=u'The tea was great', slash_command=u'good')
        robo_response = self.post_command(text=u'list', slash_command=u'retro')
        expected_list = u'{{"text": "Retrospective items for *Sprint 1, started on {}*:", '.format(date) +\
            u'"response_type": "in_channel", "attachments": [' +\
            u'{"color": "danger", "text": "\\u2022 The coffee was bad", "title": "Bad"}, ' +\
            u'{"color": "good", "text": "\\u2022 The coffee was great\\n\\n\\u2022 The tea was great", "title": "Good"}, ' +\
            u'{"color": "warning", "text": "\\u2022 Make more coffee", "title": "Try"}]}'
        self.assertEqual(robo_response.data, expected_list)

    def test_help(self):
        ''' Test getting the help for the command.
        '''
        robo_response = self.post_command(text=u'help', slash_command=u'retro')
        self.assertTrue('to see this message' in robo_response.data)

    def test_start_new_sprint(self):
        ''' Test starting a new sprint with POST.
        '''
        date = self._get_sprint_date()

        # Test first sprint logs 'good' item correctly
        robo_response = self.post_command(text=u'The coffee was great', slash_command=u'good')
        robo_response = self.post_command(text=u'list', slash_command=u'retro')
        expected_list = u'{{"text": "Retrospective items for *Sprint 1, started on {}*:", '.format(date) +\
            u'"response_type": "in_channel", "attachments": [' +\
            u'{"color": "good", "text": "\\u2022 The coffee was great", "title": "Good"}]}'
        self.assertEqual(robo_response.data, expected_list)

        # Start a new sprint and check that no item is in it
        robo_response = self.post_command(text=u'new', slash_command=u'retro')
        robo_response = self.post_command(text=u'list', slash_command=u'retro')
        expected_list = u'{"text": "' +\
            u'No retrospective items yet for *Sprint 2, started on {}*.'.format(date) +\
            u'", "response_type": "in_channel", "attachments": []}'
        self.assertEqual(robo_response.data, expected_list)

        # Test second sprint logs another 'good' item correctly
        robo_response = self.post_command(text=u'The coffee was great again', slash_command=u'good')
        robo_response = self.post_command(text=u'list', slash_command=u'retro')
        expected_list = u'{{"text": "Retrospective items for *Sprint 2, started on {}*:", '.format(date) +\
            u'"response_type": "in_channel", "attachments": [' +\
            u'{"color": "good", "text": "\\u2022 The coffee was great again", "title": "Good"}]}'
        self.assertEqual(robo_response.data, expected_list)

    def test_start_new_sprint_with_params(self):
        '''Test starting a sprint with commands (probably a mistake).'''
        robo_response = self.post_command(text='new The coffee was great')
        response = json.loads(robo_response.data)
        self.assertEqual({
            'text': 'Oops, did you mean "/retro good The coffee was great"?',
            'response_type': 'in_channel',
            'attachments': []}, response)

    def test_reset_current_sprint(self):
        ''' Test deleting all retrospective items in the current sprint with POST.
        '''
        # Test first sprint logs 'good' item correctly
        date = self._get_sprint_date()
        robo_response = self.post_command(text=u'The coffee was great', slash_command=u'good')
        robo_response = self.post_command(text=u'list', slash_command=u'retro')
        expected_list = u'{{"text": "Retrospective items for *Sprint 1, started on {}*:", '.format(date) +\
            u'"response_type": "in_channel", "attachments": [' +\
            u'{"color": "good", "text": "\\u2022 The coffee was great", "title": "Good"}]}'
        self.assertEqual(robo_response.data, expected_list)

        # Reset sprint
        robo_response = self.post_command(text=u'reset', slash_command=u'retro')
        expected_response = '{{"text": "All retrospective items have been deleted for *Sprint 1, started on {}*.", '.format(date) +\
            '"response_type": "in_channel", "attachments": []}'
        self.assertEqual(robo_response.data, expected_response)

        # And check that no items are found anymore
        date = self._get_sprint_date()
        robo_response = self.post_command(text=u'list', slash_command=u'retro')
        expected_list = u'{"text": "' +\
            u'No retrospective items yet for *Sprint 1, started on {}*.'.format(date) +\
            u'", "response_type": "in_channel", "attachments": []}'
        self.assertEqual(robo_response.data, expected_list)

    def _get_sprint_date(self):
        sprint = Sprint.get_current_sprint(u'test_user')
        date = sprint.creation_date.date()
        return date

if __name__ == '__main__':
    unittest.main()
