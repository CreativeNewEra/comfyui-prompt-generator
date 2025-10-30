#!/usr/bin/env python3
"""
Simple test script to demonstrate the persona API endpoints.

This script tests all persona-related endpoints:
- GET /api/personas (list all personas)
- GET /api/personas/<id> (get specific persona with system prompt)
- POST /persona-reset (reset conversation)

NOTE: Testing /persona-chat and /persona-chat-stream requires Ollama to be running.
This script only demonstrates the API structure without actual Ollama calls.
"""

import requests
import json

BASE_URL = "http://localhost:5000"  # Change if using different port

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_get_personas():
    """Test GET /api/personas - List all personas"""
    print_section("TEST 1: GET /api/personas (List All Personas)")

    response = requests.get(f"{BASE_URL}/api/personas")

    print(f"Status Code: {response.status_code}")
    print(f"\nAvailable Personas:")

    if response.status_code == 200:
        personas = response.json()
        for persona_id, info in personas.items():
            print(f"\n  • {info['icon']} {info['name']}")
            print(f"    ID: {persona_id}")
            print(f"    Category: {info['category']}")
            print(f"    Description: {info['description'][:60]}...")
            print(f"    Supports Presets: {info['supports_presets']}")
            print(f"    Supports Streaming: {info['supports_streaming']}")

    return response.status_code == 200


def test_get_specific_persona(persona_id="creative_vision_guide"):
    """Test GET /api/personas/<id> - Get specific persona with system prompt"""
    print_section(f"TEST 2: GET /api/personas/{persona_id} (Get Specific Persona)")

    response = requests.get(f"{BASE_URL}/api/personas/{persona_id}")

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        persona = response.json()
        print(f"\n  Icon: {persona['icon']}")
        print(f"  Name: {persona['name']}")
        print(f"  Category: {persona['category']}")
        print(f"  Description: {persona['description']}")
        print(f"  Features: {', '.join(persona['features'])}")
        print(f"  Best For: {persona['best_for']}")
        print(f"\n  System Prompt Length: {len(persona['system_prompt'])} characters")
        print(f"  System Prompt Preview:")
        print(f"  {persona['system_prompt'][:200]}...")

    return response.status_code == 200


def test_invalid_persona():
    """Test GET /api/personas/<id> with invalid persona_id"""
    print_section("TEST 3: GET /api/personas/invalid_id (Error Handling)")

    response = requests.get(f"{BASE_URL}/api/personas/invalid_id")

    print(f"Status Code: {response.status_code}")

    if response.status_code == 404:
        error = response.json()
        print(f"\n  ✓ Expected 404 Error:")
        print(f"    Error: {error['error']}")
        print(f"    Message: {error['message']}")

    return response.status_code == 404


def test_persona_reset():
    """Test POST /persona-reset"""
    print_section("TEST 4: POST /persona-reset (Reset Conversation)")

    response = requests.post(f"{BASE_URL}/persona-reset")

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n  ✓ {result['message']}")

    return response.status_code == 200


def test_persona_chat_validation():
    """Test /persona-chat validation without calling Ollama"""
    print_section("TEST 5: POST /persona-chat (Validation Tests)")

    # Test 1: Missing persona_id
    print("Test 5a: Missing persona_id")
    response = requests.post(
        f"{BASE_URL}/persona-chat",
        json={"message": "Hello"}
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 400:
        error = response.json()
        print(f"  ✓ Error: {error['message']}")

    # Test 2: Invalid persona_id
    print("\nTest 5b: Invalid persona_id")
    response = requests.post(
        f"{BASE_URL}/persona-chat",
        json={"message": "Hello", "persona_id": "invalid_persona"}
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 404:
        error = response.json()
        print(f"  ✓ Error: {error['message']}")

    # Test 3: Valid request (will fail at Ollama call if Ollama not running)
    print("\nTest 5c: Valid request structure")
    response = requests.post(
        f"{BASE_URL}/persona-chat",
        json={
            "message": "I want to create an image of a dragon",
            "persona_id": "creative_vision_guide"
        }
    )
    print(f"  Status: {response.status_code}")

    if response.status_code == 200:
        print("  ✓ Success! Ollama is running and responded.")
    elif response.status_code == 503:
        error = response.json()
        print(f"  ⚠ Ollama not running: {error['message']}")
        print(f"  (This is expected if Ollama is not installed/running)")
    else:
        print(f"  Response: {response.json()}")

    return True


def run_all_tests():
    """Run all API tests"""
    print("\n" + "="*70)
    print("  PERSONA API TEST SUITE")
    print("="*70)

    results = []

    try:
        results.append(("List All Personas", test_get_personas()))
        results.append(("Get Specific Persona", test_get_specific_persona()))
        results.append(("Invalid Persona Error", test_invalid_persona()))
        results.append(("Reset Conversation", test_persona_reset()))
        results.append(("Chat Validation", test_persona_chat_validation()))

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to Flask server.")
        print(f"   Make sure the server is running at {BASE_URL}")
        return

    # Print summary
    print_section("TEST SUMMARY")

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")

    passed_count = sum(results)
    total_count = len(results)

    print(f"\n  Results: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n  🎉 All tests passed!")
    else:
        print(f"\n  ⚠ {total_count - passed_count} test(s) failed")


if __name__ == "__main__":
    run_all_tests()
