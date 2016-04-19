#!/usr/bin/env python
# -*- coding: utf8 -*-
import datetime
import unittest
import json
from httmock import response, HTTMock
from flask import current_app
from gloss.models import Sprint, RetrospectiveItem
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
        self.assertTrue(u'*{}: {}* successfully saved'.format(category.capitalize(), text) in robo_response.data, robo_response.data)

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
        expected_list = u'{"text": "' +\
            u'Retrospective items for *Sprint 1, started on {}*:\\n'.format(date) +\
            u'Bad:\\nThe coffee was bad\\n\\nGood:\\nThe coffee was great\\nThe tea was great\\n\\nTry:\\nMake more coffee\\n\\n' +\
            u'", "response_type": "in_channel", "attachments": []}'
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
        expected_list = u'{"text": "' +\
            u'Retrospective items for *Sprint 1, started on {}*:\\n'.format(date) +\
            u'Good:\\nThe coffee was great\\n\\n' +\
            u'", "response_type": "in_channel", "attachments": []}'
        self.assertEqual(robo_response.data, expected_list)

        # Start a new sprint and check that new item is in it
        robo_response = self.post_command(text=u'new', slash_command=u'retro')
        robo_response = self.post_command(text=u'list', slash_command=u'retro')
        expected_list = u'{"text": "' +\
            u'No retrospective items yet for *Sprint 2, started on {}*.'.format(date) +\
            u'", "response_type": "in_channel", "attachments": []}'
        self.assertEqual(robo_response.data, expected_list)

        # Test second sprint logs another 'good' item correctly
        robo_response = self.post_command(text=u'The coffee was great again', slash_command=u'good')
        robo_response = self.post_command(text=u'list', slash_command=u'retro')
        expected_list = u'{"text": "' +\
            u'Retrospective items for *Sprint 2, started on {}*:\\n'.format(date) +\
            u'Good:\\nThe coffee was great again\\n\\n' +\
            u'", "response_type": "in_channel", "attachments": []}'
        self.assertEqual(robo_response.data, expected_list)

    def _get_sprint_date(self):
        sprint = Sprint.get_current_sprint(u'test_user')
        date = sprint.creation_date.date()
        return date

if __name__ == '__main__':
    unittest.main()
