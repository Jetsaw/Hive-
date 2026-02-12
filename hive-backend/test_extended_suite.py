"""
Extended Test Suite for HIVE Chatbot
Tests all 29 courses in the knowledge base
"""

import json
import asyncio
import httpx
from typing import List, Dict

# Test configuration
API_URL = "http://localhost:8000/api/chat"
USER_ID = "test_user_extended"

# Load all courses from knowledge base
def load_all_courses() -> List[str]:
    """Load unique course codes from knowledge base"""
    courses = set()
    with open('../docs/new doc/hive_course_qa_pairs.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                courses.add(data['course_code'])
    return sorted(list(courses))

async def test_course_question(client: httpx.AsyncClient, user_id: str, course_code: str, question_type: str = "about") -> Dict:
    """Test a single course question"""
    
    if question_type == "about":
        question = f"What is {course_code} about?"
    elif question_type == "prerequisite":
        question = f"What is the prerequisite for {course_code}?"
    else:
        question = f"How many credit hours is {course_code}?"
    
    try:
        response = await client.post(
            API_URL,
            json={"user_id": user_id, "question": question},
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("response", "")
            
            # Check if it's a greeting or actual answer
            is_greeting = "Great to meet you" in answer or "What would you like to know" in answer
            has_course_info = course_code in answer or any(keyword in answer.lower() for keyword in ["prerequisite", "credit", "covers", "introduction"])
            
            return {
                "course_code": course_code,
                "question": question,
                "answer": answer[:200] + "..." if len(answer) > 200 else answer,
                "is_greeting": is_greeting,
                "has_course_info": has_course_info,
                "status": "greeting" if is_greeting else ("pass" if has_course_info else "unclear"),
                "full_response": answer
            }
        else:
            return {
                "course_code": course_code,
                "question": question,
                "answer": f"ERROR: HTTP {response.status_code}",
                "is_greeting": False,
                "has_course_info": False,
                "status": "error",
                "full_response": ""
            }
    except Exception as e:
        return {
            "course_code": course_code,
            "question": question,
            "answer": f"ERROR: {str(e)}",
            "is_greeting": False,
            "has_course_info": False,
            "status": "error",
            "full_response": ""
        }

async def run_extended_tests():
    """Run tests for all 29 courses"""
    
    print("=" * 80)
    print("HIVE CHATBOT - EXTENDED TEST SUITE")
    print("Testing all 29 courses in knowledge base")
    print("=" * 80)
    print()
    
    # Load courses
    courses = load_all_courses()
    print(f"✓ Loaded {len(courses)} unique courses from knowledge base")
    print()
    
    # Create async HTTP client
    async with httpx.AsyncClient() as client:
        # Test "about" questions for all courses
        print("Running 'about' question tests...")
        print("-" * 80)
        
        about_results = []
        for i, course in enumerate(courses, 1):
            print(f"Testing {i}/{len(courses)}: {course}...", end=" ")
            result = await test_course_question(client, USER_ID, course, "about")
            about_results.append(result)
            
            status_symbol = "✓" if result["status"] == "pass" else ("⚠" if result["status"] == "unclear" else "✗")
            print(f"{status_symbol} {result['status'].upper()}")
            
            # Small delay to avoid overwhelming the server
            await asyncio.sleep(0.5)
        
        print()
        
        # Calculate statistics
        total_tests = len(about_results)
        passed = sum(1 for r in about_results if r["status"] == "pass")
        greeting = sum(1 for r in about_results if r["status"] == "greeting")
        unclear = sum(1 for r in about_results if r["status"] == "unclear")
        errors = sum(1 for r in about_results if r["status"] == "error")
        
        # Print summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests:     {total_tests}")
        print(f"✓ Passed:        {passed} ({passed/total_tests*100:.1f}%)")
        print(f"⚠ Unclear:       {unclear} ({unclear/total_tests*100:.1f}%)")
        print(f"✗ Greetings:     {greeting} ({greeting/total_tests*100:.1f}%)")
        print(f"✗ Errors:        {errors} ({errors/total_tests*100:.1f}%)")
        print()
        
        # Show failures (greetings and errors)
        if greeting > 0 or errors > 0:
            print("FAILURES:")
            print("-" * 80)
            for r in about_results:
                if r["status"] in ["greeting", "error"]:
                    print(f"❌ {r['course_code']}: {r['status'].upper()}")
                    print(f"   Q: {r['question']}")
                    print(f"   A: {r['answer']}")
                    print()
        
        # Save detailed results
        with open('test_results_extended.json', 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total": total_tests,
                    "passed": passed,
                    "unclear": unclear,
                    "greeting": greeting,
                    "errors": errors,
                    "pass_rate": f"{passed/total_tests*100:.1f}%"
                },
                "results": about_results
            }, f, indent=2, ensure_ascii=False)
        
        print("✓ Detailed results saved to test_results_extended.json")
        print()
        
        return about_results, {
            "total": total_tests,
            "passed": passed,
            "unclear": unclear,
            "greeting": greeting,
            "errors": errors
        }

if __name__ == "__main__":
    asyncio.run(run_extended_tests())
