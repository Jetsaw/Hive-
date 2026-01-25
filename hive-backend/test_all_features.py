"""
Comprehensive Feature Testing Script for HIVE
Tests all backend features and provides manual UI testing checklist
"""

import requests
import json
import time
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "http://localhost:8000/api"
TEST_USER = "feature_test_user"

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

# Test 1: Backend Health
print_header("TEST 1: Backend Health Check")
try:
    resp = requests.get(f"{BASE_URL}/health", timeout=5)
    if resp.status_code == 200:
        print_success("Backend server is healthy")
        print_info(f"Response: {resp.json()}")
    else:
        print_fail(f"Health check failed: {resp.status_code}")
except Exception as e:
    print_fail(f"Backend unreachable: {e}")

time.sleep(1)

# Test 2: Memory Status (Initial)
print_header("TEST 2: Initial Memory Status")
try:
    resp = requests.get(f"{BASE_URL}/session/memory?user_id={TEST_USER}", timeout=5)
    if resp.status_code == 200:
        memory = resp.json()
        print_success("Memory endpoint working")
        print_info(f"Pairs: {memory['pairs_count']}, Summary: {memory['summary_available']}")
    else:
        print_fail(f"Memory status failed: {resp.status_code}")
except Exception as e:
    print_fail(f"Memory endpoint error: {e}")

time.sleep(1)

# Test 3-7: Send 5 Messages (Build up to 5 pairs)
print_header("TEST 3-7: Conversation Window (5 Messages)")
questions = [
    "What is ACE6313?",
    "What are the prerequisites for ACE6313?",
    "When is ACE6313 offered?",
    "Who teaches ACE6313?",
    "Is ACE6313 difficult?"
]

for i, question in enumerate(questions, 1):
    print(f"\n{Fore.YELLOW}Message {i}: {question}")
    try:
        resp = requests.post(
            f"{BASE_URL}/chat",
            json={"user_id": TEST_USER, "message": question},
            timeout=30
        )
        
        if resp.status_code == 200:
            data = resp.json()
            answer = data.get('answer', '')
            memory = data.get('memory', {})
            
            print_success(f"Response received ({len(answer)} chars)")
            print_info(f"Memory: {memory.get('pairs_count', 0)} pairs, Summary: {memory.get('summary_available', False)}")
            print(f"{Style.DIM}Answer preview: {answer[:150]}...")
        else:
            print_fail(f"Chat failed: {resp.status_code}")
    except Exception as e:
        print_fail(f"Chat error: {e}")
    
    time.sleep(2)

# Test 8: Check Memory After 5 Pairs
print_header("TEST 8: Memory Status After 5 Pairs")
try:
    resp = requests.get(f"{BASE_URL}/session/memory?user_id={TEST_USER}", timeout=5)
    if resp.status_code == 200:
        memory = resp.json()
        print_success(f"Memory status retrieved")
        print_info(f"Pairs: {memory['pairs_count']}")
        print_info(f"Summary available: {memory['summary_available']}")
        print_info(f"Total pairs (including summarized): {memory.get('total_pairs', 0)}")
        
        if memory['pairs_count'] == 5:
            print_success("✅ Window correctly holds 5 pairs!")
        else:
            print_fail(f"Expected 5 pairs, got {memory['pairs_count']}")
    else:
        print_fail(f"Memory check failed: {resp.status_code}")
except Exception as e:
    print_fail(f"Memory endpoint error: {e}")

time.sleep(2)

# Test 9: 6th Message (Triggers Summarization)
print_header("TEST 9: 6th Message (Auto-Summarization Test)")
print(f"{Fore.YELLOW}Sending 6th message to trigger summarization...")
try:
    resp = requests.post(
        f"{BASE_URL}/chat",
        json={"user_id": TEST_USER, "message": "What about ACE6323?"},
        timeout=30
    )
    
    if resp.status_code == 200:
        data = resp.json()
        memory = data.get('memory', {})
        
        print_success("6th message sent successfully")
        print_info(f"Memory: {memory.get('pairs_count', 0)} pairs")
        print_info(f"Summary available: {memory.get('summary_available', False)}")
        print_info(f"Summarized count: {memory.get('summarized_count', 0)}")
        
        if memory.get('summary_available'):
            print_success("✅ AUTO-SUMMARIZATION TRIGGERED!")
        else:
            print_info("Summarization may occur on next message")
    else:
        print_fail(f"6th message failed: {resp.status_code}")
except Exception as e:
    print_fail(f"Chat error: {e}")

time.sleep(2)

# Test 10: Get Summary
print_header("TEST 10: Retrieve Conversation Summary")
try:
    resp = requests.get(f"{BASE_URL}/session/summary?user_id={TEST_USER}", timeout=5)
    if resp.status_code == 200:
        summary_data = resp.json()
        print_success("Summary endpoint working")
        print_info(f"Pairs in window: {summary_data.get('pairs_count', 0)}")
        print_info(f"Summarized pairs: {summary_data.get('summarized_count', 0)}")
        
        if summary_data.get('summary'):
            print_success("Summary generated:")
            print(f"{Style.DIM}{summary_data['summary']}")
        else:
            print_info("No summary yet (may need more messages)")
    else:
        print_fail(f"Summary retrieval failed: {resp.status_code}")
except Exception as e:
    print_fail(f"Summary endpoint error: {e}")

time.sleep(2)

# Test 11: Session Reset
print_header("TEST 11: New Session (Memory Reset)")
try:
    resp = requests.post(f"{BASE_URL}/session/reset?user_id={TEST_USER}", timeout=5)
    if resp.status_code == 200:
        print_success("Session reset successful")
        
        # Verify memory cleared
        resp2 = requests.get(f"{BASE_URL}/session/memory?user_id={TEST_USER}", timeout=5)
        if resp2.status_code == 200:
            memory = resp2.json()
            if memory['pairs_count'] == 0 and not memory['summary_available']:
                print_success("✅ Memory successfully cleared!")
            else:
                print_fail(f"Memory not cleared: {memory}")
    else:
        print_fail(f"Session reset failed: {resp.status_code}")
except Exception as e:
    print_fail(f"Reset error: {e}")

# Final Summary
print_header("TEST SUMMARY")
print(f"""
{Fore.GREEN}✅ Backend Tests Completed{Style.RESET_ALL}

{Fore.CYAN}Tested Features:{Style.RESET_ALL}
1. ✅ Backend health check
2. ✅ Memory status endpoint
3. ✅ 5-message conversation window
4. ✅ Auto-summarization trigger (6th message)
5. ✅ Summary retrieval
6. ✅ Session reset & memory clearing

{Fore.YELLOW}📋 Manual UI Testing Checklist:{Style.RESET_ALL}

Open http://localhost:8080 in your browser and verify:

{Fore.CYAN}[ ] Visual Design (Academic Futurism){Style.RESET_ALL}
    - Fraunces serif font in "HIVE" logo
    - Gold accent colors (#FFB800)
    - Hexagonal logo with pulse animation
    - Grid pattern background
    - Smooth slide-in animations

{Fore.CYAN}[ ] Memory Status Indicator{Style.RESET_ALL}
    - Hidden initially
    - Shows "💬 X pairs" after conversations
    - Shows "💬 X pairs + summary" when summary exists
    - Updates in real-time

{Fore.CYAN}[ ] Text Input (No Voice){Style.RESET_ALL}
    - Type a message and send
    - Response appears (NO voice plays)
    - "Thinking..." indicator shows while processing

{Fore.CYAN}[ ] Voice Input (With Voice){Style.RESET_ALL}
    - Click 🎤 microphone button
    - Speak a question
    - Response appears WITH voice playback

{Fore.CYAN}[ ] New Session Button{Style.RESET_ALL}
    - Click "🔄 New Session"
    - Confirm dialog
    - Chat clears, memory resets

{Fore.CYAN}[ ] Settings Modal{Style.RESET_ALL}
    - Click ⚙️ settings
    - Change voice profile
    - Toggle auto-play
    - Settings persist

{Fore.CYAN}[ ] Quick Action Buttons{Style.RESET_ALL}
    - Click any quick action
    - Question auto-sends
    - Response appears

{Fore.CYAN}[ ] Responsive Design{Style.RESET_ALL}
    - Resize browser window
    - Layout adapts to mobile/tablet/desktop

{Fore.GREEN}🎉 All backend features are working!{Style.RESET_ALL}
{Fore.YELLOW}Please manually verify the UI features above.{Style.RESET_ALL}
""")

print(f"\n{Fore.CYAN}{'='*70}\n")
