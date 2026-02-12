"""
HIVE Chatbot - Realistic Student Conversation Test (150 Questions)
Simulates an undergraduate student enrolling in Intelligent Robotics
Tests conversational flow, planning, prerequisites, and academic scenarios
"""

import requests
import json
import re
from datetime import datetime
import time

API_BASE = "http://localhost:8000"
USER_ID = "student_robotics_150q"

# 150 Realistic Student Questions - Intelligent Robotics Focus
STUDENT_QUESTIONS = [
    # === Initial Exploration (10 questions) ===
    "Hi, I'm interested in the Intelligent Robotics programme",
    "Can you tell me about Intelligent Robotics?",
    "What will I learn in Intelligent Robotics?",
    "What subjects are in Year 1 for Intelligent Robotics?",
    "How many years is the programme?",
    "Is this a full-time programme?",
    "What are the career prospects?",
    "Can I specialize in drones?",
    "Is there industrial training?",
    "When do I start my final year project?",
    
    # === Year 1 Planning (15 questions) ===
    "What courses do I take in my first trimester?",
    "Tell me about Math 1",
    "What is AMT6113?",
    "Do I need to take programming in Year 1?",
    "What is ACE6113?",
    "Is English compulsory?",
    "What's the credit requirement for Year 1?",
    "Can I take extra courses in Year 1?",
    "What happens if I fail a course?",
    "What subjects are in Year 1 Trimester 2?",
    "Do I need to take physics?",
    "What is Electrical Technology?",
    "Are there any project courses in Year 1?",
    "Can I skip any Year 1 courses?",
    "What's the passing grade?",
    
    # === Prerequisites & Planning (20 questions) ===
    "If I fail Math 1, can I take Math 2 next semester?",
    "What are the prerequisites for Math 2?",
    "Can I take Math 2 without passing Math 1?",
    "What happens if I fail Programming Fundamentals?",
    "Can I proceed to Year 2 if I fail one subject?",
    "What courses require Math 1 as prerequisite?",
    "If I pass Math 1, what can I take next?",
    "Can I take OOP without passing Programming Fundamentals?",
    "What are the prerequisites for Data Structures?",
    "If I fail Math 1 and Programming, can I still continue?",
    "Can I retake failed courses in the same semester?",
    "What's the maximum number of times I can retake a course?",
    "If I fail Electrical Technology, what happens?",
    "Can I take Year 2 courses while in Year 1?",
    "What if I fail multiple courses in one semester?",
    "Do I need to pass all Year 1 courses to proceed to Year 2?",
    "Can I defer a course to next year?",
    "What courses can I take if I passed Math 1 and Programming?",
    "If I fail English, can I still graduate?",
    "What's the minimum GPA to continue?",
    
    # === Specific Course Queries (25 questions) ===
    "Tell me about Robotics Fundamentals",
    "What is ACE6173?",
    "When do I take Robotics Fundamentals?",
    "What are the prerequisites for Robotics Fundamentals?",
    "Tell me about Control Systems",
    "What is ACE6163?",
    "Is Control Systems difficult?",
    "What's Robot Vision about?",
    "When do I learn about autonomous systems?",
    "Tell me about Mechatronics",
    "What is Human-Robot Interaction?",
    "Can I learn about drones in this programme?",
    "What's Drone Systems about?",
    "When do I take Advanced Robotics?",
    "What programming languages will I learn?",
    "Do I study AI in Intelligent Robotics?",
    "What's Computer Vision about?",
    "Tell me about Machine Learning Fundamentals",
    "Can Intelligent Robotics students take AI courses?",
    "What's the difference between Robot Vision and Computer Vision?",
    "Do I learn ROS (Robot Operating System)?",
    "What about embedded systems?",
    "Tell me about Microprocessor Systems",
    "What electronics courses do I need to take?",
    "Is there a course on sensors and actuators?",
    
    # === Year 2 Planning (20 questions) ===
    "What subjects are in Year 2?",
    "What courses do I take in Year 2 Trimester 1?",
    "Show me Year 2 Trimester 2 courses",
    "What's in Year 2 Trimester 3?",
    "When do I start taking robotics-specific courses?",
    "Can I take electives in Year 2?",
    "What's the difference between Year 1 and Year 2 courses?",
    "Are Year 2 courses harder?",
    "Do I need to pass all Year 1 courses before Year 2?",
    "Can I mix Year 1 and Year 2 courses?",
    "What if I'm behind on Year 1 courses in Year 2?",
    "How many courses per trimester in Year 2?",
    "Is there a capstone project in Year 2?",
    "What's Project 1 about?",
    "When do I do industrial training?",
    "How long is industrial training?",
    "Can I do internship overseas?",
    "Do I get credits for industrial training?",
    "Can I skip industrial training?",
    "What companies hire Intelligent Robotics students?",
    
    # === Advanced Topics (15 questions) ===
    "What advanced courses are in Year 3?",
    "Tell me about Year 3 subjects",
    "What's Advanced Robotics about?",
    "Can I specialize in a specific area?",
    "What electives are available?",
    "Can I take courses from Applied AI programme?",
    "What's the final year project about?",
    "How many credits is the final year project?",
    "Can I choose my own project topic?",
    "Do I work in a team or individually?",
    "What if I want to focus on drones?",
    "Can I do research projects?",
    "Are there opportunities for publications?",
    "Can I continue to PhD after this?",
    "What master's programmes can I pursue after?",
    
    # === Comparative Questions (10 questions) ===
    "What's the difference between Intelligent Robotics and Applied AI?",
    "Should I choose Robotics or AI?",
    "Can I switch from Robotics to AI?",
    "Do Applied AI students take robotics courses?",
    "Which programme has more job opportunities?",
    "Is Robotics harder than AI?",
    "Can I take AI courses as a Robotics student?",
    "What if I'm interested in both AI and Robotics?",
    "Which programme is better for drone development?",
    "What's unique about Intelligent Robotics?",
    
    # === Math & Core Courses (15 questions) ===
    "What math courses do I need?",
    "Is Linear Algebra required?",
    "What's Statistics and Probability used for?",
    "Do I need Optimization Methods?",
    "How important is math in robotics?",
    "Can I take Math 3 without Math 2?",
    "What if I'm weak in mathematics?",
    "Are there any math support classes?",
    "What's Engineering Mathematics about?",
    "Do I need calculus?",
    "What about discrete mathematics?",
    "Is there physics in the curriculum?",
    "Do I study electronics?",
    "What's Digital Electronics about?",
    "How much programming is required?",
    
    # === Practical & Hands-on (10 questions) ===
    "Are there lab sessions?",
    "Do I get to build actual robots?",
    "What equipment is available?",
    "Are there robotics competitions?",
    "Can I join robotics clubs?",
    "Is there access to 3D printers?",
    "Do we work with real robots or simulations?",
    "What programming tools do we use?",
    "Are there maker spaces on campus?",
    "Can I work on personal robotics projects?",
    
    # === Assessment & Graduation (10 questions) ===
    "How are courses assessed?",
    "Is it exam-based or project-based?",
    "What's the grading system?",
    "What GPA do I need to maintain?",
    "Can I graduate early?",
    "What if I fail my final year project?",
    "How many credits to graduate?",
    "What's the minimum duration to complete?",
    "Can I take longer than 3 years?",
    "What happens if I exceed the maximum duration?",
    
    # === Career & Industry (10 questions) ===
    "What jobs can I get with this degree?",
    "Which companies hire robotics engineers?",
    "What's the starting salary?",
    "Can I work in automation?",
    "What about jobs in manufacturing?",
    "Can I work as an AI engineer?",
    "What industries need robotics engineers?",
    "Are there jobs in research?",
    "Can I become a robotics consultant?",
    "What certifications are valuable?",
    
    # === Edge Cases & Specific Scenarios (10 questions) ===
    "What if I want to minor in AI?",
    "Can I audit courses?",
    "Is part-time study available?",
    "Can I transfer credits from another university?",
    "What if I have work experience in programming?",
    "Can I get exemptions for courses?",
    "Is there credit for prior learning?",
    "Can international students apply?",
    "Are there scholarships available?",
    "What's the application deadline?"
]

def send_question(question, delay=0.5):
    """Send question with delay to simulate natural conversation"""
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
        "word_count": len(answer.split()),
        "mentions_intelligent_robotics": "intelligent robotics" in answer.lower() or "robotics" in answer.lower(),
        "provides_clarification": "which programme" in answer.lower() or "applied ai" in answer.lower()
    }

def main():
    print("=" * 100)
    print("HIVE CHATBOT - REALISTIC STUDENT CONVERSATION TEST (150 QUESTIONS)")
    print("Perspective: Undergraduate Student - Intelligent Robotics Programme")
    print("=" * 100)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Questions: {len(STUDENT_QUESTIONS)}")
    print(f"User ID: {USER_ID}")
    print("=" * 100)
    print()
    
    results = []
    
    for i, question in enumerate(STUDENT_QUESTIONS, 1):
        print(f"[{i}/150] Q: {question}")
        answer = send_question(question, delay=0.3)
        analysis = analyze_response(question, answer)
        results.append(analysis)
        
        # Display answer (truncated)
        answer_display = answer if len(answer) <= 200 else answer[:200] + "..."
        print(f"         A: {answer_display}")
        print(f"         Stats: {analysis['sentences']} sent | {analysis['word_count']} words | Emoji: {analysis['has_emoji']}")
        
        # Show special insights
        if "fail" in question.lower() and "can i take" in question.lower():
            print(f"         [PLANNING] Testing prerequisite logic")
        if analysis['provides_clarification']:
            print(f"         [CLARIFICATION] Bot asked for programme specification")
        
        print()
    
    # === COMPREHENSIVE ANALYSIS ===
    print("=" * 100)
    print("COMPREHENSIVE ANALYSIS")
    print("=" * 100)
    
    total = len(results)
    errors = sum(1 for r in results if r['is_error'])
    with_emoji = sum(1 for r in results if r['has_emoji'])
    concise = sum(1 for r in results if r['is_concise'])
    mentions_robotics = sum(1 for r in results if r['mentions_intelligent_robotics'])
    clarifications = sum(1 for r in results if r['provides_clarification'])
    
    avg_sentences = sum(r['sentences'] for r in results) / total
    avg_words = sum(r['word_count'] for r in results) / total
    
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"   Total Questions: {total}")
    print(f"   Successful Responses: {total - errors} ({(total-errors)/total*100:.1f}%)")
    print(f"   Errors: {errors} ({errors/total*100:.1f}%)")
    print()
    
    print(f"✅ QUALITY METRICS:")
    print(f"   No Emojis: {total - with_emoji}/{total} ({(total-with_emoji)/total*100:.1f}%)")
    print(f"   Concise (≤3 sent): {concise}/{total} ({concise/total*100:.1f}%)")
    print(f"   Average Sentences: {avg_sentences:.1f}")
    print(f"   Average Words: {avg_words:.1f}")
    print()
    
    print(f"🤖 CONVERSATIONAL QUALITY:")
    print(f"   Mentions Robotics Context: {mentions_robotics}/{total} ({mentions_robotics/total*100:.1f}%)")
    print(f"   Clarification Requests: {clarifications} questions")
    print()
    
    # Category-specific analysis
    categories = {
        "Initial Exploration": (0, 10),
        "Year 1 Planning": (10, 25),
        "Prerequisites & Planning": (25, 45),
        "Specific Course Queries": (45, 70),
        "Year 2 Planning": (70, 90),
        "Advanced Topics": (90, 105),
        "Comparative Questions": (105, 115),
        "Math & Core Courses": (115, 130),
        "Practical & Hands-on": (130, 140),
        "Assessment & Graduation": (140, 150)
    }
    
    print(f"📂 CATEGORY BREAKDOWN:")
    for category, (start, end) in categories.items():
        cat_results = results[start:end]
        cat_errors = sum(1 for r in cat_results if r['is_error'])
        cat_concise = sum(1 for r in cat_results if r['is_concise'])
        cat_total = len(cat_results)
        print(f"   {category}: {cat_total-cat_errors}/{cat_total} success ({cat_concise}/{cat_total} concise)")
    
    print()
    
    # Save detailed results
    output_file = 'student_conversation_150q_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("=" * 100)
    print(f"✅ Test Complete!")
    print(f"📄 Detailed results saved to: {output_file}")
    print(f"🕐 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)

if __name__ == "__main__":
    main()
