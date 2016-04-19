#!/usr/bin/env python
# -*- coding: utf8 -*-
import unittest
import json
from httmock import response, HTTMock
from flask import current_app
from gloss.models import Sprint, RetrospectiveItem, Definition, Interaction
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
            robo_response = self.post_command(text=u'{} {}'.format(category, text), slash_command=u'retrospective')
        self.assertTrue(u'has saved the retrospective item' in robo_response.data, robo_response.data)

        filters = (RetrospectiveItem.category == category, RetrospectiveItem.text == text)
        retrospective_item_check = self.db.session.query(RetrospectiveItem).filter(*filters).first()
        self.assertIsNotNone(retrospective_item_check)
        self.assertEqual(retrospective_item_check.category, category)
        self.assertEqual(retrospective_item_check.text, text)

    def test_list(self):
        ''' Test getting the list of all items with POST.
        '''
        robo_response = self.post_command(text=u'The coffee was great', slash_command=u'good')
        robo_response = self.post_command(text=u'The coffee was bad', slash_command=u'bad')
        robo_response = self.post_command(text=u'Make more coffee', slash_command=u'try')
        robo_response = self.post_command(text=u'The tea was great', slash_command=u'good')
        robo_response = self.post_command(text=u'list', slash_command=u'retrospective')
        expected_list = u'Bad:\nThe coffee was bad\n\nGood:\nThe coffee was great\nThe tea was great\n\nTry:\nMake more coffee\n\n'
        self.assertTrue(robo_response.data == expected_list, robo_response.data)

if __name__ == '__main__':
    unittest.main()
