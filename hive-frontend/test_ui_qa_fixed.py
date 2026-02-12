# -*- coding: utf-8 -*-
"""
HIVE UI Testing - 100 QA Pairs through Browser
Fixed version with proper browser configuration
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import asyncio
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# Configuration
JSONL_PATH = Path("hive-backend/data/global_docs/faie_full_qa.jsonl")
UI_URL = "http://localhost:8080"
NUM_QUESTIONS = 730  # Test ALL QA pairs
RESULTS_FILE = f"hive-frontend/test-results/ui_qa_full_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
SCREENSHOT_DIR = Path(f"hive-frontend/test-results/screenshots_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
TIMEOUT = 60000  # 60 seconds per question

class UIQATester:
    def __init__(self):
        self.results = []
        self.qa_pairs = []
        self.page = None
        self.browser = None
        
    def load_questions(self, num_questions=100):
        """Load QA pairs from JSONL file"""
        print(f"Loading questions from {JSONL_PATH}")
        
        with open(JSONL_PATH, 'r', encoding='utf-8') as f:
            all_pairs = [json.loads(line) for line in f]
        
        self.qa_pairs = all_pairs[:num_questions]
        print(f"Loaded {len(self.qa_pairs)} QA pairs\n")
        
    async def start_browser(self):
        """Launch browser with simplified configuration"""
        print("Launching browser...")
        
        playwright = await async_playwright().start()
        
        # Use simpler launch args to avoid issues
        self.browser = await playwright.chromium.launch(
            headless=False,  # Show browser for visibility
            args=['--disable-dev-shm-usage']
        )
        
        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        
        self.page = await context.new_page()
        print("Browser launched successfully\n")
        
    async def navigate_to_app(self):
        """Navigate to HIVE and wait for it to load"""
        print(f"Navigating to {UI_URL}...")
        
        await self.page.goto(UI_URL, wait_until='networkidle')
        
        # Wait for the message input to be ready
        await self.page.wait_for_selector('#messageInput', timeout=10000)
        
        # Hide welcome screen if visible
        await self.page.evaluate('''
            const welcome = document.getElementById('welcomeScreen');
            if (welcome) welcome.style.display = 'none';
        ''')
        
        print("App loaded and ready\n")
        
    async def send_question(self, question, question_num):
        """Send question through UI and get response"""
        try:
            # Type the question
            input_field = await self.page.wait_for_selector('#messageInput')
            await input_field.fill(question)
            
            # Brief wait for rendering
            await asyncio.sleep(0.3)
            
            # Click send button
            send_btn = await self.page.wait_for_selector('#sendBtn')
            await send_btn.click()
            
            # Wait for typing indicator to appear (means message was sent)
            try:
                await self.page.wait_for_selector('.typing-indicator', timeout=3000)
            except PlaywrightTimeout:
                pass  # May not always appear
            
            # Wait for typing indicator to disappear (response received)
            await self.page.wait_for_selector('.typing-indicator', state='hidden', timeout=TIMEOUT)
            
            # Small delay for DOM to update
            await asyncio.sleep(0.5)
            
            # Get the last assistant message
            assistant_messages = await self.page.query_selector_all('.assistant-message .message')
            
            if not assistant_messages:
                return None, "No response message found"
            
            last_message = assistant_messages[-1]
            response_text = await last_message.inner_text()
            
            # Remove timestamp if present
            lines = response_text.split('\n')
            if lines and ':' in lines[-1] and len(lines[-1]) < 20:
                response_text = '\n'.join(lines[:-1])
            
            # Take screenshot every 50 questions for full test
            if question_num % 50 == 0:
                SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
                screenshot_path = SCREENSHOT_DIR / f"question_{question_num}.png"
                await self.page.screenshot(path=str(screenshot_path))
                print(f"  Screenshot saved: {screenshot_path.name}")
            
            return response_text.strip(), None
            
        except PlaywrightTimeout:
            return None, "Response timeout"
        except Exception as e:
            return None, f"Error: {str(e)}"
    
    async def run_tests(self):
        """Run all QA tests through UI"""
        print(f"Starting UI QA Testing - {len(self.qa_pairs)} questions")
        print(f"Target: {UI_URL}")
        print(f"Timeout per question: {TIMEOUT/1000}s\n")
        print("="*80)
        
        await self.start_browser()
        await self.navigate_to_app()
        
        for idx, qa in enumerate(self.qa_pairs, 1):
            question = qa.get('question', '')
            expected_answer = qa.get('answer', '')
            
            print(f"\n[{idx}/{len(self.qa_pairs)}] {question[:70]}...")
            
            start_time = datetime.now()
            response, error = await self.send_question(question, idx)
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            # Store result
            result = {
                'question_num': idx,
                'question': question,
                'expected_answer': expected_answer,
                'actual_answer': response if response else f"ERROR: {error}",
                'response_time_seconds': round(response_time, 2),
                'success': response is not None,
                'error': error
            }
            self.results.append(result)
            
            # Print status
            if result['success']:
                print(f"  SUCCESS ({response_time:.2f}s)")
                print(f"  Response: {response[:80]}...")
            else:
                print(f"  FAILED: {error}")
            
            # Save checkpoints every 25 questions
            if idx % 25 == 0:
                self.save_results()
                print(f"\n{'-'*80}")
                print(f"Checkpoint: {idx}/{len(self.qa_pairs)} completed")
                summary = self.generate_summary()
                print(f"Success Rate: {summary['success_rate']}")
                print(f"Avg Response Time: {summary['average_response_time']}")
                print(f"{'-'*80}")
            
            # Small delay between questions
            await asyncio.sleep(0.5)
        
        await self.browser.close()
    
    def save_results(self):
        """Save test results to JSON file"""
        Path(RESULTS_FILE).parent.mkdir(parents=True, exist_ok=True)
        
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'total_questions': len(self.qa_pairs),
                    'ui_url': UI_URL,
                    'timeout_seconds': TIMEOUT / 1000,
                    'test_type': 'UI Browser Automation'
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
        print("UI TEST SUMMARY")
        print("="*80)
        print(f"Total Questions:      {summary['total_questions']}")
        print(f"Successful Responses: {summary['successful']}")
        print(f"Failed Responses:     {summary['failed']}")
        print(f"Success Rate:         {summary['success_rate']}")
        print(f"Avg Response Time:    {summary['average_response_time']}")
        print(f"Min Response Time:    {summary['min_response_time']}")
        print(f"Max Response Time:    {summary['max_response_time']}")
        print("="*80 + "\n")

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
        
        print("UI Testing complete!")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        if tester.browser:
            await tester.browser.close()
        tester.save_results()
        tester.print_summary()
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        if tester.browser:
            await tester.browser.close()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
