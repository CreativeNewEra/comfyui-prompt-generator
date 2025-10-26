"""
Tests for Flask application routes and functionality
"""

import copy
import json
import pytest


HIERARCHICAL_SAMPLE_SELECTIONS = {
    'level1': 'photography',
    'level2': 'portrait',
    'level3': 'annie_leibovitz',
    'level4': {
        'composition': 'dynamic_low_angle'
    },
    'universal': {
        'lighting': 'golden_hour',
        'mood': ['dramatic']
    }
}


def _first_valid_option(options):
    for key in options:
        if key != 'None':
            return key
    return 'None'


def _build_legacy_presets(presets):
    styles = presets.get('styles', {}) if isinstance(presets, dict) else {}
    artists = presets.get('artists', {}) if isinstance(presets, dict) else {}
    composition = presets.get('composition', {}) if isinstance(presets, dict) else {}
    lighting = presets.get('lighting', {}) if isinstance(presets, dict) else {}

    return {
        'style': _first_valid_option(styles),
        'artist': _first_valid_option(artists),
        'composition': _first_valid_option(composition),
        'lighting': _first_valid_option(lighting)
    }


def _build_hierarchical_presets():
    return copy.deepcopy(HIERARCHICAL_SAMPLE_SELECTIONS)


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

    def test_presets_has_required_categories(self, client, hierarchical_enabled):
        """Verify /presets response has all required categories"""
        response = client.get('/presets')
        data = json.loads(response.data)

        if hierarchical_enabled:
            assert 'categories' in data
            assert 'preset_packs' in data
            assert 'universal_options' in data
        else:
            required_categories = ['styles', 'artists', 'composition', 'lighting']
            for category in required_categories:
                assert category in data, f"Missing category: {category}"


class TestGenerateRoute:
    """Test the /generate route"""

    def test_generate_with_valid_input(self, client, monkeypatch, app_module, presets, hierarchical_enabled):
        """Verify POST /generate with valid input"""
        # Mock the call_ollama function to avoid actual Ollama calls
        captured = {}

        def mock_call_ollama(messages, model=None):
            captured['messages'] = messages
            return "Mocked prompt response"

        monkeypatch.setattr(app_module, 'call_ollama', mock_call_ollama)

        if hierarchical_enabled:
            selections = _build_hierarchical_presets()
            payload = {
                'input': 'a warrior in a forest',
                'model': 'flux',
                'selections': selections
            }
            legacy_presets = None
        else:
            legacy_presets = _build_legacy_presets(presets)
            payload = {
                'input': 'a warrior in a forest',
                'model': 'flux',
                **legacy_presets
            }

        response = client.post('/generate',
                                data=json.dumps(payload),
                                content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'result' in data
        assert 'model' in data

        assert 'messages' in captured
        messages = captured['messages']
        assert messages[1]['role'] == 'user'
        user_content = messages[1]['content']
        assert 'Selected presets' in user_content

        if hierarchical_enabled:
            assert 'Photography' in user_content
            assert 'Golden Hour' in user_content
        else:
            style_key = legacy_presets['style']
            style_text = presets['styles'].get(style_key)
            if style_text:
                assert style_text in user_content

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

    def test_generate_stream_with_presets(self, client, monkeypatch, app_module, presets, hierarchical_enabled):
        """Verify streaming generate handles presets in both modes"""
        captured = {}

        def mock_call_ollama(messages, model=None, stream=False):
            captured['messages'] = messages

            if stream:
                def _gen():
                    for token in ['Hello']:
                        yield token
                return _gen()

            return "Mocked prompt response"

        monkeypatch.setattr(app_module, 'call_ollama', mock_call_ollama)

        if hierarchical_enabled:
            selections = _build_hierarchical_presets()
            payload = {
                'input': 'explore the stars',
                'model': 'flux',
                'selections': selections
            }
            legacy_presets = None
        else:
            legacy_presets = _build_legacy_presets(presets)
            payload = {
                'input': 'explore the stars',
                'model': 'flux',
                **legacy_presets
            }

        response = client.post('/generate-stream',
                                data=json.dumps(payload),
                                content_type='application/json')

        assert response.status_code == 200
        chunks = []
        for chunk in response.response:
            if isinstance(chunk, bytes):
                chunks.append(chunk.decode('utf-8'))
            else:
                chunks.append(chunk)
        combined = ''.join(chunks)
        assert 'data:' in combined

        user_content = captured['messages'][1]['content']
        assert 'Selected presets' in user_content

        if hierarchical_enabled:
            assert 'Photography' in user_content
        else:
            style_key = legacy_presets['style']
            style_text = presets['styles'].get(style_key)
            if style_text:
                assert style_text in user_content


class TestChatRoute:
    """Test the /chat route"""

    def test_chat_with_valid_message(self, client, monkeypatch, app_module, presets, hierarchical_enabled):
        """Verify POST /chat with valid message"""
        # Mock the call_ollama function
        captured = {}

        def mock_call_ollama(messages, model=None):
            captured['messages'] = messages
            return "Mocked chat response"

        monkeypatch.setattr(app_module, 'call_ollama', mock_call_ollama)

        if hierarchical_enabled:
            selections = _build_hierarchical_presets()
            payload = {
                'message': 'make it more dramatic',
                'model': 'flux',
                'selections': selections
            }
            legacy_presets = None
        else:
            legacy_presets = _build_legacy_presets(presets)
            payload = {
                'message': 'make it more dramatic',
                'model': 'flux',
                **legacy_presets
            }

        response = client.post('/chat',
                                data=json.dumps(payload),
                                content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'result' in data
        assert 'model' in data
        assert captured['messages'][0]['role'] == 'system'
        assert 'creative brainstorming partner' in captured['messages'][0]['content']

        user_entry = captured['messages'][1]['content']
        if hierarchical_enabled:
            assert 'Golden Hour' in user_entry
        else:
            style_key = legacy_presets['style']
            style_text = presets['styles'].get(style_key)
            if style_text:
                assert style_text in user_entry

    def test_chat_without_message_returns_400(self, client):
        """Verify POST /chat without message returns 400"""
        payload = {
            'model': 'flux'
        }

        response = client.post('/chat',
                                data=json.dumps(payload),
                                content_type='application/json')

        assert response.status_code == 400

    def test_chat_stream_with_presets(self, client, monkeypatch, app_module, presets, hierarchical_enabled):
        """Verify streaming chat handles presets across modes"""
        captured = {}

        def mock_call_ollama(messages, model=None, stream=False):
            captured['messages'] = messages

            if stream:
                def _gen():
                    for token in ['Hi there']:
                        yield token
                return _gen()

            return "Mocked chat response"

        monkeypatch.setattr(app_module, 'call_ollama', mock_call_ollama)

        if hierarchical_enabled:
            selections = _build_hierarchical_presets()
            payload = {
                'message': 'hello there',
                'model': 'flux',
                'selections': selections
            }
            legacy_presets = None
        else:
            legacy_presets = _build_legacy_presets(presets)
            payload = {
                'message': 'hello there',
                'model': 'flux',
                **legacy_presets
            }

        response = client.post('/chat-stream',
                                data=json.dumps(payload),
                                content_type='application/json')

        assert response.status_code == 200
        chunks = []
        for chunk in response.response:
            if isinstance(chunk, bytes):
                chunks.append(chunk.decode('utf-8'))
            else:
                chunks.append(chunk)
        combined = ''.join(chunks)
        assert 'data:' in combined

        user_message = captured['messages'][1]['content']
        if hierarchical_enabled:
            assert 'Golden Hour' in user_message
        else:
            style_key = legacy_presets['style']
            style_text = presets['styles'].get(style_key)
            if style_text:
                assert style_text in user_message

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
