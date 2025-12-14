# test_app.py
import unittest
import json
import xml.etree.ElementTree as ET
from app import app


class TestCRUDAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test client."""
        cls.client = app.test_client()
        cls.client.testing = True

    def tearDown(self):
        """Clean up test users after each test."""
        # We'll use a special email pattern to identify test records
        import mysql.connector
        from app import DB_CONFIG
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE email LIKE 'testuser+%%@example.com'")
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Cleanup warning: {e}")

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'CSE1 CRUD API', response.data)

    def test_get_users_json(self):
        response = self.client.get('/users')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.get_data(as_text=True))
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 20)

    def test_get_users_xml(self):
        response = self.client.get('/users?format=xml')
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/xml', response.content_type)
        xml_str = response.get_data(as_text=True)
        root = ET.fromstring(xml_str)
        self.assertEqual(root.tag, 'users')
        self.assertGreaterEqual(len(root), 20)

    def test_create_user_json(self):
        user_data = {
            "name": "Test User JSON",
            "email": "testuser+json@example.com",
            "age": 25
        }
        response = self.client.post('/users', json=user_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['name'], user_data['name'])
        self.assertEqual(data['email'], user_data['email'])

    def test_create_user_xml(self):
        user_data = {
            "name": "Test User XML",
            "email": "testuser+xml@example.com",
            "age": 30
        }
        response = self.client.post('/users?format=xml', json=user_data)
        self.assertEqual(response.status_code, 201)
        self.assertIn('application/xml', response.content_type)
        xml_str = response.get_data(as_text=True)
        root = ET.fromstring(xml_str)
        user = root.find('user')
        self.assertIsNotNone(user)
        self.assertEqual(user.find('name').text, user_data['name'])

    def test_duplicate_email(self):
        email = "testuser+dup@example.com"
        self.client.post('/users', json={"name": "A", "email": email, "age": 20})
        response = self.client.post('/users', json={"name": "B", "email": email, "age": 25})
        self.assertEqual(response.status_code, 409)

    def test_get_single_user(self):
        # Create
        resp = self.client.post('/users', json={
            "name": "Single",
            "email": "testuser+single@example.com",
            "age": 22
        })
        user_id = json.loads(resp.get_data(as_text=True))['id']

        # Retrieve
        resp2 = self.client.get(f'/users/{user_id}')
        self.assertEqual(resp2.status_code, 200)
        data = json.loads(resp2.get_data(as_text=True))
        self.assertEqual(data['id'], user_id)

    def test_update_user(self):
        # Create
        resp = self.client.post('/users', json={
            "name": "Old",
            "email": "testuser+update@example.com",
            "age": 40
        })
        user_id = json.loads(resp.get_data(as_text=True))['id']

        # Update
        update_resp = self.client.put(f'/users/{user_id}', json={
            "name": "Updated Name",
            "age": 45
        })
        self.assertEqual(update_resp.status_code, 200)
        data = json.loads(update_resp.get_data(as_text=True))
        self.assertEqual(data['name'], "Updated Name")
        self.assertEqual(data['age'], 45)

    def test_delete_user(self):
        # Create
        resp = self.client.post('/users', json={
            "name": "To Delete",
            "email": "testuser+delete@example.com",
            "age": 50
        })
        user_id = json.loads(resp.get_data(as_text=True))['id']

        # Delete
        del_resp = self.client.delete(f'/users/{user_id}')
        self.assertEqual(del_resp.status_code, 200)

        # Verify gone
        get_resp = self.client.get(f'/users/{user_id}')
        self.assertEqual(get_resp.status_code, 404)


if __name__ == '__main__':
    unittest.main()