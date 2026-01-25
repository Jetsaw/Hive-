"""
Comprehensive Diagnostic Script
Checks all components of the RAG system
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def check_health():
    print_section("1. BACKEND HEALTH CHECK")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            print("✅ Backend is healthy")
            print(f"   Response: {resp.json()}")
            return True
        else:
            print(f"❌ Backend returned {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not reachable: {e}")
        return False

def check_indices():
    print_section("2. CHECKING INDICES")
    try:
        from app.rag.indexer import build_or_load_structure_index, build_or_load_details_index
        
        print("Loading structure index...")
        s_idx, s_meta = build_or_load_structure_index()
        print(f"✅ Structure index: {s_idx.ntotal} vectors, {len(s_meta)} metadata entries")
        
        print("Loading details index...")
        d_idx, d_meta = build_or_load_details_index()
        print(f"✅ Details index: {d_idx.ntotal} vectors, {len(d_meta)} metadata entries")
        
        if s_idx.ntotal == 0:
            print("⚠️  WARNING: Structure index is EMPTY!")
            return False
        if d_idx.ntotal == 0:
            print("⚠️  WARNING: Details index is EMPTY!")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error loading indices: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_knowledge_base():
    print_section("3. CHECKING KNOWLEDGE BASE FILES")
    import os
    
    files = [
        "data/kb/programme_structure.jsonl",
        "data/kb/faie_ai_robotics_combined_qa.jsonl",
        "data/kb/alias_mapping.yaml",
        "data/kb/rules.yaml"
    ]
    
    all_ok = True
    for f in files:
        if os.path.exists(f):
            size = os.path.getsize(f)
            # Count lines
            with open(f, 'r', encoding='utf-8') as file:
                lines = sum(1 for line in file if line.strip())
            print(f"✅ {f}: {size} bytes, {lines} entries")
        else:
            print(f"❌ {f}: NOT FOUND")
            all_ok = False
    
    return all_ok

def test_chat_query(query, description):
    print(f"\n   Testing: {description}")
    print(f"   Query: '{query}'")
    try:
        resp = requests.post(
            f"{BASE_URL}/chat",
            json={"user_id": "diagnostic_test", "message": query},
            timeout=30
        )
        data = resp.json()
        answer = data.get('answer', '')
        metadata = data.get('metadata', {})
        
        print(f"   Status: {resp.status_code}")
        print(f"   Query Type: {metadata.get('query_type', 'N/A')}")
        print(f"   Target Layer: {metadata.get('target_layer', 'N/A')}")
        print(f"   Course Codes: {metadata.get('course_codes', [])}")
        print(f"   Results Count: {metadata.get('results_count', 0)}")
        print(f"   Answer Length: {len(answer)} chars")
        print(f"   Answer Preview: {answer[:150]}...")
        
        return {
            "success": resp.status_code == 200 and len(answer) > 50,
            "answer": answer,
            "metadata": metadata
        }
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"success": False, "error": str(e)}

def check_chat_functionality():
    print_section("4. TESTING CHAT API")
    
    tests = [
        ("What is ACE6313?", "Course Code Detection"),
        ("Tell me about machine learning", "Alias Resolution"),
        ("What subjects are in Year 2 Trimester 1?", "Structure Query"),
        ("Tell me about the Intelligent Robotics programme", "Programme Overview"),
    ]
    
    results = []
    for query, desc in tests:
        result = test_chat_query(query, desc)
        results.append((desc, result))
    
    passed = sum(1 for _, r in results if r.get('success', False))
    print(f"\n   Passed: {passed}/{len(tests)}")
    return passed >= 2  # At least 2 should pass

def check_query_router():
    print_section("5. CHECKING QUERY ROUTER")
    try:
        from app.rag.query_router import route_query
        from app.advisor.session_manager import Session
        
        test_session = Session(session_id="test", programme="Applied AI")
        
        tests = [
            ("What is ACE6313?", "Should detect course code"),
            ("Tell me about machine learning", "Should trigger alias lookup"),
            ("What subjects in Year 2?", "Should route to structure"),
        ]
        
        for query, expected in tests:
            route = route_query(query, test_session)
            print(f"   Query: '{query}'")
            print(f"   → Type: {route.query_type}, Layer: {route.target_layer}")
            print(f"   → Codes: {route.detected_course_codes}, Structure: {route.should_query_structure}, Details: {route.should_query_details}")
            print()
        
        return True
    except Exception as e:
        print(f"❌ Query router error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_alias_resolver():
    print_section("6. CHECKING ALIAS RESOLVER")
    try:
        from app.advisor.alias_resolver import resolve_aliases
        
        tests = [
            ("machine learning", None),
            ("deep learning", None),
            ("AI ethics", None),
        ]
        
        for query, programme in tests:
            result = resolve_aliases(query, programme)
            if result:
                print(f"   '{query}' → {[r['course_code'] for r in result]}")
            else:
                print(f"   '{query}' → No match")
        
        return True
    except Exception as e:
        print(f"❌ Alias resolver error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*60)
    print("  🔍 COMPREHENSIVE SYSTEM DIAGNOSTIC")
    print("="*60)
    
    results = {}
    
    results['health'] = check_health()
    results['kb_files'] = check_knowledge_base()
    results['indices'] = check_indices()
    results['query_router'] = check_query_router()
    results['alias_resolver'] = check_alias_resolver()
    results['chat'] = check_chat_functionality()
    
    print_section("DIAGNOSTIC SUMMARY")
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {name}: {status}")
    
    total_passed = sum(1 for v in results.values() if v)
    print(f"\n   Overall: {total_passed}/{len(results)} checks passed")
    
    if total_passed == len(results):
        print("\n🎉 All systems operational!")
    else:
        print("\n⚠️  Some issues detected - see details above")
    
    # Save results
    with open('diagnostic_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to diagnostic_results.json")

if __name__ == "__main__":
    main()
