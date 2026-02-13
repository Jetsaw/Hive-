"""
Simple test script to trigger and capture the 500 error
"""
import requests
import json

API_URL = "http://localhost:8000/api/chat"

# Test 1: First message (should work - acknowledgment)
print("=" * 60)
print("TEST 1: First message (acknowledgment)")
print("=" * 60)

user_id = "debug_user_final"
msg1 = {"user_id": user_id, "message": "Hi, I'm interested in Applied AI"}

resp1 = requests.post(API_URL, json=msg1)
print(f"Status: {resp1.status_code}")
print(f"Response: {json.dumps(resp1.json(), indent=2)}")

print("\n")

# Test 2: Second message (should fail with 500)
print("=" * 60)
print("TEST 2: Second message (course query)")
print("=" * 60)

msg2 = {"user_id": user_id, "message": "What is AAC6133 about?"}

resp2 = requests.post(API_URL, json=msg2)
print(f"Status: {resp2.status_code}")
if resp2.status_code == 200:
    print(f"Response: {json.dumps(resp2.json(), indent=2)}")
else:
    print(f"Error: {resp2.text}")

print("\n" + "=" * 60)
print("Check the backend terminal for the full error traceback")
print("=" * 60)
