# -*- coding: utf-8 -*-
"""
HIVE API QA Testing Script
Direct API testing of 100 QA pairs (simpler than UI automation)
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import requests
import time
from pathlib import Path
from datetime import datetime
import uuid

# Configuration
JSONL_PATH = Path("hive-backend/data/global_docs/faie_full_qa.jsonl")
API_URL = "http://localhost:8080/api/chat"
NUM_QUESTIONS = 100
RESULTS_FILE = f"hive-frontend/test-results/api_qa_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
TIMEOUT = 60  # seconds

class APIQATester:
    def __init__(self):
        self.results = []
        self.qa_pairs = []
        self.user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        
    def load_questions(self, num_questions=100):
        """Load QA pairs from JSONL file"""
        print(f"Loading questions from {JSONL_PATH}")
        
        with open(JSONL_PATH, 'r', encoding='utf-8') as f:
            all_pairs = [json.loads(line) for line in f]
        
        self.qa_pairs = all_pairs[:num_questions]
        print(f"Loaded {len(self.qa_pairs)} QA pairs\n")
        
    def send_question(self, question: str) -> tuple:
        """Send question to API and get response"""
        try:
            start_time = time.time()
            
            response = requests.post(
                API_URL,
                json={"user_id": self.user_id, "message": question},
                timeout=TIMEOUT
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', 'ERROR: No answer in response')
                return answer, response_time, None
            else:
                return None, response_time, f"HTTP {response.status_code}: {response.text}"
                
        except requests.exceptions.Timeout:
            return None, TIMEOUT, "Request timeout"
        except Exception as e:
            return None, 0, str(e)
    
    def run_tests(self):
        """Run all QA tests"""
        print(f"Starting API QA Testing - {len(self.qa_pairs)} questions")
        print(f"Target: {API_URL}")
        print(f"User ID: {self.user_id}")
        print(f"Timeout: {TIMEOUT}s\n")
        print("="*80)
        
        for idx, qa in enumerate(self.qa_pairs, 1):
            question = qa.get('question', '')
            expected_answer = qa.get('answer', '')
            
            print(f"\n[{idx}/{len(self.qa_pairs)}] Question: {question[:70]}...")
            
            answer, response_time, error = self.send_question(question)
            
            # Store result
            result = {
                'question_num': idx,
                'question': question,
                'expected_answer': expected_answer,
                'actual_answer': answer if answer else f"ERROR: {error}",
                'response_time_seconds': round(response_time, 2),
                'success': answer is not None,
                'error': error
            }
            self.results.append(result)
            
            # Print status
            if result['success']:
                print(f"SUCCESS ({response_time:.2f}s)")
                print(f"Answer: {answer[:100]}...")
            else:
                print(f"FAILED: {error}")
            
            # Save checkpoints every 10 questions
            if idx % 10 == 0:
                self.save_results()
                print(f"\n{'-'*80}")
                print(f"Checkpoint: {idx}/{len(self.qa_pairs)} completed")
                summary = self.generate_summary()
                print(f"Success Rate: {summary['success_rate']}")
                print(f"Avg Response Time: {summary['average_response_time']}")
                print(f"{'-'*80}")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.5)
    
    def save_results(self):
        """Save test results to JSON file"""
        Path(RESULTS_FILE).parent.mkdir(parents=True, exist_ok=True)
        
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'total_questions': len(self.qa_pairs),
                    'api_url': API_URL,
                    'user_id': self.user_id,
                    'timeout_seconds': TIMEOUT
                },
                'results': self.results,
                'summary': self.generate_summary()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {RESULTS_FILE}")
    
    def generate_summary(self):
        """Generate test summary statistics"""
        if not self.results:
            return {}
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r['success'])
        failed = total - successful
        
        response_times = [r['response_time_seconds'] for r in self.results if r['success']]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            'total_questions': total,
            'successful': successful,
            'failed': failed,
            'success_rate': f"{(successful/total*100):.1f}%",
            'average_response_time': f"{avg_response_time:.2f}s",
            'min_response_time': f"{min(response_times, default=0):.2f}s",
            'max_response_time': f"{max(response_times, default=0):.2f}s"
        }
    
    def print_summary(self):
        """Print detailed test summary"""
        summary = self.generate_summary()
        
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Questions:      {summary['total_questions']}")
        print(f"Successful Responses: {summary['successful']}")
        print(f"Failed Responses:     {summary['failed']}")
        print(f"Success Rate:         {summary['success_rate']}")
        print(f"Avg Response Time:    {summary['average_response_time']}")
        print(f"Min Response Time:    {summary['min_response_time']}")
        print(f"Max Response Time:    {summary['max_response_time']}")
        print("="*80 + "\n")

def main():
    """Main execution function"""
    tester = APIQATester()
    
    try:
        # Load questions
        tester.load_questions(NUM_QUESTIONS)
        
        # Run tests
        tester.run_tests()
        
        # Save final results
        tester.save_results()
        
        # Print summary
        tester.print_summary()
        
        print("Testing complete!")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        tester.save_results()
        tester.print_summary()
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
