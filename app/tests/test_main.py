from datetime import datetime
import unittest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.tests.mocks import mock_create_user_response, mock_create_user_payload, mock_get_user_response, mock_create_user_entry_response, mock_send_message_response, mock_message_payload, mock_entry_create_response


class TestCreateUser(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch('app.crud.get_user_by_phone_number')
    @patch('app.crud.create_user')
    def test_create_user_success(self, mock_create_user: Mock, mock_get_user: Mock):
        mock_get_user.return_value = None
        mock_create_user.return_value = mock_create_user_response

        response = self.client.post("/users/", json=mock_create_user_payload)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.json(), mock_create_user_response)

        mock_get_user.assert_called_once()
        args = mock_get_user.call_args[0]
        self.assertIsInstance(args[0], Session)
        self.assertEqual(args[1], "+16788973910")

    @patch('app.crud.get_user_by_phone_number')
    def test_create_user_already_exists(self, mock_get_user: Mock):
        mock_get_user.return_value = mock_create_user_response

        response = self.client.post("/users/", json=mock_create_user_payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("User already registered.", response.json()["detail"])


class TestCreateEntry(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch('app.crud.get_user_by_phone_number')
    @patch('app.tokenizer.embed')
    @patch('app.schemas.EntryCreate')
    @patch('app.crud.create_user_entry')
    @patch('app.crud.query_embeddings')
    @patch('app.helpers.generate_response')
    @patch('app.helpers.send_message')
    def test_create_entry_success(self, mock_send_message: Mock, mock_generate_response: Mock, mock_query_embeddings: Mock, mock_create_user_entry: Mock, mock_entry_create: Mock, mock_embed: Mock, mock_get_user: Mock):
        mock_get_user.return_value = mock_get_user_response
        mock_entry_create.return_value = mock_entry_create_response
        mock_create_user_entry.return_value = mock_create_user_entry_response
        mock_send_message.return_value = mock_send_message_response

        response = self.client.post("/entries/", json=mock_message_payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), mock_send_message_response)

        # crud.get_user_by_phone_number was called correctly
        mock_get_user.assert_called_once()
        args = mock_get_user.call_args[0]
        self.assertEqual(args[1], mock_message_payload["from_number"])

        # tokenizer.embed, crud.create_user_entry, crud_query_embeddings, and helpers.generate_response were called
        mock_embed.assert_called()
        mock_create_user_entry.assert_called_once()
        mock_query_embeddings.assert_called_once()
        mock_generate_response.assert_called_once()

        # crud.create_user_entry was called correctly
        args = mock_create_user_entry.call_args[0]
        self.assertEqual(args[1], mock_entry_create_response)

        # helpers.send_message was called correctly
        mock_send_message.assert_called_once()
        args = mock_create_user_entry.call_args[0]
        self.assertEqual(args[1], mock_send_message_response)
