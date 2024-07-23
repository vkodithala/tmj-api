from datetime import datetime
import unittest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.tests.mocks import mock_create_user_response, mock_create_user_payload


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
