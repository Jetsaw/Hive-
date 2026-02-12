"""
HIVE Chatbot Q&A Testing Script
Tests chatbot with 50 diverse questions and analyzes responses
"""

import requests
import json
import re
from datetime import datetime

API_BASE = "http://localhost:8000"
USER_ID = "test_user_qa_50"

# 50 Diverse Test Questions
TEST_QUESTIONS = [
    # Structure Questions (should ask for programme clarification)
    "What subjects are in Year 1?",
    "What courses do I take in Trimester 1?",
    "Show me Year 2 Trimester 3 courses",
    "What's the course structure for Year 3?",
    "List all subjects in first semester",
    
    # Programme-specific structure
    "What subjects are in Year 1 for Applied AI?",
    "Show me Intelligent Robotics Year 2 courses",
    "What's in Applied AI Trimester 2620?",
    "Intelligent Robotics Year 1 subjects",
    "Applied AI course list for Year 3",
    
    # Specific course codes
    "What is ACE6313?",
    "Tell me about AMT6113",
    "What is ACE6143?",
    "Explain ACE6123",
    "What's ACE6153?",
    
    # Prerequisites questions
    "What are the prerequisites for ACE6313?",
    "Prerequisites for Machine Learning?",
    "What do I need before taking ACE6323?",
    "Requirements for Deep Learning?",
    "Prerequisites for NLP course?",
    
    # Course aliases
    "Tell me about machine learning",
    "What is deep learning?",
    "Explain computer vision",
    "What's NLP?",
    "Tell me about robotics fundamentals",
    
    # Credits and details
    "How many credits is ACE6313?",
    "What's the credit value of Math 1?",
    "Credits for programming fundamentals",
    
    # Planning questions
    "Can I take ACE6313 if I failed AMT6113?",
    "What can I take if I passed Math 1?",
    "Plan my Year 1 Semester 2",
    
    # General questions
    "What programming courses are there?",
    "List all math courses",
    "What AI courses are available?",
    "Show me robotics courses",
    "What language courses do I need?",
    
    # Edge cases
    "What is the weather?",
    "Who is the dean?",
    "When is registration?",
    "How do I apply?",
    "What's the tuition fee?",
    
    # Mixed questions
    "What are prerequisites for ACE6313 and is it in Year 2?",
    "Tell me about Applied AI programme structure",
    "What's different between Applied AI and Robotics?",
    "Can I switch from Robotics to Applied AI?",
    
    # Greeting
    "Hi",
    "Hello",
    "Hey there"
]

def has_emoji(text):
    """Check if text contains emojis"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002600-\U000026FF"  # misc symbols
        "\U00002700-\U000027BF"  # dingbats
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "]+", 
        flags=re.UNICODE
    )
    return bool(emoji_pattern.search(text))

def count_sentences(text):
    """Count sentences in text"""
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])

def send_question(question):
    """Send question to chatbot API"""
    try:
        response = requests.post(
            f"{API_BASE}/api/chat",
            json={"user_id": USER_ID, "message": question},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("answer", "")
        else:
            return f"ERROR: {response.status_code}"
    except Exception as e:
        return f"ERROR: {str(e)}"

def analyze_response(question, answer):
    """Analyze response quality"""
    analysis = {
        "question": question,
        "answer": answer,
        "length": len(answer),
        "sentences": count_sentences(answer),
        "has_emoji": has_emoji(answer),
        "is_error": answer.startswith("ERROR"),
        "is_concise": count_sentences(answer) <= 3,
        "word_count": len(answer.split())
    }
    return analysis

def main():
    print("=" * 80)
    print("HIVE CHATBOT Q&A TESTING - 50 QUESTIONS")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Questions: {len(TEST_QUESTIONS)}")
    print("=" * 80)
    print()
    
    results = []
    
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"[{i}/50] Q: {question}")
        answer = send_question(question)
        analysis = analyze_response(question, answer)
        results.append(analysis)
        
        # Print answer (truncated if too long)
        answer_display = answer if len(answer) <= 150 else answer[:150] + "..."
        print(f"       A: {answer_display}")
        print(f"       Sentences: {analysis['sentences']} | Emoji: {analysis['has_emoji']} | Words: {analysis['word_count']}")
        print()
    
    # Summary Statistics
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    total = len(results)
    errors = sum(1 for r in results if r['is_error'])
    with_emoji = sum(1 for r in results if r['has_emoji'])
    concise = sum(1 for r in results if r['is_concise'])
    avg_sentences = sum(r['sentences'] for r in results) / total
    avg_words = sum(r['word_count'] for r in results) / total
    
    print(f"Total Questions: {total}")
    print(f"Errors: {errors} ({errors/total*100:.1f}%)")
    print(f"Responses with Emojis: {with_emoji} ({with_emoji/total*100:.1f}%)")
    print(f"Concise (≤3 sentences): {concise} ({concise/total*100:.1f}%)")
    print(f"Average Sentences: {avg_sentences:.1f}")
    print(f"Average Words: {avg_words:.1f}")
    print()
    
    # Quality Metrics
    print("=" * 80)
    print("QUALITY METRICS")
    print("=" * 80)
    print(f"✅ No Emojis: {total - with_emoji}/{total} ({(total-with_emoji)/total*100:.1f}%)")
    print(f"✅ Concise Responses: {concise}/{total} ({concise/total*100:.1f}%)")
    print(f"⚠️  Long Responses (>3 sentences): {total - concise}/{total}")
    print(f"❌ Errors: {errors}/{total}")
    print()
    
    # Save detailed results
    with open('chatbot_qa_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("=" * 80)
    print(f"Detailed results saved to: chatbot_qa_test_results.json")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()
