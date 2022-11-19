import unittest
from flask import current_app
from app import app
import json


class TestWebApp(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.appctx = self.app.app_context()
        self.appctx.push()

    def tearDown(self):
        self.appctx.pop()
        self.app = None
        self.appctx = None

    # check if app is running or not
    def test_app(self):
        assert self.app is not None
        assert current_app == self.app

    def test_spotify_data_comming(self):
        response = self.app.test_client().get('/api/playlist', follow_redirects=True)
        assert  (response.status_code == 201)

    def test_spotify_search(self):
        response = self.app.test_client().get('/api/search?query="test"', follow_redirects=True)
        assert  (response.status_code == 201)
        assert len(json.loads(response.data)) == 1

    def test_login(self):
        response = self.app.test_client().get('/login', follow_redirects=True)
        assert (response.status_code == 200)

    def test_signup(self):
        response = self.app.test_client().get('/signup', follow_redirects=True)
        assert (response.status_code == 200)

    def test_index(self):
        response = self.app.test_client().get('/', follow_redirects=True)
        assert (response.status_code == 200)

