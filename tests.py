import unittest
import json
import os
import shutil
from app import main


class TestCase(unittest.TestCase):
    def setUp(self):
        main.app.config['WTF_CSRF_ENABLED'] = False
        self.app = main.app.test_client()
        self.users_path = main.users_path
        # Backup the original users file
        if os.path.exists(self.users_path):
            shutil.copy(self.users_path, self.users_path + ".bak")

        # Ensure we start with a known state if needed, but for now we just backup
        # Reload users to ensure clean state if previous tests modified it in memory
        with open(main.users_path, "r") as f:
            main.users = json.load(f)

    def tearDown(self):
        # Restore the original users file
        if os.path.exists(self.users_path + ".bak"):
            shutil.move(self.users_path + ".bak", self.users_path)
            # Reload users to restore in-memory state
            with open(main.users_path, "r") as f:
                main.users = json.load(f)

    def test_main_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Check if "User Manager" title is present (indicating HTML page)
        self.assertIn(b"User Manager", response.data)

    def test_users_page(self):
        response = self.app.get('/users', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Check if it returns JSON
        self.assertEqual(response.content_type, "application/json")

    def test_add_user(self):
        response = self.app.post('/add', data=dict(
            username="testuser",
            id="999",
            name="Test User",
            description="A temporary test user"
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"User testuser added successfully", response.data)

        # Verify user was actually added to the list
        self.assertIn("testuser", main.users)
        self.assertEqual(main.users["testuser"]["name"], "Test User")

    def test_edit_user(self):
        # First add a user to edit
        main.users["edituser"] = {"id": "888", "name": "Edit Me", "description": "Original"}
        main.save_users()

        response = self.app.post('/edit/edituser', data=dict(
            username="edituser",   # Field represents the hidden or displayed username
            id="888",
            name="Edited Name",
            description="Updated Description"
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"User edituser updated successfully", response.data)

        # Verify update
        self.assertEqual(main.users["edituser"]["name"], "Edited Name")

    def test_delete_user(self):
        # First add a user to delete
        main.users["deluser"] = {"id": "777", "name": "Delete Me", "description": "Bye"}
        main.save_users()

        response = self.app.post('/delete/deluser', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"User deluser deleted", response.data)

        # Verify deletion
        self.assertNotIn("deluser", main.users)


if __name__ == '__main__':
    unittest.main()
