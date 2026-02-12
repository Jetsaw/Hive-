"""
HIVE Chatbot - 50 Question Comprehensive Test
Tests chatbot responses for quality, accuracy, and adherence to tuning guidelines
"""

import requests
import json
import re
from datetime import datetime
import time

API_BASE = "http://localhost:8000"
USER_ID = "test_50q_comprehensive"

# 50 Comprehensive Test Questions
TEST_QUESTIONS = [
    # Course Information (10 questions)
    "What subjects are in Year 1 Trimester 1?",
    "Tell me about ACE6313",
    "What are the prerequisites for Machine Learning?",
    "What is AMT6113?",
    "Tell me about Robotics Fundamentals",
    "What courses require programming skills?",
    "What is the credit value for ACE6173?",
    "Tell me about Computer Vision",
    "What is ARA6113?",
    "What courses are offered in Year 2?",
    
    # Programme Information (10 questions)
    "Tell me about the Intelligent Robotics programme",
    "What is Applied AI about?",
    "What's the difference between Robotics and AI programmes?",
    "How long is the Intelligent Robotics programme?",
    "What specializations are available?",
    "Can I take AI courses as a Robotics student?",
    "What careers can I pursue with Intelligent Robotics?",
    "Tell me about the Applied AI curriculum",
    "What is the focus of Intelligent Robotics?",
    "Are there any internship opportunities?",
    
    # Prerequisites & Planning (10 questions)
    "If I fail Math 1, can I take Math 2?",
    "What are the prerequisites for Data Structures?",
    "Can I take OOP without Programming Fundamentals?",
    "What courses can I take if I passed Math 1?",
    "Do I need Math 2 before taking Statistics?",
    "What are the core courses for Year 1?",
    "Can I skip any prerequisites?",
    "What happens if I fail a prerequisite course?",
    "How do I plan my Year 2 courses?",
    "What electives are available?",
    
    # Specific Course Queries (10 questions)
    "What is Machine Learning Fundamentals?",
    "Tell me about Neural Networks",
    "What is Deep Learning?",
    "What programming languages will I learn?",
    "Is Python taught in Year 1?",
    "What is Object Oriented Programming?",
    "Tell me about Algorithms and Data Structures",
    "What is Software Engineering about?",
    "What math courses are required?",
    "Tell me about Database Systems",
    
    # General Academic (10 questions)
    "How many credits do I need to graduate?",
    "What is the minimum GPA required?",
    "Can I change my programme?",
    "How do I register for courses?",
    "When is the final year project?",
    "What is industrial training?",
    "Can I do my internship overseas?",
    "How long is the programme?",
    "What are MPU courses?",
    "Are there any exchange programmes?",
]

def send_question(question, delay=0.5):
    """Send question with delay"""
    time.sleep(delay)
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

def has_emoji(text):
    """Check if text contains emojis"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002600-\U000026FF"
        "\U00002700-\U000027BF"
        "\U0001F900-\U0001F9FF"
        "]+", 
        flags=re.UNICODE
    )
    return bool(emoji_pattern.search(text))

def count_sentences(text):
    """Count sentences"""
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])

def analyze_response(question, answer):
    """Analyze response quality"""
    return {
        "question": question,
        "answer": answer,
        "length": len(answer),
        "sentences": count_sentences(answer),
        "has_emoji": has_emoji(answer),
        "is_error": answer.startswith("ERROR"),
        "is_concise": count_sentences(answer) <= 3,
        "word_count": len(answer.split())
    }

def main():
    print("=" * 80)
    print("HIVE CHATBOT - 50 QUESTION COMPREHENSIVE TEST")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API: {API_BASE}")
    print(f"Total Questions: {len(TEST_QUESTIONS)}")
    print("=" * 80)
    print()
    
    results = []
    
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"[{i}/50] Q: {question}")
        answer = send_question(question, delay=0.3)
        analysis = analyze_response(question, answer)
        results.append(analysis)
        
        # Display answer (truncated)
        answer_display = answer if len(answer) <= 150 else answer[:150] + "..."
        print(f"        A: {answer_display}")
        print(f"        Stats: {analysis['sentences']} sent | {analysis['word_count']} words | Emoji: {analysis['has_emoji']}")
        print()
    
    # === ANALYSIS ===
    print("=" * 80)
    print("COMPREHENSIVE ANALYSIS")
    print("=" * 80)
    
    total = len(results)
    errors = sum(1 for r in results if r['is_error'])
    with_emoji = sum(1 for r in results if r['has_emoji'])
    concise = sum(1 for r in results if r['is_concise'])
    
    avg_sentences = sum(r['sentences'] for r in results) / total
    avg_words = sum(r['word_count'] for r in results) / total
    
    print(f"\n📊 RESULTS:")
    print(f"   Total: {total}")
    print(f"   Successful: {total - errors} ({(total-errors)/total*100:.1f}%)")
    print(f"   Errors: {errors} ({errors/total*100:.1f}%)")
    print(f"   No Emojis: {total - with_emoji}/{total} ({(total-with_emoji)/total*100:.1f}%)")
    print(f"   Concise (≤3 sent): {concise}/{total} ({concise/total*100:.1f}%)")
    print(f"   Avg Sentences: {avg_sentences:.1f}")
    print(f"   Avg Words: {avg_words:.1f}")
    
    # Category breakdown
    categories = [
        ("Course Information", 0, 10),
        ("Programme Information", 10, 20),
        ("Prerequisites & Planning", 20, 30),
        ("Specific Courses", 30, 40),
        ("General Academic", 40, 50)
    ]
    
    print(f"\n📂 CATEGORY BREAKDOWN:")
    for name, start, end in categories:
        cat_results = results[start:end]
        cat_errors = sum(1 for r in cat_results if r['is_error'])
        cat_concise = sum(1 for r in cat_results if r['is_concise'])
        print(f"   {name}: {len(cat_results)-cat_errors}/{len(cat_results)} success, {cat_concise}/{len(cat_results)} concise")
    
    # Save results
    output_file = 'chatbot_50q_test_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Test Complete!")
    print(f"📄 Results saved to: {output_file}")
    print(f"🕐 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()
