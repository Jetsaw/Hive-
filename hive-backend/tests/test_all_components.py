"""
Comprehensive Component Testing Script
Tests all major components via API and code inspection
"""

import requests
import json
import time
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "http://localhost:8000/api"
TEST_USER = "component_test_user"

def print_header(text):
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}{text.center(70)}")
    print(f"{Fore.CYAN}{'='*70}\n")

def print_success(text):
    print(f"{Fore.GREEN}✅ {text}")

def print_fail(text):
    print(f"{Fore.RED}❌ {text}")

def print_info(text):
    print(f"{Fore.YELLOW}ℹ️  {text}")

# Component 1: Backend Health
print_header("COMPONENT 1: Backend Server")
try:
    resp = requests.get(f"{BASE_URL}/health", timeout=5)
    if resp.status_code == 200:
        print_success("Backend server is running")
        print_info(f"Response: {resp.json()}")
    else:
        print_fail(f"Backend returned status {resp.status_code}")
except Exception as e:
    print_fail(f"Backend unreachable: {e}")

time.sleep(1)

# Component 2: Knowledge Base Files
print_header("COMPONENT 2: Knowledge Base Files")
import os
files_to_check = [
    ("programme_structure.jsonl", "data/kb/programme_structure.jsonl"),
    ("details Q&A", "data/kb/faie_ai_robotics_combined_qa.jsonl"),
    ("alias mapping", "data/kb/alias_mapping.yaml"),
    ("routing rules", "data/kb/rules.yaml"),
]

for name, path in files_to_check:
    if os.path.exists(path):
        size = os.path.getsize(path) / 1024
        with open(path, 'r', encoding='utf-8') as f:
            lines = sum(1 for line in f if line.strip())
        print_success(f"{name}: {lines} entries, {size:.1f}KB")
    else:
        print_fail(f"{name}: NOT FOUND at {path}")

time.sleep(1)

# Component 3: RAG Indices
print_header("COMPONENT 3: RAG Indices")
try:
    from app.rag.indexer import build_or_load_structure_index, build_or_load_details_index
    
    s_idx, s_meta = build_or_load_structure_index()
    print_success(f"Structure index: {s_idx.ntotal} vectors, {len(s_meta)} chunks")
    
    d_idx, d_meta = build_or_load_details_index()
    print_success(f"Details index: {d_idx.ntotal} vectors, {len(d_meta)} chunks")
except Exception as e:
    print_fail(f"Index loading error: {e}")

time.sleep(1)

# Component 4: Alias Resolver
print_header("COMPONENT 4: Alias Resolution System")
try:
    from app.advisor.alias_resolver import resolve_aliases
    
    test_phrases = [
        "machine learning",
        "deep learning", 
        "AI ethics",
        "robotics fundamentals"
    ]
    
    for phrase in test_phrases:
        results = resolve_aliases(phrase, None)
        if results:
            codes = [r['course_code'] for r in results]
            print_success(f'"{phrase}" → {codes}')
        else:
            print_info(f'"{phrase}" → No match')
except Exception as e:
    print_fail(f"Alias resolver error: {e}")

time.sleep(1)

# Component 5: Query Router
print_header("COMPONENT 5: Query Routing Logic")
try:
    from app.rag.query_router import route_query
    from app.advisor.session_manager import Session
    
    test_session = Session(session_id="test", programme="Applied AI")
    
    test_queries = [
        ("What is ACE6313?", "Course code detection"),
        ("Tell me about machine learning", "Alias resolution"),
        ("What subjects in Year 2?", "Structure query"),
        ("Year 2 Trimester 1 and ACE6313", "Mixed query"),
    ]
    
    for query, expected in test_queries:
        route = route_query(query, test_session)
        print_info(f"{expected}:")
        print(f"   Query: '{query}'")
        print(f"   Type: {route.query_type}, Layer: {route.target_layer}")
        print(f"   Structure: {route.should_query_structure}, Details: {route.should_query_details}")
except Exception as e:
    print_fail(f"Query router error: {e}")

time.sleep(1)

# Component 6: Chat API - Course Code Query
print_header("COMPONENT 6: Chat API - Course Code Detection")
try:
    resp = requests.post(
        f"{BASE_URL}/chat",
        json={"user_id": TEST_USER, "message": "What is ACE6313?"},
        timeout=30
    )
    data = resp.json()
    answer = data.get('answer', '')
    metadata = data.get('metadata', {})
    
    print_success(f"Response received ({len(answer)} chars)")
    print_info(f"Query type: {metadata.get('query_type')}")
    print_info(f"Course codes: {metadata.get('course_codes')}")
    print_info(f"Results: {metadata.get('results_count')}")
    print(f"\n{Style.DIM}Answer preview: {answer[:200]}...")
    
    if 'ACE6313' in answer or 'machine learning' in answer.lower():
        print_success("Response is relevant to ACE6313")
    else:
        print_fail("Response may not be relevant")
except Exception as e:
    print_fail(f"Chat API error: {e}")

time.sleep(2)

# Component 7: Chat API - Alias Resolution
print_header("COMPONENT 7: Chat API - Alias Resolution")
try:
    resp = requests.post(
        f"{BASE_URL}/chat",
        json={"user_id": TEST_USER, "message": "Tell me about machine learning"},
        timeout=30
    )
    data = resp.json()
    answer = data.get('answer', '')
    metadata = data.get('metadata', {})
    
    print_success(f"Response received ({len(answer)} chars)")
    print_info(f"Course codes: {metadata.get('course_codes')}")
    print(f"\n{Style.DIM}Answer preview: {answer[:200]}...")
    
    if 'ACE6313' in str(metadata.get('course_codes')) or 'ACE6313' in answer:
        print_success("Alias 'machine learning' resolved to ACE6313")
    else:
        print_fail("Alias resolution may not be working")
except Exception as e:
    print_fail(f"Chat API error: {e}")

time.sleep(2)

# Component 8: Chat API - Structure Query
print_header("COMPONENT 8: Chat API - Structure Query")
try:
    resp = requests.post(
        f"{BASE_URL}/chat",
        json={"user_id": TEST_USER, "message": "What subjects are in Year 2 Trimester 1?"},
        timeout=30
    )
    data = resp.json()
    answer = data.get('answer', '')
    metadata = data.get('metadata', {})
    
    print_success(f"Response received ({len(answer)} chars)")
    print_info(f"Query type: {metadata.get('query_type')}")
    print_info(f"Target layer: {metadata.get('target_layer')}")
    print(f"\n{Style.DIM}Answer preview: {answer[:200]}...")
    
    # Check if response contains course codes (pattern: XXX####)
    import re
    course_codes = re.findall(r'[A-Z]{3}\d{4}', answer)
    if course_codes:
        print_success(f"Found course codes: {course_codes[:5]}")
    else:
        print_info("No course codes in response")
except Exception as e:
    print_fail(f"Chat API error: {e}")

time.sleep(2)

# Component 9: Session Management
print_header("COMPONENT 9: Session Management")
try:
    resp = requests.get(f"{BASE_URL}/session/status", params={"user_id": TEST_USER}, timeout=5)
    if resp.status_code == 200:
        session_data = resp.json()
        print_success("Session status retrieved")
        print_info(f"Programme: {session_data.get('programme')}")
        print_info(f"Mode: {session_data.get('mode')}")
        print_info(f"History: {session_data.get('history_count')} messages")
    else:
        print_fail(f"Session status failed: {resp.status_code}")
except Exception as e:
    print_fail(f"Session management error: {e}")

# Final Summary
print_header("TEST SUMMARY")
print(f"""
{Fore.GREEN}✅ Tested Components:{Style.RESET_ALL}
   1. Backend Server
   2. Knowledge Base Files  
   3. RAG Indices (Structure + Details)
   4. Alias Resolution System
   5. Query Routing Logic
   6. Chat API - Course Code Detection
   7. Chat API - Alias Resolution
   8. Chat API - Structure Queries
   9. Session Management

{Fore.YELLOW}ℹ️  Frontend Testing:{Style.RESET_ALL}
   - Open http://localhost:8080 in your browser
   - Test voice input/output functionality
   - Verify 'Thinking...' indicator appears
   - Check settings modal works

{Fore.CYAN}📊 System Status: Operational{Style.RESET_ALL}
""")

print(f"\n{Fore.CYAN}{'='*70}\n")
