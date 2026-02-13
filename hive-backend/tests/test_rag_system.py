"""
Test script for the new RAG system.
Run this to test the dual-layer architecture.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_health():
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"✅ Health: {response.json()}\n")

def test_structure_query():
    """Test structure layer query."""
    print("🔍 Testing structure query: 'What subjects in Year 2 Trimester 1?'")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "question": "What subjects are in Year 2 Trimester 1?",
            "session_id": "test_session_1"
        }
    )
    result = response.json()
    print(f"✅ Response: {result.get('answer', '')[:200]}...\n")
    return result

def test_details_query_with_code():
    """Test details layer with explicit course code."""
    print("🔍 Testing details query: 'Tell me about ACE6313'")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "question": "Tell me about ACE6313",
            "session_id": "test_session_2"
        }
    )
    result = response.json()
    print(f"✅ Response: {result.get('answer', '')[:200]}...\n")
    return result

def test_alias_resolution():
    """Test alias resolution."""
    print("🔍 Testing alias resolution: 'What is machine learning about?'")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "question": "What is machine learning about?",
            "session_id": "test_session_3"
        }
    )
    result = response.json()
    print(f"✅ Response: {result.get('answer', '')[:200]}...\n")
    return result

def test_mixed_query():
    """Test mixed query (structure + details)."""
    print("🔍 Testing mixed query: 'What subjects in Year 3 and what is deep learning?'")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "question": "What subjects are in Year 3 Trimester 1 and what is deep learning about?",
            "session_id": "test_session_4"
        }
    )
    result = response.json()
    print(f"✅ Response: {result.get('answer', '')[:200]}...\n")
    return result

def test_programme_detection():
    """Test programme auto-detection."""
    print("🔍 Testing programme detection: 'I'm interested in robotics and drones'")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "question": "I'm interested in robotics and drones. What should I study?",
            "session_id": "test_session_5"
        }
    )
    result = response.json()
    print(f"✅ Response: {result.get('answer', '')[:200]}...\n")
    return result

def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("🚀 RAG SYSTEM TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        test_health()
        test_structure_query()
        test_details_query_with_code()
        test_alias_resolution()
        test_mixed_query()
        test_programme_detection()
        
        print("=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_all_tests()
