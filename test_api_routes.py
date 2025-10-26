#!/usr/bin/env python3
"""
Test script for hierarchical preset API routes

This script tests all the new API endpoints to verify they work correctly.
Run this after starting the Flask app with ENABLE_HIERARCHICAL_PRESETS=true.

Usage:
    1. Start the app: python prompt_generator.py
    2. In another terminal: python test_api_routes.py
"""

import json
import sys

import pytest
import requests

pytestmark = pytest.mark.skip("Integration script requires running server manually")

# Base URL for the Flask app
BASE_URL = "http://localhost:5000"

def test_route(method, endpoint, expected_status=200, description=""):
    """Test a single API route"""
    url = f"{BASE_URL}{endpoint}"

    print(f"\n{'='*70}")
    print(f"Testing: {method} {endpoint}")
    if description:
        print(f"Description: {description}")
    print(f"{'='*70}")

    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json={}, timeout=5)
        else:
            print(f"❌ Unsupported method: {method}")
            return False

        print(f"Status Code: {response.status_code}")

        if response.status_code != expected_status:
            print(f"❌ FAIL: Expected {expected_status}, got {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False

        # Try to parse JSON
        try:
            data = response.json()
            print(f"✅ PASS: Valid JSON response")

            # Show sample of response
            if isinstance(data, dict):
                if 'error' in data:
                    print(f"⚠️  Error response: {data.get('error')}")
                    print(f"   Message: {data.get('message')}")
                else:
                    # Show some keys
                    keys = list(data.keys())[:5]
                    print(f"Response keys: {keys}")

                    # Show counts for list responses
                    for key, value in data.items():
                        if isinstance(value, list):
                            print(f"  - {key}: {len(value)} items")
                        elif isinstance(value, dict):
                            print(f"  - {key}: {len(value)} keys")

            return True

        except json.JSONDecodeError:
            print(f"❌ FAIL: Invalid JSON response")
            print(f"Response: {response.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"❌ FAIL: Could not connect to {BASE_URL}")
        print(f"   Make sure the Flask app is running!")
        return False

    except requests.exceptions.Timeout:
        print(f"❌ FAIL: Request timed out")
        return False

    except Exception as e:
        print(f"❌ FAIL: Unexpected error: {e}")
        return False


def main():
    """Run all API route tests"""
    print("\n" + "="*70)
    print("HIERARCHICAL PRESET API ROUTES - TEST SUITE")
    print("="*70)

    # Check if server is running
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"✅ Flask app is running at {BASE_URL}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Flask app is NOT running at {BASE_URL}")
        print(f"\n   Please start the app first:")
        print(f"   1. Make sure ENABLE_HIERARCHICAL_PRESETS=true in .env")
        print(f"   2. Run: python prompt_generator.py")
        print(f"   3. Then run this test script again")
        sys.exit(1)

    # Track results
    results = []

    # Test 1: Get all categories (Level 1)
    results.append(test_route(
        "GET",
        "/api/categories",
        description="Get all main categories"
    ))

    # Test 2: Get types for photography (Level 2)
    results.append(test_route(
        "GET",
        "/api/categories/photography/types",
        description="Get photography types"
    ))

    # Test 3: Get artists for portrait photography (Level 3)
    results.append(test_route(
        "GET",
        "/api/categories/photography/types/portrait/artists",
        description="Get portrait photographers"
    ))

    # Test 4: Get technical options for Annie Leibovitz (Level 4)
    results.append(test_route(
        "GET",
        "/api/artists/photography/portrait/annie_leibovitz/technical",
        description="Get Annie Leibovitz technical options"
    ))

    # Test 5: Get scene specifics for Annie Leibovitz (Level 5)
    results.append(test_route(
        "GET",
        "/api/artists/photography/portrait/annie_leibovitz/specifics",
        description="Get Annie Leibovitz scene specifics"
    ))

    # Test 6: Get preset packs
    results.append(test_route(
        "GET",
        "/api/preset-packs",
        description="Get all preset packs"
    ))

    # Test 7: Get universal options
    results.append(test_route(
        "GET",
        "/api/universal-options",
        description="Get universal options"
    ))

    # Test 8: Test with Fantasy category
    results.append(test_route(
        "GET",
        "/api/categories/fantasy/types",
        description="Get fantasy types"
    ))

    # Test 9: Test with Fantasy > High Fantasy > Greg Rutkowski
    results.append(test_route(
        "GET",
        "/api/categories/fantasy/types/high_fantasy/artists",
        description="Get high fantasy artists"
    ))

    results.append(test_route(
        "GET",
        "/api/artists/fantasy/high_fantasy/greg_rutkowski/technical",
        description="Get Greg Rutkowski technical options"
    ))

    # Test 10: Test error handling (non-existent category)
    results.append(test_route(
        "GET",
        "/api/categories/nonexistent/types",
        expected_status=404,
        description="Test error handling for non-existent category"
    ))

    # Test 11: Test legacy /presets endpoint still works
    results.append(test_route(
        "GET",
        "/presets",
        description="Verify legacy /presets endpoint still works"
    ))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(results)
    total = len(results)

    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {total - passed} ❌")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nThe hierarchical preset API routes are working correctly!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED")
        print("\nPlease check the errors above and:")
        print("1. Verify ENABLE_HIERARCHICAL_PRESETS=true in .env")
        print("2. Verify hierarchical_presets.json exists")
        print("3. Check logs/app.log for errors")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
