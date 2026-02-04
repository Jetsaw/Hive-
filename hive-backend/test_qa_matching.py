"""
Test script to verify chatbot returns answers from QA pairs file
"""
import requests
import json

API_URL = "http://localhost:8000/api/chat"

# Load the QA pairs to check expected answers
qa_pairs = []
with open("data/kb/hive_course_qa_pairs.jsonl", 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            qa_pairs.append(json.loads(line))

# Find AAC6133 Q&A pairs
aac_pairs = [q for q in qa_pairs if q['course_code'] == 'AAC6133']

print("=" * 80)
print(f"Found {len(aac_pairs)} Q&A pairs for AAC6133 in the file:")
print("=" * 80)
for i, pair in enumerate(aac_pairs[:3], 1):  # Show first 3
    print(f"\n{i}. Question: {pair['question']}")
    print(f"   Expected Answer: {pair['answer']}")

# Test with the chatbot
print("\n" + "=" * 80)
print("Testing chatbot responses:")
print("=" * 80)

user_id = "qa_test_user"

# First message
msg1 = {"user_id": user_id, "message": "Hi, I'm interested in Applied AI"}
resp1 = requests.post(API_URL, json=msg1)
print(f"\n1. Acknowledgment: {resp1.json().get('answer', resp1.json().get('response', ''))}")

# Test AAC6133 query
msg2 = {"user_id": user_id, "message": "What is AAC6133 about?"}
resp2 = requests.post(API_URL, json=msg2)

print(f"\n2. AAC6133 Query:")
print(f"   Status: {resp2.status_code}")

if resp2.status_code == 200:
    data = resp2.json()
    answer = data.get('answer', data.get('response', ''))
    print(f"   Chatbot Answer: {answer}")
    
    # Check if the answer matches any expected answers
    expected = aac_pairs[0]['answer']  # First Q&A pair's answer
    print(f"\n   Expected from KB: {expected}")
    
    if expected.lower() in answer.lower() or answer.lower() in expected.lower():
        print("   ✅ Answer matches KB!")
    else:
        print("   ⚠️  Answer may be generated, not from KB")
        print(f"\n   Query Type: {data.get('metadata', {}).get('query_type')}")
        print(f"   Results Count: {data.get('metadata', {}).get('results_count')}")
else:
    print(f"   ❌ Error: {resp2.text}")
