"""
Comprehensive Chatbot Testing Suite
Tests accuracy using actual Q&A pairs from the knowledge base
"""

import requests
import json
import time
from typing import List, Dict

BASE_URL = "http://localhost:8000/api"
SESSION_ID = "test_accuracy_session"

# Test Q&A pairs from the knowledge base
TEST_CASES = [
    {
        "category": "Programme Overview",
        "question": "Tell me about the Intelligent Robotics programme",
        "expected_keywords": ["robotics", "intelligent", "automation", "AI"],
        "should_mention": ["programme", "robotics"]
    },
    {
        "category": "Programme Overview",
        "question": "What is Applied AI about?",
        "expected_keywords": ["AI", "artificial intelligence", "machine learning"],
        "should_mention": ["applied", "AI"]
    },
    {
        "category": "Course Details - ACE6313",
        "question": "What is ACE6313 about?",
        "expected_keywords": ["machine learning", "ACE6313"],
        "should_mention": ["ACE6313", "learning"]
    },
    {
        "category": "Course Details - ACE6323",
        "question": "Tell me about deep learning",
        "expected_keywords": ["deep learning", "neural networks"],
        "should_mention": ["deep", "learning"]
    },
    {
        "category": "Structure Query",
        "question": "What subjects are in Year 2 Trimester 1?",
        "expected_keywords": ["year 2", "trimester 1", "subjects"],
        "should_mention": ["year", "trimester"]
    },
    {
        "category": "Alias Resolution",
        "question": "What is machine learning fundamentals about?",
        "expected_keywords": ["ACE6313", "machine learning"],
        "should_mention": ["machine", "learning"]
    },
    {
        "category": "Mixed Query",
        "question": "What subjects in Year 3 and what is AI ethics?",
        "expected_keywords": ["year 3", "ethics", "ACE6253"],
        "should_mention": ["year", "ethics"]
    }
]

def test_chat(question: str) -> Dict:
    """Send a chat request and return the response."""
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "user_id": SESSION_ID,
                "message": question
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "answer": ""}
    except Exception as e:
        return {"error": str(e), "answer": ""}

def analyze_response(response: str, expected_keywords: List[str], should_mention: List[str]) -> Dict:
    """Analyze response quality."""
    response_lower = response.lower()
    
    # Check keyword presence
    keywords_found = [kw for kw in expected_keywords if kw.lower() in response_lower]
    keywords_missing = [kw for kw in expected_keywords if kw.lower() not in response_lower]
    
    # Check must-mention terms
    mentions_found = [term for term in should_mention if term.lower() in response_lower]
    mentions_missing = [term for term in should_mention if term.lower() not in response_lower]
    
    # Calculate score
    keyword_score = len(keywords_found) / len(expected_keywords) if expected_keywords else 0
    mention_score = len(mentions_found) / len(should_mention) if should_mention else 0
    overall_score = (keyword_score * 0.6 + mention_score * 0.4)
    
    # Determine quality
    if overall_score >= 0.7:
        quality = "✅ GOOD"
    elif overall_score >= 0.4:
        quality = "⚠️ FAIR"
    else:
        quality = "❌ POOR"
    
    return {
        "score": overall_score,
        "quality": quality,
        "keywords_found": keywords_found,
        "keywords_missing": keywords_missing,
        "mentions_found": mentions_found,
        "mentions_missing": mentions_missing,
        "response_length": len(response)
    }

def run_test_suite():
    """Run all test cases."""
    print("=" * 80)
    print("🧪 CHATBOT ACCURACY TEST SUITE")
    print("=" * 80)
    print()
    
    results = []
    total_score = 0
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(TEST_CASES)}: {test_case['category']}")
        print(f"{'='*80}")
        print(f"❓ Question: {test_case['question']}")
        print()
        
        # Send request
        response_data = test_chat(test_case['question'])
        
        if "error" in response_data:
            print(f"❌ ERROR: {response_data['error']}")
            results.append({
                "test": test_case['category'],
                "question": test_case['question'],
                "error": response_data['error'],
                "score": 0
            })
            continue
        
        answer = response_data.get('answer', '')
        
        # Analyze response
        analysis = analyze_response(
            answer,
            test_case['expected_keywords'],
            test_case['should_mention']
        )
        
        print(f"💬 Response ({analysis['response_length']} chars):")
        print(f"   {answer[:300]}{'...' if len(answer) > 300 else ''}")
        print()
        print(f"📊 Analysis:")
        print(f"   Quality: {analysis['quality']}")
        print(f"   Score: {analysis['score']:.2%}")
        print(f"   Keywords Found: {', '.join(analysis['keywords_found']) if analysis['keywords_found'] else 'None'}")
        print(f"   Keywords Missing: {', '.join(analysis['keywords_missing']) if analysis['keywords_missing'] else 'None'}")
        print(f"   Must-Mention Found: {', '.join(analysis['mentions_found']) if analysis['mentions_found'] else 'None'}")
        print(f"   Must-Mention Missing: {', '.join(analysis['mentions_missing']) if analysis['mentions_missing'] else 'None'}")
        
        results.append({
            "test": test_case['category'],
            "question": test_case['question'],
            "answer": answer,
            "analysis": analysis
        })
        
        total_score += analysis['score']
        
        # Rate limiting
        time.sleep(1)
    
    # Summary
    print(f"\n{'='*80}")
    print("📈 SUMMARY")
    print(f"{'='*80}")
    
    avg_score = total_score / len(TEST_CASES) if TEST_CASES else 0
    print(f"\n🎯 Overall Accuracy: {avg_score:.2%}")
    print(f"✅ Tests Passed (≥70%): {sum(1 for r in results if r.get('analysis', {}).get('score', 0) >= 0.7)}/{len(TEST_CASES)}")
    print(f"⚠️ Tests Fair (40-69%): {sum(1 for r in results if 0.4 <= r.get('analysis', {}).get('score', 0) < 0.7)}/{len(TEST_CASES)}")
    print(f"❌ Tests Failed (<40%): {sum(1 for r in results if r.get('analysis', {}).get('score', 0) < 0.4)}/{len(TEST_CASES)}")
    
    print(f"\n{'='*80}")
    print("🔍 ISSUES DETECTED")
    print(f"{'='*80}")
    
    poor_tests = [r for r in results if r.get('analysis', {}).get('score', 0) < 0.4]
    if poor_tests:
        print("\n❌ Tests with poor performance:")
        for test in poor_tests:
            print(f"   - {test['test']}: {test['question']}")
            if 'analysis' in test:
                print(f"     Missing: {', '.join(test['analysis']['keywords_missing'])}")
    else:
        print("\n✅ No major issues detected!")
    
    # Save results
    with open('test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed results saved to: test_results.json")
    print()
    
    return results, avg_score

if __name__ == "__main__":
    try:
        results, avg_score = run_test_suite()
        
        if avg_score < 0.5:
            print("\n⚠️ WARNING: Overall accuracy is below 50%")
            print("   This indicates the chatbot needs improvement.")
            print("   Possible issues:")
            print("   1. RAG system not properly integrated")
            print("   2. Knowledge base not indexed correctly")
            print("   3. Query routing not working")
        
    except KeyboardInterrupt:
        print("\n\n⏸️ Test suite interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
