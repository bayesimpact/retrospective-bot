#!/usr/bin/env python
# -*- coding: utf8 -*-
import unittest
import json
from httmock import response, HTTMock
from flask import current_app
from gloss.models import Sprint, RetrospectiveItem, Definition, Interaction
from gloss.views import query_definition
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

    def test_set_good_retrospective_item(self):
        ''' A definition set via a POST is recorded in the database
        '''
        robo_response = self.post_command(text=u'The coffee was great', slash_command=u'good')
        self.assertTrue(u'has saved the retrospective item' in robo_response.data, robo_response.data)

        filter = (RetrospectiveItem.category == 'good' and RetrospectiveItem.text == u'The coffee was great')
        retrospective_item_check = self.db.session.query(RetrospectiveItem).filter(filter).first()
        self.assertIsNotNone(retrospective_item_check)

    def test_set_definition(self):
        ''' A definition set via a POST is recorded in the database
        '''
        robo_response = self.post_command(text=u'EW = Eligibility Worker')
        self.assertTrue(u'has set the definition' in robo_response.data)

        filter = Definition.term == u'EW'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'EW')
        self.assertEqual(definition_check.definition, u'Eligibility Worker')

    def test_set_definition_with_lots_of_whitespace(self):
        ''' Excess whitespace is trimmed when parsing the set command.
        '''
        robo_response = self.post_command(text=u'     EW   =    Eligibility      Worker  ')
        self.assertTrue(u'has set the definition' in robo_response.data)

        filter = Definition.term == u'EW'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'EW')
        self.assertEqual(definition_check.definition, u'Eligibility Worker')

    def test_set_definition_with_multiple_equals_signs(self):
        ''' A set with multiple equals signs considers all equals signs after
            the first to be part of the definition
        '''
        robo_response = self.post_command(text=u'EW = Eligibility Worker = Cool Person=Yeah')
        self.assertTrue(u'has set the definition' in robo_response.data)

        filter = Definition.term == u'EW'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'EW')
        self.assertEqual(definition_check.definition, u'Eligibility Worker = Cool Person=Yeah')

    def test_reset_definition(self):
        ''' Setting a definition for an existing term overwrites the original
        '''
        robo_response = self.post_command(text=u'EW = Eligibility Worker')
        self.assertTrue(u'has set the definition' in robo_response.data)

        filter = Definition.term == u'EW'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'EW')
        self.assertEqual(definition_check.definition, u'Eligibility Worker')

        robo_response = self.post_command(text=u'EW = Egg Weathervane')
        self.assertTrue(u'overwriting the previous entry' in robo_response.data)

        filter = Definition.term == u'EW'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'EW')
        self.assertEqual(definition_check.definition, u'Egg Weathervane')

    def test_set_same_word_with_different_capitalization(self):
        ''' We can't set different definitions for the same word by using different cases
        '''
        robo_response = self.post_command(text=u'lower case = NOT UPPER CASE')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u'has set the definition' in robo_response.data)

        filter = Definition.term == u'lower case'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'lower case')
        self.assertEqual(definition_check.definition, u'NOT UPPER CASE')

        robo_response = self.post_command(text=u'LOWER CASE = really not upper case')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u'overwriting the previous entry' in robo_response.data)

        robo_response = self.post_command(text=u'shh lower case')
        self.assertTrue(u'LOWER CASE: really not upper case' in robo_response.data)

    def test_set_identical_definition(self):
        ''' Correct response for setting an identical definition for an existing term
        '''
        robo_response = self.post_command(text=u'EW = Eligibility Worker')
        self.assertTrue(u'has set the definition' in robo_response.data)

        filter = Definition.term == u'EW'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'EW')
        self.assertEqual(definition_check.definition, u'Eligibility Worker')

        robo_response = self.post_command(text=u'EW = Eligibility Worker')
        self.assertTrue(u'already knows that the definition for' in robo_response.data)

    def test_set_command_word_definitions(self):
        ''' We can successfull set and get definitions for unreserved command words.
        '''
        robo_response = self.post_command(text=u'SHH = Sonic Hedge Hog')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u'has set the definition' in robo_response.data)

        filter = Definition.term == u'SHH'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'SHH')
        self.assertEqual(definition_check.definition, u'Sonic Hedge Hog')

        robo_response = self.post_command(text=u'SSH = Secure SHell')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u'has set the definition' in robo_response.data)

        filter = Definition.term == u'SSH'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'SSH')
        self.assertEqual(definition_check.definition, u'Secure SHell')

        robo_response = self.post_command(text=u'Delete = Remove or Obliterate')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u'has set the definition' in robo_response.data)

        filter = Definition.term == u'Delete'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'Delete')
        self.assertEqual(definition_check.definition, u'Remove or Obliterate')

        robo_response = self.post_command(text=u'help me = I\'m in hell')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u'has set the definition' in robo_response.data)

        filter = Definition.term == u'help me'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'help me')
        self.assertEqual(definition_check.definition, u'I\'m in hell')

    def test_failed_set_command_word_definitions(self):
        ''' We can't successfully set and get definitions for reserved command words.
        '''
        robo_response = self.post_command(text=u'Stats = Statistics')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u'because it\'s a reserved term' in robo_response.data)

        robo_response = self.post_command(text=u'help = aid')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u'because it\'s a reserved term' in robo_response.data)

        robo_response = self.post_command(text=u'LeArNiNgS = recently')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u'because it\'s a reserved term' in robo_response.data)

        robo_response = self.post_command(text=u'? = riddle me this')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u'because it\'s a reserved term' in robo_response.data)

    def test_get_definition(self):
        ''' We can succesfully set and get a definition from the bot
        '''
        # set & test a definition
        self.post_command(text=u'EW = Eligibility Worker')

        filter = Definition.term == u'EW'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'EW')
        self.assertEqual(definition_check.definition, u'Eligibility Worker')

        # capture the bot's POST to the incoming webhook and test its content
        def response_content(url, request):
            if 'hooks.example.com' in url.geturl():
                payload = json.loads(request.body)
                self.assertIsNotNone(payload['username'])
                self.assertIsNotNone(payload['text'])
                self.assertTrue(u'glossie' in payload['text'])
                self.assertTrue(u'gloss EW' in payload['text'])
                self.assertEqual(payload['channel'], u'123456')
                self.assertIsNotNone(payload['icon_emoji'])

                attachment = payload['attachments'][0]
                self.assertIsNotNone(attachment)
                self.assertEqual(attachment['title'], u'EW')
                self.assertEqual(attachment['text'], u'Eligibility Worker')
                self.assertIsNotNone(attachment['color'])
                self.assertIsNotNone(attachment['fallback'])
                return response(200)

        # send a POST to the bot to request the definition
        with HTTMock(response_content):
            fake_response = self.post_command(text=u'EW')
            self.assertTrue(fake_response.status_code in range(200, 299), fake_response.status_code)

        # the request was recorded in the interactions table
        interaction_check = self.db.session.query(Interaction).first()
        self.assertIsNotNone(interaction_check)
        self.assertEqual(interaction_check.user_name, u'glossie')
        self.assertEqual(interaction_check.term, u'EW')
        self.assertEqual(interaction_check.action, u'found')

    def test_get_definition_with_special_characters(self):
        ''' We can succesfully set and get a definition with special characters from the bot
        '''
        # set & test a definition
        self.post_command(text=u'EW = ™¥∑ø∂∆∫')

        filter = Definition.term == u'EW'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'EW')
        self.assertEqual(definition_check.definition, u'™¥∑ø∂∆∫')

        # capture the bot's POST to the incoming webhook and test its content
        def response_content(url, request):
            if 'hooks.example.com' in url.geturl():
                payload = json.loads(request.body)
                self.assertIsNotNone(payload['username'])
                self.assertIsNotNone(payload['text'])
                self.assertTrue(u'glossie' in payload['text'])
                self.assertTrue(u'gloss EW' in payload['text'])
                self.assertEqual(payload['channel'], u'123456')
                self.assertIsNotNone(payload['icon_emoji'])

                attachment = payload['attachments'][0]
                self.assertIsNotNone(attachment)
                self.assertEqual(attachment['title'], u'EW')
                self.assertEqual(attachment['text'], u'™¥∑ø∂∆∫')
                self.assertIsNotNone(attachment['color'])
                self.assertIsNotNone(attachment['fallback'])
                return response(200)

        # send a POST to the bot to request the definition
        with HTTMock(response_content):
            fake_response = self.post_command(text=u'EW')
            self.assertTrue(fake_response.status_code in range(200, 299), fake_response.status_code)

        # the request was recorded in the interactions table
        interaction_check = self.db.session.query(Interaction).first()
        self.assertIsNotNone(interaction_check)
        self.assertEqual(interaction_check.user_name, u'glossie')
        self.assertEqual(interaction_check.term, u'EW')
        self.assertEqual(interaction_check.action, u'found')

    def test_request_nonexistent_definition(self):
        ''' Test requesting a non-existent definition
        '''
        # send a POST to the bot to request the definition
        robo_response = self.post_command(text=u'EW')
        self.assertTrue(u'has no definition for' in robo_response.data)

        # the request was recorded in the interactions table
        interaction_check = self.db.session.query(Interaction).first()
        self.assertIsNotNone(interaction_check)
        self.assertEqual(interaction_check.user_name, u'glossie')
        self.assertEqual(interaction_check.term, u'EW')
        self.assertEqual(interaction_check.action, u'not_found')

    def test_get_definition_with_image(self):
        ''' We can get a properly formatted definition with an image from the bot
        '''
        # set & test a definition
        self.post_command(text=u'EW = http://example.com/ew.gif')

        filter = Definition.term == u'EW'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'EW')
        self.assertEqual(definition_check.definition, u'http://example.com/ew.gif')

        # capture the bot's POST to the incoming webhook and test its content
        def response_content(url, request):
            if 'hooks.example.com' in url.geturl():
                payload = json.loads(request.body)
                self.assertIsNotNone(payload['username'])
                self.assertIsNotNone(payload['text'])
                self.assertTrue(u'glossie' in payload['text'])
                self.assertTrue(u'gloss EW' in payload['text'])
                self.assertEqual(payload['channel'], u'123456')
                self.assertIsNotNone(payload['icon_emoji'])

                attachment = payload['attachments'][0]
                self.assertIsNotNone(attachment)
                self.assertEqual(attachment['title'], u'EW')
                self.assertEqual(attachment['text'], u'http://example.com/ew.gif')
                self.assertEqual(attachment['image_url'], u'http://example.com/ew.gif')
                self.assertIsNotNone(attachment['color'])
                self.assertIsNotNone(attachment['fallback'])
                return response(200)

        # send a POST to the bot to request the definition
        with HTTMock(response_content):
            fake_response = self.post_command(text=u'EW')
            self.assertTrue(fake_response.status_code in range(200, 299), fake_response.status_code)

    def test_delete_definition(self):
        ''' A definition can be deleted from the database
        '''
        # first set a value in the database and verify that it's there
        self.post_command(text=u'EW = Eligibility Worker')

        filter = Definition.term == u'EW'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'EW')
        self.assertEqual(definition_check.definition, u'Eligibility Worker')

        # now delete the value and verify that it's gone
        robo_response = self.post_command(text=u'delete EW')
        self.assertTrue(u'has deleted the definition for' in robo_response.data)

        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNone(definition_check)

    def test_get_stats(self):
        ''' Stats are properly returned by the bot
        '''
        # set and get a definition to generate some stats
        self.post_command(text=u'EW = Eligibility Worker')
        self.post_command(text=u'shh EW')

        # capture the bot's POST to the incoming webhook and test its content
        def response_content(url, request):
            if 'hooks.example.com' in url.geturl():
                payload = json.loads(request.body)
                self.assertIsNotNone(payload['username'])
                self.assertIsNotNone(payload['text'])
                self.assertTrue(u'glossie' in payload['text'])
                self.assertTrue(u'gloss stats' in payload['text'])
                self.assertEqual(payload['channel'], u'123456')
                self.assertIsNotNone(payload['icon_emoji'])

                attachment = payload['attachments'][0]
                self.assertIsNotNone(attachment)
                self.assertIsNotNone(attachment['title'])
                self.assertTrue(u'I have definitions for 1 term' in attachment['text'])
                self.assertTrue(u'1 person has defined terms' in attachment['text'])
                self.assertTrue(u'I\'ve been asked for definitions 1 time' in attachment['text'])
                self.assertIsNotNone(attachment['color'])
                self.assertIsNotNone(attachment['fallback'])
                return response(200)

        # send a POST to the bot to request stats
        with HTTMock(response_content):
            fake_response = self.post_command(text=u'stats')
            self.assertTrue(fake_response.status_code in range(200, 299), fake_response.status_code)

    def test_get_stats_on_empty_database(self):
        ''' A coherent message is returned when requesting stats on an empty database
        '''
        # capture the bot's POST to the incoming webhook and test its content
        def response_content(url, request):
            if 'hooks.example.com' in url.geturl():
                payload = json.loads(request.body)
                self.assertIsNotNone(payload['username'])
                self.assertIsNotNone(payload['text'])
                self.assertTrue(u'glossie' in payload['text'])
                self.assertTrue(u'gloss stats' in payload['text'])
                self.assertEqual(payload['channel'], u'123456')
                self.assertIsNotNone(payload['icon_emoji'])

                attachment = payload['attachments'][0]
                self.assertIsNotNone(attachment)
                self.assertIsNotNone(attachment['title'])
                self.assertTrue(u'I don\'t have any definitions' in attachment['text'])
                self.assertTrue(u'Nobody has defined terms' in attachment['text'])
                self.assertTrue(u'Nobody has asked me for definitions' in attachment['text'])
                self.assertIsNotNone(attachment['color'])
                self.assertIsNotNone(attachment['fallback'])
                return response(200)

        # send a POST to the bot to request stats
        with HTTMock(response_content):
            fake_response = self.post_command(text=u'stats')
            self.assertTrue(fake_response.status_code in range(200, 299), fake_response.status_code)

    def test_get_learnings(self):
        ''' Learnings are properly returned by the bot
        '''
        # set some values in the database
        letters = [u'K', u'L', u'M', u'N', u'Ó', u'P', u'Q', u'R', u'S', u'T', u'U', u'V']
        for letter in letters:
            self.post_command(text=u'{letter}W = {letter}ligibility Worker'.format(letter=letter))

        # capture the bot's POST to the incoming webhook and test its content
        def response_content(url, request):
            if 'hooks.example.com' in url.geturl():
                payload = json.loads(request.body)
                self.assertIsNotNone(payload['username'])
                self.assertIsNotNone(payload['text'])
                self.assertTrue(u'glossie' in payload['text'])
                self.assertTrue(u'gloss learnings' in payload['text'])
                self.assertEqual(payload['channel'], u'123456')
                self.assertIsNotNone(payload['icon_emoji'])

                attachment = payload['attachments'][0]
                self.assertIsNotNone(attachment)
                self.assertIsNotNone(attachment['title'])

                self.assertTrue(u'I recently learned definitions for' in attachment['text'])
                self.assertTrue(u'KW' in attachment['text'])
                self.assertTrue(u'LW' in attachment['text'])
                self.assertTrue(u'MW' in attachment['text'])
                self.assertTrue(u'NW' in attachment['text'])
                self.assertTrue(u'ÓW' in attachment['text'])
                self.assertTrue(u'PW' in attachment['text'])
                self.assertTrue(u'QW' in attachment['text'])
                self.assertTrue(u'RW' in attachment['text'])
                self.assertTrue(u'SW' in attachment['text'])
                self.assertTrue(u'TW' in attachment['text'])
                self.assertTrue(u'UW' in attachment['text'])
                self.assertTrue(u'VW' in attachment['text'])
                self.assertIsNotNone(attachment['color'])
                self.assertIsNotNone(attachment['fallback'])
                return response(200)

        # send a POST to the bot to request learnings
        with HTTMock(response_content):
            fake_response = self.post_command(text=u'learnings')
            self.assertTrue(fake_response.status_code in range(200, 299), fake_response.status_code)

    def test_random_learnings(self):
        ''' Learnings are returned in random order when requested
        '''
        # set some values in the database
        letters = [u'E', u'F', u'G', u'H', u'I', u'J', u'K', u'L', u'M', u'N', u'O', u'P', u'Q', u'R', u'S']
        for letter in letters:
            self.post_command(text=u'{letter}W = {letter}ligibility Worker'.format(letter=letter))

        # get chronological learnings
        robo_response = self.post_command(text=u'shh learnings')
        self.assertEqual(robo_response.status_code, 200)
        control = robo_response.data

        # get a few random learnings
        robo_response = self.post_command(text=u'shh learnings random')
        self.assertEqual(robo_response.status_code, 200)
        random1 = robo_response.data

        robo_response = self.post_command(text=u'shh learnings random')
        self.assertEqual(robo_response.status_code, 200)
        random2 = robo_response.data

        robo_response = self.post_command(text=u'shh learnings random')
        self.assertEqual(robo_response.status_code, 200)
        random3 = robo_response.data

        # if they're all equal, we've failed
        self.assertFalse(control == random1 and control == random2 and control == random3)

    def test_alphabetical_learnings(self):
        ''' Learnings are returned in random order when requested
        '''
        # set some values in the database
        letters = [u'E', u'G', u'I', u'K', u'M', u'O', u'Q', u'S', u'R', u'P', u'N', u'L', u'J', u'H', u'F']
        check = []
        for letter in letters:
            self.post_command(text=u'{letter}W = {letter}ligibility Worker'.format(letter=letter))
            check.insert(0, u'{}W'.format(letter))

        desc_check = check[:12]
        alpha_check = list(check)
        alpha_check.sort()
        alpha_check = alpha_check[:12]

        # get chronological learnings
        robo_response = self.post_command(text=u'shh learnings')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u', '.join(desc_check) in robo_response.data)

        # get alphabetical learnings
        robo_response = self.post_command(text=u'shh learnings alpha')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u', '.join(alpha_check) in robo_response.data)

    def test_random_offset_learnings(self):
        ''' An offset group of learnings are returned randomized
        '''
        # set some values in the database
        letters = [u'E', u'F', u'G', u'H', u'I', u'J', u'K', u'L', u'M', u'N', u'O', u'P', u'Q', u'R', u'S']
        for letter in letters:
            self.post_command(text=u'{letter}W = {letter}ligibility Worker'.format(letter=letter))

        # get chronological learnings
        robo_response = self.post_command(text=u'shh learnings 7 4')
        self.assertEqual(robo_response.status_code, 200)
        control = robo_response.data

        # get a list of the terms from the control string
        check_terms = control.split(', ')
        check_terms[0] = check_terms[0][-2:]

        # get a few random learnings
        robo_response = self.post_command(text=u'shh learnings random 7 4')
        self.assertEqual(robo_response.status_code, 200)
        random1 = robo_response.data

        robo_response = self.post_command(text=u'shh learnings random 7 4')
        self.assertEqual(robo_response.status_code, 200)
        random2 = robo_response.data

        robo_response = self.post_command(text=u'shh learnings random 7 4')
        self.assertEqual(robo_response.status_code, 200)
        random3 = robo_response.data

        # if they're all equal, we've failed
        self.assertFalse(control == random1 and control == random2 and control == random3)
        # but they should all have the same elements
        for term in check_terms:
            self.assertTrue(term in random1)
            self.assertTrue(term in random2)
            self.assertTrue(term in random3)

    def test_all_learnings(self):
        ''' All learnings are returned when requested
        '''
        # set some values in the database
        letters = [u'E', u'F', u'G', u'H', u'I', u'J', u'K', u'L', u'M', u'N', u'O', u'P', u'Q', u'R', u'S', u'T', u'U', u'V', u'W', u'X']
        check = []
        for letter in letters:
            self.post_command(text=u'{letter}W = {letter}ligibility Worker'.format(letter=letter))
            check.insert(0, u'{}W'.format(letter))

        # get all learnings
        robo_response = self.post_command(text=u'shh learnings all')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u', '.join(check) in robo_response.data)

        # if 'all' is part of the command, other limiting params are ignored
        robo_response = self.post_command(text=u'shh learnings all 5')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u', '.join(check) in robo_response.data)

        robo_response = self.post_command(text=u'shh learnings 5 3 all')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u', '.join(check) in robo_response.data)

        robo_response = self.post_command(text=u'shh learnings all 3 5')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u', '.join(check) in robo_response.data)

    def test_some_learnings(self):
        ''' Only a few learnings are returned when requested
        '''
        # set some values in the database
        letters = [u'E', u'F', u'G', u'H', u'I', u'J', u'K', u'L', u'M', u'N', u'O', u'P', u'Q', u'R', u'S', u'T', u'U', u'V', u'W', u'X']
        for letter in letters:
            self.post_command(text=u'{letter}W = {letter}ligibility Worker'.format(letter=letter))

        limit = 7
        check = [u'{}W'.format(item) for item in list(reversed(letters[-limit:]))]

        # get some learnings
        robo_response = self.post_command(text=u'shh learnings {}'.format(limit))
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u', '.join(check) in robo_response.data)

    def test_offset_learnings(self):
        ''' An offset of learnings are returned when requested
        '''
        # set some values in the database
        letters = [u'E', u'F', u'G', u'H', u'I', u'J', u'K', u'L', u'M', u'N', u'O', u'P', u'Q', u'R', u'S', u'T', u'U', u'V', u'W', u'X']
        for letter in letters:
            self.post_command(text=u'{letter}W = {letter}ligibility Worker'.format(letter=letter))

        limit = 7
        offset = 11
        check = [u'{}W'.format(item) for item in list(reversed(letters[-(limit + offset):-offset]))]

        # get some learnings
        robo_response = self.post_command(text=u'shh learnings {} {}'.format(limit, offset))
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u', '.join(check) in robo_response.data)

    def test_learnings_language(self):
        ''' Language describing learnings is numerically accurate
        '''
        # ask for learnings before any values have been set
        robo_response = self.post_command(text=u'shh learnings')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u'I haven\'t learned any definitions yet.' in robo_response.data)

        # when one value has been set
        self.post_command(text=u'EW = Eligibility Worker')
        robo_response = self.post_command(text=u'shh learnings')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u'I recently learned the definition for' in robo_response.data)

        # when more than one value has been set
        self.post_command(text=u'FW = Fligibility Worker')
        robo_response = self.post_command(text=u'shh learnings')
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(u'I recently learned definitions for' in robo_response.data)

    def test_get_help(self):
        ''' Help is properly returned by the bot
        '''
        # testing different chunks of help text with each response
        robo_response = self.post_command(text=u'help')
        self.assertTrue(u'to show the definition for a term' in robo_response.data)

        robo_response = self.post_command(text=u'?')
        self.assertTrue(u'to set the definition for a term' in robo_response.data)

        robo_response = self.post_command(text=u'')
        self.assertTrue(u'to delete the definition for a term' in robo_response.data)

        robo_response = self.post_command(text=u' ')
        self.assertTrue(u'to see this message' in robo_response.data)

    def test_custom_slash_command_for_private_requests(self):
        ''' A slash command other than /gloss is echoed in the bot's response
        '''
        test_command = u'/gg'
        # the help command
        robo_response = self.post_command(text=u'help', slash_command=test_command)
        self.assertTrue(u'*{}'.format(test_command) in robo_response.data)
        self.assertFalse(u'*/gloss' in robo_response.data)

        # ask for a definition that doesn't exist
        robo_response = self.post_command(text=u'shh EW', slash_command=test_command)
        self.assertTrue(u'*{}'.format(test_command) in robo_response.data)
        self.assertFalse(u'*/gloss' in robo_response.data)

        # get a definition that does exist
        self.post_command(text=u'EW = Eligibility Worker', slash_command=test_command)
        robo_response = self.post_command(text=u'shh EW', slash_command=test_command)
        self.assertTrue(u'{}'.format(test_command) in robo_response.data)
        self.assertFalse(u'/gloss' in robo_response.data)

        # get the error message for a bogus set
        robo_response = self.post_command(text=u'AW =', slash_command=test_command)
        self.assertTrue(u'*{}'.format(test_command) in robo_response.data)
        self.assertFalse(u'*/gloss' in robo_response.data)

    def test_custom_slash_command_for_public_stats(self):
        ''' A slash command other than /gloss is echoed in the bot's response
            to a public stats request.
        '''
        test_command = u'/gg'
        # set and get a definition to generate some stats
        self.post_command(text=u'EW = Eligibility Worker')
        self.post_command(text=u'shh EW')

        # capture the bot's POST to the incoming webhook and test its content
        def response_content(url, request):
            if 'hooks.example.com' in url.geturl():
                payload = json.loads(request.body)
                self.assertIsNotNone(payload['text'])
                self.assertTrue(u'{command} stats'.format(command=test_command) in payload['text'])

                return response(200)

        # send a POST to the bot to request stats
        with HTTMock(response_content):
            fake_response = self.post_command(text=u'stats', slash_command=test_command)
            self.assertTrue(fake_response.status_code in range(200, 299), fake_response.status_code)

    def test_custom_slash_command_for_public_definition(self):
        ''' A slash command other than /gloss is echoed in the bot's response
            to a public definition request.
        '''
        test_command = u'/gg'
        # set and get a definition to generate some stats
        self.post_command(text=u'EW = Eligibility Worker')

        # capture the bot's POST to the incoming webhook and test its content
        def response_content(url, request):
            if 'hooks.example.com' in url.geturl():
                payload = json.loads(request.body)
                self.assertIsNotNone(payload['text'])
                self.assertTrue(u'{command} EW'.format(command=test_command) in payload['text'])

                return response(200)

        # send a POST to the bot to request stats
        with HTTMock(response_content):
            fake_response = self.post_command(text=u'EW', slash_command=test_command)
            self.assertTrue(fake_response.status_code in range(200, 299), fake_response.status_code)

    def test_custom_slash_command_for_public_learnings(self):
        ''' A slash command other than /gloss is echoed in the bot's response
            to a public learnings request.
        '''
        test_command = u'/gg'

        # capture the bot's POST to the incoming webhook and test its content
        def response_content(url, request):
            if 'hooks.example.com' in url.geturl():
                payload = json.loads(request.body)
                self.assertIsNotNone(payload['text'])
                self.assertTrue(u'{command} learnings'.format(command=test_command) in payload['text'])

                return response(200)

        # send a POST to the bot to request stats
        with HTTMock(response_content):
            fake_response = self.post_command(text=u'learnings', slash_command=test_command)
            self.assertTrue(fake_response.status_code in range(200, 299), fake_response.status_code)

    def test_get_quiet_definition(self):
        ''' The bot will send a quiet definition when told to do so
        '''
        # set & test a definition
        self.post_command(text=u'EW = Eligibility Worker')

        filter = Definition.term == u'EW'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'EW')
        self.assertEqual(definition_check.definition, u'Eligibility Worker')

        # send a POST to the bot to request the quiet definition
        robo_response = self.post_command(text=u'shh EW')
        self.assertTrue(u'glossie' in robo_response.data)
        self.assertTrue(u'EW: Eligibility Worker' in robo_response.data)

        # send POSTs with variations of 'shh' to make sure that they're caught
        robo_response = self.post_command(text=u'ssh EW')
        self.assertTrue(u'glossie' in robo_response.data)
        self.assertTrue(u'EW: Eligibility Worker' in robo_response.data)

        robo_response = self.post_command(text=u'sh EW')
        self.assertTrue(u'glossie' in robo_response.data)
        self.assertTrue(u'EW: Eligibility Worker' in robo_response.data)

        # at least one request was recorded in the interactions table
        interaction_check = self.db.session.query(Interaction).first()
        self.assertIsNotNone(interaction_check)
        self.assertEqual(interaction_check.user_name, u'glossie')
        self.assertEqual(interaction_check.term, u'EW')
        self.assertEqual(interaction_check.action, u'found')

    def test_bad_set_commands(self):
        ''' We get the right error back when sending bad set commands
        '''
        robo_response = self.post_command(text=u'EW =')
        self.assertTrue(u'You can set definitions like this' in robo_response.data)

        robo_response = self.post_command(text=u'=')
        self.assertTrue(u'You can set definitions like this' in robo_response.data)

        robo_response = self.post_command(text=u'= = =')
        self.assertTrue(u'You can set definitions like this' in robo_response.data)

    def test_bad_image_urls_rejected(self):
        ''' Bad image URLs are not sent in the attachment's image_url parameter
        '''
        # set some definitions with bad image URLs
        self.post_command(text=u'EW = http://kittens.gif')
        self.post_command(text=u'FW = httpdoggie.jpeg')
        self.post_command(text=u'GW = http://stupid/goldfish.bmp')
        self.post_command(text=u'HW = http://s.mlkshk-cdn.com/r/13ILU')

        # capture the bot's POSTs to the incoming webhook and test the content
        def response_content(url, request):
            if 'hooks.example.com' in url.geturl():
                payload = json.loads(request.body)
                attachment = payload['attachments'][0]
                self.assertIsNotNone(attachment)
                self.assertIsNone(attachment['image_url'])
                return response(200)

        # send POSTs to the bot to request the definitions
        with HTTMock(response_content):
            fake_response = self.post_command(text=u'EW')
            self.assertTrue(fake_response.status_code in range(200, 299), fake_response.status_code)
            fake_response = self.post_command(text=u'FW')
            self.assertTrue(fake_response.status_code in range(200, 299), fake_response.status_code)
            fake_response = self.post_command(text=u'GW')
            self.assertTrue(fake_response.status_code in range(200, 299), fake_response.status_code)
            fake_response = self.post_command(text=u'HW')
            self.assertTrue(fake_response.status_code in range(200, 299), fake_response.status_code)

if __name__ == '__main__':
    unittest.main()
