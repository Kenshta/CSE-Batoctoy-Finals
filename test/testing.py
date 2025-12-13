import unittest
import json
from app import app

class TestUsersAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_get_users_json(self):
        response = self.client.get('/users')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

    def test_get_users_xml(self):
        response = self.client.get('/users?format=xml')
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/xml', response.content_type)

    def test_create_user(self):
        new_user = {"name": "Test User", "email": "test@example.com", "age": 30}
        response = self.client.post('/users', json=new_user)
        self.assertIn(response.status_code, [201, 400])  # 400 if email exists

if __name__ == '__main__':
    unittest.main()