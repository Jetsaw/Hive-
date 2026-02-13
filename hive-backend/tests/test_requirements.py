"""
Comprehensive Test Suite - Verify All Requirements
Tests the chatbot via API calls to validate requirements
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def test_requirement_checks():
    """Test all user requirements"""
    print("="*80)
    print("🧪 REQUIREMENT VERIFICATION TEST SUITE")
    print("="*80)
    print()
    
    results = {
        "tests_passed": 0,
        "tests_failed": 0,
        "details": []
    }
    
    # Test 1: Backend is running
    print("Test 1: Backend Health Check")
    print("-" * 80)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running on port 8000")
            results["tests_passed"] += 1
            results["details"].append({"test": "Backend Health", "status": "PASS"})
        else:
            print(f"❌ Backend returned status {response.status_code}")
            results["tests_failed"] += 1
            results["details"].append({"test": "Backend Health", "status": "FAIL"})
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        results["tests_failed"] += 1
        results["details"].append({"test": "Backend Health", "status": "FAIL", "error": str(e)})
    print()
    
    # Test 2: RAG System - Programme Structure Query
    print("Test 2: RAG System - Structure Layer")
    print("-" * 80)
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"user_id": "test_req_1", "message": "Tell me about the Intelligent Robotics programme"},
            timeout=30
        )
        data = response.json()
        answer = data.get('answer', '')
        
        # Check if answer contains relevant keywords
        has_robotics = 'robotics' in answer.lower() or 'robot' in answer.lower()
        has_programme = 'programme' in answer.lower() or 'program' in answer.lower()
        is_relevant = has_robotics and has_programme and len(answer) > 100
        
        if is_relevant:
            print("✅ Structure query returns relevant answer")
            print(f"   Answer length: {len(answer)} chars")
            print(f"   Contains 'robotics': {has_robotics}")
            print(f"   Contains 'programme': {has_programme}")
            print(f"   Preview: {answer[:150]}...")
            results["tests_passed"] += 1
            results["details"].append({
                "test": "Structure Layer Query", 
                "status": "PASS",
                "answer_length": len(answer)
            })
        else:
            print("❌ Structure query answer not relevant")
            print(f"   Answer: {answer[:200]}")
            results["tests_failed"] += 1
            results["details"].append({
                "test": "Structure Layer Query",
                "status": "FAIL",
                "answer": answer[:200]
            })
    except Exception as e:
        print(f"❌ Structure query failed: {e}")
        results["tests_failed"] += 1
        results["details"].append({"test": "Structure Layer Query", "status": "ERROR", "error": str(e)})
    print()
    time.sleep(2)
    
    # Test 3: RAG System - Alias Resolution
    print("Test 3: RAG System - Alias Resolution")
    print("-" * 80)
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"user_id": "test_req_2", "message": "What is machine learning about?"},
            timeout=30
        )
        data = response.json()
        answer = data.get('answer', '')
        metadata = data.get('metadata', {})
        
        # Check if alias was resolved to ACE6313
        course_codes = metadata.get('course_codes', [])
        has_ace6313 = 'ACE6313' in course_codes or 'ACE6313' in answer
        has_ml_content = 'machine learning' in answer.lower() or 'ml' in answer.lower()
        
        if has_ace6313 and has_ml_content:
            print("✅ Alias resolution working")
            print(f"   Resolved to: {course_codes}")
            print(f"   Answer mentions ML: {has_ml_content}")
            print(f"   Preview: {answer[:150]}...")
            results["tests_passed"] += 1
            results["details"].append({
                "test": "Alias Resolution",
                "status": "PASS",
                "resolved_to": course_codes
            })
        else:
            print("❌ Alias resolution not working")
            print(f"   Course codes: {course_codes}")
            print(f"   Answer: {answer[:200]}")
            results["tests_failed"] += 1
            results["details"].append({
                "test": "Alias Resolution",
                "status": "FAIL"
            })
    except Exception as e:
        print(f"❌ Alias resolution test failed: {e}")
        results["tests_failed"] += 1
        results["details"].append({"test": "Alias Resolution", "status": "ERROR", "error": str(e)})
    print()
    time.sleep(2)
    
    # Test 4: Course Code Detection
    print("Test 4: Course Code Detection")
    print("-" * 80)
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"user_id": "test_req_3", "message": "What is ACE6313?"},
            timeout=30
        )
        data = response.json()
        answer = data.get('answer', '')
        metadata = data.get('metadata', {})
        
        # Check if ACE6313 was detected
        course_codes = metadata.get('course_codes', [])
        has_course_code = 'ACE6313' in course_codes or 'ACE6313' in answer
        
        if has_course_code and len(answer) > 50:
            print("✅ Course code detection working")
            print(f"   Detected: {course_codes}")
            print(f"   Answer length: {len(answer)} chars")
            results["tests_passed"] += 1
            results["details"].append({
                "test": "Course Code Detection",
                "status": "PASS"
            })
        else:
            print("❌ Course code detection not working")
            print(f"   Answer: {answer[:200]}")
            results["tests_failed"] += 1
            results["details"].append({
                "test": "Course Code Detection",
                "status": "FAIL"
            })
    except Exception as e:
        print(f"❌ Course code detection failed: {e}")
        results["tests_failed"] += 1
        results["details"].append({"test": "Course Code Detection", "status": "ERROR", "error": str(e)})
    print()
    
    # Test 5: Check if new RAG system is being used
    print("Test 5: New RAG System Integration")
    print("-" * 80)
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"user_id": "test_req_4", "message": "Test query"},
            timeout=30
        )
        data = response.json()
        has_metadata = 'metadata' in data
        
        if has_metadata:
            metadata = data['metadata']
            print("✅ New RAG system is integrated")
            print(f"   Metadata available: {list(metadata.keys())}")
            print(f"   Programme: {metadata.get('programme')}")
            print(f"   Query type: {metadata.get('query_type')}")
            print(f"   Target layer: {metadata.get('target_layer')}")
            results["tests_passed"] += 1
            results["details"].append({
                "test": "New RAG Integration",
                "status": "PASS"
            })
        else:
            print("⚠️ New RAG system may not be fully integrated (no metadata)")
            results["tests_failed"] += 1
            results["details"].append({
                "test": "New RAG Integration",
                "status": "PARTIAL"
            })
    except Exception as e:
        print(f"❌ RAG system check failed: {e}")
        results["tests_failed"] += 1
        results["details"].append({"test": "New RAG Integration", "status": "ERROR", "error": str(e)})
    print()
    
    # Summary
    print("="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    total_tests = results["tests_passed"] + results["tests_failed"]
    pass_rate = (results["tests_passed"] / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n✅ Tests Passed: {results['tests_passed']}/{total_tests}")
    print(f"❌ Tests Failed: {results['tests_failed']}/{total_tests}")
    print(f"📈 Pass Rate: {pass_rate:.1f}%")
    
    if pass_rate >= 80:
        print("\n🎉 REQUIREMENTS MET - System is working as expected!")
    elif pass_rate >= 60:
        print("\n⚠️ PARTIAL SUCCESS - Most requirements met, some issues found")
    else:
        print("\n❌ REQUIREMENTS NOT MET - Significant issues found")
    
    print("\n" + "="*80)
    print("📝 FRONTEND REQUIREMENTS (Manual Testing Required)")
    print("="*80)
    print("\nSince browser testing is unavailable, please manually verify:")
    print()
    print("1. ✓ Text Input → Text-Only Response:")
    print("   - Open http://localhost:8080")
    print("   - Type a question in the text box")
    print("   - Press Enter or click Send")
    print("   - Verify: NO voice plays automatically")
    print()
    print("2. ✓ Voice Input → Text + Voice Response:")
    print("   - Click the microphone button")
    print("   - Speak a question")
    print("   - Verify: Voice playback DOES occur after response")
    print()
    print("3. ✓ Thinking Indicator:")
    print("   - Send any query")
    print("   - Verify: 'Thinking...' message appears with animated dots")
    print("   - Verify: Message disappears when response arrives")
    print()
    
    # Save results
    with open('requirement_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("💾 Test results saved to: requirement_test_results.json")
    print()
    
    return results

if __name__ == "__main__":
    try:
        results = test_requirement_checks()
    except KeyboardInterrupt:
        print("\n⏸️ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
