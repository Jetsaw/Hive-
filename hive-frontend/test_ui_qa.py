"""
HIVE UI QA Testing Script
Automated testing of 100 QA pairs through the UI
"""

import sys
import io
# Force UTF-8 encoding for stdout/stderr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import asyncio
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, Page

# Configuration
JSONL_PATH = Path("hive-backend/data/global_docs/faie_full_qa.jsonl")
UI_URL = "http://localhost:8080"
NUM_QUESTIONS = 100
RESULTS_FILE = f"hive-frontend/test-results/ui_qa_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
TIMEOUT = 60000  # 60 seconds per question

class UIQATester:
    def __init__(self):
        self.results = []
        self.qa_pairs = []
        
    def load_questions(self, num_questions=100):
        """Load QA pairs from JSONL file"""
        print(f"📂 Loading questions from {JSONL_PATH}")
        
        with open(JSONL_PATH, 'r', encoding='utf-8') as f:
            all_pairs = [json.loads(line) for line in f]
        
        # Take first num_questions
        self.qa_pairs = all_pairs[:num_questions]
        print(f"✅ Loaded {len(self.qa_pairs)} QA pairs")
        
    async def send_message(self, page: Page, question: str) -> str:
        """Send message through UI and get response"""
        try:
            # Type question
            textarea = await page.wait_for_selector('#messageInput', timeout=5000)
            await textarea.fill(question)
            
            # Click send button
            send_btn = await page.wait_for_selector('#sendBtn')
            await send_btn.click()
            
            # Wait for typing indicator to appear
            await page.wait_for_selector('.typing-indicator', timeout=5000)
            
            # Wait for typing indicator to disappear (response received)
            await page.wait_for_selector('.typing-indicator', state='hidden', timeout=TIMEOUT)
            
            # Get the last assistant message
            await asyncio.sleep(0.5)  # Brief wait for DOM update
            assistant_messages = await page.query_selector_all('.assistant-message .message')
            
            if assistant_messages:
                last_message = assistant_messages[-1]
                response_text = await last_message.inner_text()
                # Remove timestamp
                response_text = response_text.rsplit('\n', 1)[0] if '\n' in response_text else response_text
                return response_text.strip()
            
            return "ERROR: No response received"
            
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    async def run_tests(self):
        """Run all QA tests through UI"""
        print(f"\n🧪 Starting UI QA Testing - {len(self.qa_pairs)} questions")
        print(f"🌐 Target: {UI_URL}")
        print(f"⏱️  Timeout per question: {TIMEOUT/1000}s\n")
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Navigate to app
            await page.goto(UI_URL)
            await page.wait_for_load_state('networkidle')
            
            # Wait for app to be ready
            await page.wait_for_selector('#messageInput', timeout=10000)
            print("✅ App loaded successfully\n")
            
            # Test each QA pair
            for idx, qa in enumerate(self.qa_pairs, 1):
                question = qa.get('question', '')
                expected_answer = qa.get('answer', '')
                
                print(f"[{idx}/{len(self.qa_pairs)}] Testing: {question[:60]}...")
                
                start_time = datetime.now()
                response = await self.send_message(page, question)
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                # Store result
                result = {
                    'question_num': idx,
                    'question': question,
                    'expected_answer': expected_answer,
                    'actual_answer': response,
                    'response_time_seconds': response_time,
                    'error': response.startswith('ERROR')
                }
                self.results.append(result)
                
                # Print status
                status = "❌ ERROR" if result['error'] else f"✅ OK ({response_time:.1f}s)"
                print(f"    {status}")
                
                # Brief pause between questions
                await asyncio.sleep(1)
                
                # Save intermediate results every 10 questions
                if idx % 10 == 0:
                    self.save_results()
                    print(f"\n📊 Checkpoint: {idx} questions completed\n")
            
            await browser.close()
    
    def save_results(self):
        """Save test results to JSON file"""
        Path(RESULTS_FILE).parent.mkdir(parents=True, exist_ok=True)
        
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'total_questions': len(self.qa_pairs),
                    'ui_url': UI_URL,
                    'timeout_seconds': TIMEOUT / 1000
                },
                'results': self.results,
                'summary': self.generate_summary()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {RESULTS_FILE}")
    
    def generate_summary(self):
        """Generate test summary statistics"""
        if not self.results:
            return {}
        
        total = len(self.results)
        errors = sum(1 for r in self.results if r['error'])
        successful = total - errors
        
        response_times = [r['response_time_seconds'] for r in self.results if not r['error']]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            'total_questions': total,
            'successful': successful,
            'errors': errors,
            'success_rate': f"{(successful/total*100):.1f}%",
            'average_response_time': f"{avg_response_time:.2f}s",
            'min_response_time': f"{min(response_times, default=0):.2f}s",
            'max_response_time': f"{max(response_times, default=0):.2f}s"
        }
    
    def print_summary(self):
        """Print test summary to console"""
        summary = self.generate_summary()
        
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Total Questions:      {summary['total_questions']}")
        print(f"Successful Responses: {summary['successful']}")
        print(f"Errors:               {summary['errors']}")
        print(f"Success Rate:         {summary['success_rate']}")
        print(f"Avg Response Time:    {summary['average_response_time']}")
        print(f"Min Response Time:    {summary['min_response_time']}")
        print(f"Max Response Time:    {summary['max_response_time']}")
        print("="*60 + "\n")

async def main():
    """Main execution function"""
    tester = UIQATester()
    
    try:
        # Load questions
        tester.load_questions(NUM_QUESTIONS)
        
        # Run tests
        await tester.run_tests()
        
        # Save final results
        tester.save_results()
        
        # Print summary
        tester.print_summary()
        
        print("✅ Testing complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
