/**
 * HIVE Chatbot - 1000 Question JSONL Test
 * Tests chatbot through user dashboard with questions from JSONL file
 */

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

// Load questions from JSONL file
function loadQuestionsFromJSONL(filePath, maxQuestions = 1000) {
    const questions = [];
    const fileContent = fs.readFileSync(filePath, 'utf-8');
    const lines = fileContent.split('\n').filter(line => line.trim());

    for (let i = 0; i < Math.min(lines.length, maxQuestions); i++) {
        try {
            const data = JSON.parse(lines[i]);
            if (data.question) {
                questions.push({
                    question: data.question,
                    expectedAnswer: data.answer || null,
                    category: data.category || 'general'
                });
            }
        } catch (error) {
            console.log(`Skipping line ${i + 1}: Parse error`);
        }
    }

    return questions;
}

// Path to JSONL file with QA pairs
const JSONL_PATH = path.join(__dirname, '../hive-backend/data/global_docs/faie_full_qa.jsonl');

test.describe('HIVE Chatbot - 200 Question JSONL Test', () => {
    test('should answer 200 questions from JSONL through UI', async ({ page }) => {
        // Load questions
        const TEST_QUESTIONS = loadQuestionsFromJSONL(JSONL_PATH, 200);
        console.log(`\nLoaded ${TEST_QUESTIONS.length} questions from JSONL file\n`);

        // Navigate to user dashboard
        await page.goto('http://localhost:8080');
        await page.waitForSelector('.welcome-section', { timeout: 10000 });

        const results = [];
        let successCount = 0;
        let emojiCount = 0;
        let conciseCount = 0;
        let totalSentences = 0;
        let totalWords = 0;
        let timeoutCount = 0;

        console.log('=' + '='.repeat(79));
        console.log('HIVE CHATBOT - 200 QUESTION JSONL TEST');
        console.log('=' + '='.repeat(79));
        console.log(`Started: ${new Date().toLocaleString()}`);
        console.log(`Questions loaded from: faie_full_qa.jsonl`);
        console.log(`Total questions to test: ${TEST_QUESTIONS.length}`);
        console.log('=' + '='.repeat(79));
        console.log('');

        // WARM-UP QUERY (prevents first-question timeout)
        console.log('🔥 Warming up chatbot...');
        try {
            const input = await page.locator('#messageInput');
            await input.fill('Hello');
            const sendButton = await page.locator('#sendBtn');
            await sendButton.click();
            await page.waitForSelector('.message.bot:last-of-type', { timeout: 60000 });
            console.log('✅ Chatbot warmed up successfully\n');
            await page.waitForTimeout(1000);
        } catch (error) {
            console.log('⚠️  Warm-up failed, continuing anyway...\n');
        }

        // Main test loop
        for (let i = 0; i < TEST_QUESTIONS.length; i++) {
            const { question, expectedAnswer, category } = TEST_QUESTIONS[i];
            const progress = `[${i + 1}/${TEST_QUESTIONS.length}]`;
            console.log(`${progress} Q: ${question.substring(0, 80)}${question.length > 80 ? '...' : ''}`);

            try {
                const input = await page.locator('#messageInput');
                await input.clear();
                await input.fill(question);

                const sendButton = await page.locator('#sendBtn');
                await sendButton.click();

                // Wait for bot response with longer timeout
                await page.waitForSelector('.message.bot:last-of-type', { timeout: 60000 });

                // Get the latest bot response
                const botMessage = await page.locator('.message.bot:last-of-type .card').last();
                const answer = await botMessage.textContent();

                // Analyze response
                const hasEmoji = /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F900}-\u{1F9FF}]/u.test(answer);
                const sentences = answer.split(/[.!?]+/).filter(s => s.trim().length > 0).length;
                const words = answer.split(/\s+/).filter(w => w.length > 0).length;
                const isConcise = sentences <= 3;

                // Display answer (truncated)
                const displayAnswer = answer.length > 100 ? answer.substring(0, 100) + '...' : answer;
                console.log(`        A: ${displayAnswer}`);
                console.log(`        📊 ${sentences} sent | ${words} words | Emoji: ${hasEmoji ? '❌' : '✅'} | Category: ${category}`);

                results.push({
                    questionNumber: i + 1,
                    question,
                    answer,
                    expectedAnswer,
                    category,
                    sentences,
                    words,
                    hasEmoji,
                    isConcise,
                    success: true
                });

                successCount++;
                if (hasEmoji) emojiCount++;
                if (isConcise) conciseCount++;
                totalSentences += sentences;
                totalWords += words;

                // Small delay between questions (500ms)
                await page.waitForTimeout(500);

            } catch (error) {
                const isTimeout = error.message.includes('timeout') || error.message.includes('Test timeout');
                if (isTimeout) timeoutCount++;

                console.log(`        ❌ ERROR: ${error.message.substring(0, 80)}`);
                results.push({
                    questionNumber: i + 1,
                    question,
                    answer: `ERROR: ${error.message}`,
                    expectedAnswer,
                    category,
                    sentences: 0,
                    words: 0,
                    hasEmoji: false,
                    isConcise: false,
                    error: true,
                    errorType: isTimeout ? 'timeout' : 'other'
                });

                // Don't stop on errors, continue testing
                continue;
            }

            console.log('');

            // Progress update every 50 questions
            if ((i + 1) % 50 === 0) {
                console.log(`📈 Progress: ${i + 1}/${TEST_QUESTIONS.length} (${((i + 1) / TEST_QUESTIONS.length * 100).toFixed(1)}%)`);
                console.log(`   Success rate so far: ${(successCount / (i + 1) * 100).toFixed(1)}%`);
                console.log('');
            }
        }

        // === COMPREHENSIVE ANALYSIS ===
        console.log('=' + '='.repeat(79));
        console.log('COMPREHENSIVE ANALYSIS');
        console.log('=' + '='.repeat(79));

        const failureCount = TEST_QUESTIONS.length - successCount;
        const avgSentences = successCount > 0 ? totalSentences / successCount : 0;
        const avgWords = successCount > 0 ? totalWords / successCount : 0;

        console.log(`\n📊 OVERALL RESULTS:`);
        console.log(`   Total Questions: ${TEST_QUESTIONS.length}`);
        console.log(`   ✅ Successful: ${successCount} (${(successCount / TEST_QUESTIONS.length * 100).toFixed(1)}%)`);
        console.log(`   ❌ Failed: ${failureCount} (${(failureCount / TEST_QUESTIONS.length * 100).toFixed(1)}%)`);
        console.log(`   ⏱️  Timeouts: ${timeoutCount}`);
        console.log(`   😊 No Emojis: ${successCount - emojiCount}/${successCount} (${successCount > 0 ? ((successCount - emojiCount) / successCount * 100).toFixed(1) : 0}%)`);
        console.log(`   📝 Concise (≤3 sent): ${conciseCount}/${successCount} (${successCount > 0 ? (conciseCount / successCount * 100).toFixed(1) : 0}%)`);
        console.log(`   📏 Avg Sentences: ${avgSentences.toFixed(1)}`);
        console.log(`   📏 Avg Words: ${avgWords.toFixed(1)}`);

        // Category breakdown
        const categories = {};
        results.forEach(r => {
            if (!categories[r.category]) {
                categories[r.category] = { total: 0, success: 0 };
            }
            categories[r.category].total++;
            if (r.success) categories[r.category].success++;
        });

        console.log(`\n📂 CATEGORY BREAKDOWN:`);
        Object.keys(categories).forEach(cat => {
            const stats = categories[cat];
            console.log(`   ${cat}: ${stats.success}/${stats.total} (${(stats.success / stats.total * 100).toFixed(1)}%)`);
        });

        // Save results to JSON file
        const outputPath = 'chatbot_200q_jsonl_results.json';
        fs.writeFileSync(
            outputPath,
            JSON.stringify({
                testInfo: {
                    totalQuestions: TEST_QUESTIONS.length,
                    successful: successCount,
                    failed: failureCount,
                    timeouts: timeoutCount,
                    avgSentences,
                    avgWords,
                    noEmojis: successCount - emojiCount,
                    conciseResponses: conciseCount,
                    timestamp: new Date().toISOString()
                },
                categoryStats: categories,
                results: results
            }, null, 2)
        );

        console.log(`\n✅ Test Complete!`);
        console.log(`📄 Results saved to: ${outputPath}`);
        console.log(`🕐 Completed: ${new Date().toLocaleString()}`);
        console.log('=' + '='.repeat(79));

        // Assertions (relaxed for large dataset)
        expect(successCount).toBeGreaterThan(TEST_QUESTIONS.length * 0.90); // At least 90% success
        expect(emojiCount).toBe(0); // No emojis
        if (successCount > 0) {
            expect(conciseCount / successCount).toBeGreaterThan(0.90); // 90% concise
        }
    });
});
