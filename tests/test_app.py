"""
Tests for Flask application routes and functionality
"""

import pytest
import json


class TestAppInitialization:
    """Test Flask app initialization"""

    def test_app_exists(self, flask_app):
        """Verify Flask app is created"""
        assert flask_app is not None

    def test_app_is_testing_mode(self, flask_app):
        """Verify app is in testing mode"""
        assert flask_app.config['TESTING'] is True

    def test_app_has_secret_key(self, flask_app):
        """Verify app has a secret key configured"""
        assert flask_app.secret_key is not None


class TestIndexRoute:
    """Test the main index route"""

    def test_index_returns_200(self, client):
        """Verify GET / returns 200 status code"""
        response = client.get('/')
        assert response.status_code == 200

    def test_index_returns_html(self, client):
        """Verify GET / returns HTML content"""
        response = client.get('/')
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data


class TestPresetsRoute:
    """Test the /presets route"""

    def test_presets_returns_200(self, client):
        """Verify GET /presets returns 200 status code"""
        response = client.get('/presets')
        assert response.status_code == 200

    def test_presets_returns_json(self, client):
        """Verify GET /presets returns valid JSON"""
        response = client.get('/presets')
        assert response.content_type == 'application/json'

        # Verify it can be parsed as JSON
        data = json.loads(response.data)
        assert isinstance(data, dict)

    def test_presets_has_required_categories(self, client):
        """Verify /presets response has all required categories"""
        response = client.get('/presets')
        data = json.loads(response.data)

        required_categories = ['styles', 'artists', 'composition', 'lighting']
        for category in required_categories:
            assert category in data, f"Missing category: {category}"


class TestGenerateRoute:
    """Test the /generate route"""

    def test_generate_with_valid_input(self, client, monkeypatch):
        """Verify POST /generate with valid input"""
        # Mock the call_ollama function to avoid actual Ollama calls
        def mock_call_ollama(messages, model=None):
            return "Mocked prompt response"

        import prompt_generator
        monkeypatch.setattr(prompt_generator, 'call_ollama', mock_call_ollama)

        payload = {
            'input': 'a warrior in a forest',
            'model': 'flux',
            'style': 'None',
            'artist': 'None',
            'composition': 'None',
            'lighting': 'None'
        }

        response = client.post('/generate',
                                data=json.dumps(payload),
                                content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'result' in data
        assert 'model' in data

    def test_generate_without_input_returns_400(self, client):
        """Verify POST /generate without input returns 400"""
        payload = {
            'model': 'flux',
            'style': 'None',
            'artist': 'None',
            'composition': 'None',
            'lighting': 'None'
        }

        response = client.post('/generate',
                                data=json.dumps(payload),
                                content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data or 'message' in data

    def test_generate_with_empty_input_returns_400(self, client):
        """Verify POST /generate with empty input returns 400"""
        payload = {
            'input': '',
            'model': 'flux'
        }

        response = client.post('/generate',
                                data=json.dumps(payload),
                                content_type='application/json')

        assert response.status_code == 400

    def test_generate_without_json_returns_400(self, client):
        """Verify POST /generate without JSON content returns 400"""
        response = client.post('/generate',
                                data='not json',
                                content_type='text/plain')

        assert response.status_code == 400


class TestChatRoute:
    """Test the /chat route"""

    def test_chat_with_valid_message(self, client, monkeypatch):
        """Verify POST /chat with valid message"""
        # Mock the call_ollama function
        def mock_call_ollama(messages, model=None):
            return "Mocked chat response"

        import prompt_generator
        monkeypatch.setattr(prompt_generator, 'call_ollama', mock_call_ollama)

        payload = {
            'message': 'make it more dramatic',
            'model': 'flux',
            'style': 'None',
            'artist': 'None',
            'composition': 'None',
            'lighting': 'None'
        }

        response = client.post('/chat',
                                data=json.dumps(payload),
                                content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'result' in data
        assert 'model' in data

    def test_chat_without_message_returns_400(self, client):
        """Verify POST /chat without message returns 400"""
        payload = {
            'model': 'flux'
        }

        response = client.post('/chat',
                                data=json.dumps(payload),
                                content_type='application/json')

        assert response.status_code == 400

    def test_chat_with_empty_message_returns_400(self, client):
        """Verify POST /chat with empty message returns 400"""
        payload = {
            'message': '',
            'model': 'flux'
        }

        response = client.post('/chat',
                                data=json.dumps(payload),
                                content_type='application/json')

        assert response.status_code == 400


class TestResetRoute:
    """Test the /reset route"""

    def test_reset_returns_200(self, client):
        """Verify POST /reset returns 200 status code"""
        response = client.post('/reset')
        assert response.status_code == 200

    def test_reset_returns_json(self, client):
        """Verify POST /reset returns JSON"""
        response = client.post('/reset')
        assert response.content_type == 'application/json'

        data = json.loads(response.data)
        assert 'status' in data


class TestErrorHandling:
    """Test error handling"""

    def test_404_returns_json(self, client):
        """Verify 404 errors return JSON"""
        response = client.get('/nonexistent-route')
        assert response.status_code == 404

        # Should return JSON, not HTML
        assert response.content_type == 'application/json'

        data = json.loads(response.data)
        assert 'error' in data or 'message' in data

    def test_405_method_not_allowed(self, client):
        """Verify wrong HTTP method returns appropriate error"""
        # Try POST to / which only accepts GET
        response = client.post('/')
        assert response.status_code == 405
