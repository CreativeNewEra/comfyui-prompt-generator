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
        captured = {}

        def mock_call_ollama(messages, model=None):
            captured['messages'] = messages
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
        assert captured['messages'][0]['role'] == 'system'
        # Check for system message flexibility (different prompt variants)
        system_message = captured['messages'][0]['content']
        assert (
            'Flux' in system_message or
            'Avoid emitting a single "PROMPT:" response' in system_message or
            'NEVER output a single "PROMPT:"' in system_message
        )

        import prompt_generator

        with client.session_transaction() as flask_session:
            assert 'conversation_id' in flask_session
            assert 'conversation' not in flask_session
            conversation_id = flask_session['conversation_id']

        stored_conversation, stored_model = prompt_generator.conversation_store.get_conversation(conversation_id)
        assert stored_model == 'flux'
        assert any(message['role'] == 'assistant' for message in stored_conversation)

        cookies = response.headers.getlist('Set-Cookie')
        assert all('make+it+more+dramatic' not in cookie for cookie in cookies)

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


class TestHierarchicalSelections:
    """Tests that hierarchical selections reach the backend helpers."""

    @staticmethod
    def _sample_presets():
        return {
            'categories': {
                'photography': {
                    'name': 'Photography',
                    'level2_types': {
                        'portrait': {
                            'name': 'Portrait',
                            'level3_artists': {
                                'annie_leibovitz': {
                                    'name': 'Annie Leibovitz',
                                    'description': 'Iconic portrait photographer.',
                                    'signature': 'Bold lighting and dramatic poses.',
                                    'level4_technical': {
                                        'lighting': {
                                            'name': 'Lighting',
                                            'options': [
                                                {
                                                    'id': 'rembrandt',
                                                    'name': 'Rembrandt lighting',
                                                    'description': 'Classic triangle lighting setup.'
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            'preset_packs': {'packs': []},
            'universal_options': {},
            'quality_tags': {'flux': {}, 'sdxl': {}}
        }

    @staticmethod
    def _sample_selections():
        return {
            'level1': 'photography',
            'level2': 'portrait',
            'level3': 'annie_leibovitz',
            'level4': {'lighting': 'rembrandt'},
            'level5': {'subject': 'warrior princess'},
            'universal': {'mood': ['dramatic', 'elegant']}
        }

    def test_generate_uses_hierarchical_prompt(self, client, monkeypatch):
        import prompt_generator

        selections = self._sample_selections()
        captured = {}

        def fake_load_presets():
            captured['load_called'] = True
            return self._sample_presets()

        def fake_call_ollama(messages, model=None, stream=False):
            captured['messages'] = messages
            return 'Mocked hierarchical response'

        monkeypatch.setattr(prompt_generator, 'ENABLE_HIERARCHICAL_PRESETS', True)
        monkeypatch.setattr(prompt_generator, 'load_presets', fake_load_presets)
        monkeypatch.setattr(prompt_generator, 'call_ollama', fake_call_ollama)

        payload = {
            'input': 'A heroic figure in the forest',
            'model': 'flux',
            'selections': selections
        }

        response = client.post(
            '/generate',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 200
        assert captured.get('load_called') is True
        assert 'messages' in captured
        enhanced = captured['messages'][1]['content']
        assert 'Style: Photography > Portrait' in enhanced
        assert 'Mood: dramatic, elegant' in enhanced

        history = prompt_generator.get_history(limit=10)
        matching = next((item for item in history if item['user_input'] == payload['input']), None)
        assert matching is not None
        assert matching['presets'].get('hierarchical') == selections

    def test_chat_uses_hierarchical_prompt(self, client, monkeypatch):
        import prompt_generator

        selections = self._sample_selections()
        captured = {}

        def fake_load_presets():
            captured['load_called'] = True
            return self._sample_presets()

        def fake_call_ollama(messages, model=None, stream=False):
            captured['messages'] = messages
            return 'Mocked chat response'

        monkeypatch.setattr(prompt_generator, 'ENABLE_HIERARCHICAL_PRESETS', True)
        monkeypatch.setattr(prompt_generator, 'load_presets', fake_load_presets)
        monkeypatch.setattr(prompt_generator, 'call_ollama', fake_call_ollama)

        payload = {
            'message': 'Can you make it moodier?',
            'model': 'flux',
            'selections': selections
        }

        response = client.post(
            '/chat',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 200
        assert captured.get('load_called') is True
        assert 'messages' in captured
        chat_request = captured['messages'][1]['content']
        assert 'Style: Photography > Portrait' in chat_request

        with client.session_transaction() as flask_session:
            conversation_id = flask_session['conversation_id']

        stored_conversation, stored_model = prompt_generator.conversation_store.get_conversation(conversation_id)
        assert stored_model == 'flux'
        user_messages = [msg['content'] for msg in stored_conversation if msg['role'] == 'user']
        assert any('Style: Photography > Portrait' in message for message in user_messages)

        history = prompt_generator.get_history(limit=10)
        matching = next((item for item in history if item['user_input'] == payload['message']), None)
        assert matching is not None
        assert matching['presets'].get('hierarchical') == selections


class TestConversationStore:
    """Direct tests for the server-side conversation storage."""

    def test_conversation_store_trims_history(self):
        import prompt_generator

        store = prompt_generator.conversation_store
        system_message = {"role": "system", "content": "System instructions"}
        messages = [system_message]

        for index in range(40):
            messages.append({"role": "user", "content": f"user {index}"})
            messages.append({"role": "assistant", "content": f"assistant {index}"})

        session_id = store.create_session('flux', messages)
        stored_messages, stored_model = store.get_conversation(session_id)

        assert stored_model == 'flux'
        assert len(stored_messages) <= store.max_messages
        assert stored_messages[0]['role'] == 'system'
        assert stored_messages[0]['content'] == system_message['content']

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


class TestAdminSecurity:
    """Test security controls on admin endpoints"""

    def test_reload_prompts_rejects_unauthorized_request(self, client, monkeypatch):
        """Verify /admin/reload-prompts requires authentication"""
        import prompt_generator

        monkeypatch.setattr(prompt_generator, 'ADMIN_API_KEY', 'super-secret-key')

        response = client.post(
            '/admin/reload-prompts',
            environ_overrides={'REMOTE_ADDR': '203.0.113.10'}
        )

        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'forbidden'
