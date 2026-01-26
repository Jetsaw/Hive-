/**
 * HIVE Chatbot - 100 Question UI Test
 * Tests chatbot through actual user interface interaction
 */

const { test, expect } = require('@playwright/test');
const fs = require('fs');

// 100 Comprehensive Test Questions
const TEST_QUESTIONS = [
    // Year 1 Basics (20 questions)
    "What subjects are in Year 1 Trimester 1?",
    "Tell me about ACE6313",
    "What is AMT6113?",
    "What is Programming Fundamentals?",
    "Tell me about English for Communication",
    "What courses are in Year 1 Trimester 2?",
    "What is AMT6123?",
    "Tell me about Data Structures",
    "What is Object Oriented Programming?",
    "What math courses are in Year 1?",
    "What is the credit value for ACE6173?",
    "Tell me about Engineering Mathematics 1",
    "What is ARC6113?",
    "Tell me about Introduction to Robotics",
    "What programming languages are taught in Year 1?",
    "What is the total credits for Year 1?",
    "Are there any electives in Year 1?",
    "What is MPU?",
    "Tell me about soft skills courses",
    "What is the structure of Year 1?",

    // Programme Information (20 questions)
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
    "What companies hire Robotics graduates?",
    "Is there a final year project?",
    "What is industrial training?",
    "How many trimesters are there?",
    "What is the programme structure?",
    "Are there any competitions or hackathons?",
    "Can I do research?",
    "What labs and equipment are available?",
    "Is there international collaboration?",
    "What makes this programme unique?",

    // Prerequisites & Planning (20 questions)
    "If I fail Math 1, can I take Math 2?",
    "What are the prerequisites for Machine Learning?",
    "Can I take OOP without Programming Fundamentals?",
    "What courses can I take if I passed Math 1?",
    "Do I need Math 2 before taking Statistics?",
    "What are the core courses for Year 1?",
    "Can I skip any prerequisites?",
    "What happens if I fail a prerequisite course?",
    "How do I plan my Year 2 courses?",
    "What electives are available?",
    "Can I take courses from other faculties?",
    "What if I want to change my specialization?",
    "How many courses can I take per trimester?",
    "What is the minimum credit requirement?",
    "Can I graduate early?",
    "What if I need to repeat a course?",
    "How do prerequisites work?",
    "Can I take advanced courses in Year 1?",
    "What is academic advising?",
    "How do I check my progress?",

    // Specific Courses - AI & ML (20 questions)
    "What is Machine Learning Fundamentals?",
    "Tell me about Neural Networks",
    "What is Deep Learning?",
    "Tell me about Computer Vision",
    "What is Natural Language Processing?",
    "Tell me about Reinforcement Learning",
    "What is AI Ethics?",
    "Tell me about Pattern Recognition",
    "What is Data Mining?",
    "Tell me about Big Data Analytics",
    "What is Intelligent Systems?",
    "Tell me about Expert Systems",
    "What is Knowledge Representation?",
    "Tell me about Fuzzy Logic",
    "What is Genetic Algorithms?",
    "Tell me about AI Applications",
    "What is Cognitive Computing?",
    "Tell me about AI in Healthcare",
    "What is Autonomous Systems?",
    "Tell me about AI and IoT",

    // Specific Courses - Robotics (20 questions)
    "Tell me about Robotics Fundamentals",
    "What is Robot Vision?",
    "Tell me about Control Systems",
    "What is Mechatronics?",
    "Tell me about Sensors and Actuators",
    "What is Robot Kinematics?",
    "Tell me about Robot Dynamics",
    "What is Mobile Robotics?",
    "Tell me about Manipulation and Grasping",
    "What is Human-Robot Interaction?",
    "Tell me about Robot Operating System",
    "What is SLAM?",
    "Tell me about Path Planning",
    "What is Swarm Robotics?",
    "Tell me about Industrial Automation",
    "What is Embedded Systems for Robotics?",
    "Tell me about Robot Design",
    "What is Soft Robotics?",
    "Tell me about Collaborative Robots",
    "What is Robot Simulation?",
];

test.describe('HIVE Chatbot - 100 Question UI Test', () => {
    test('should answer all 100 questions through UI interaction', async ({ page }) => {
        await page.goto('http://localhost:8080');
        await page.waitForSelector('.welcome-section');

        const results = [];
        let successCount = 0;
        let emojiCount = 0;
        let conciseCount = 0;
        let totalSentences = 0;
        let totalWords = 0;

        console.log('\n' + '='.repeat(80));
        console.log('HIVE CHATBOT - 100 QUESTION UI TEST');
        console.log('='.repeat(80));
        console.log(`Started: ${new Date().toLocaleString()}`);
        console.log('Testing through actual UI interaction');
        console.log('='.repeat(80));
        console.log('');

        for (let i = 0; i < TEST_QUESTIONS.length; i++) {
            const question = TEST_QUESTIONS[i];
            console.log(`[${i + 1}/100] Q: ${question}`);

            try {
                const input = await page.locator('#messageInput');
                await input.fill(question);

                const sendButton = await page.locator('#sendBtn');
                await sendButton.click();

                await page.waitForSelector('.message.bot:last-of-type', { timeout: 30000 });

                const botMessage = await page.locator('.message.bot:last-of-type .card').last();
                const answer = await botMessage.textContent();

                const hasEmoji = /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F900}-\u{1F9FF}]/u.test(answer);
                const sentences = answer.split(/[.!?]+/).filter(s => s.trim().length > 0).length;
                const words = answer.split(/\s+/).filter(w => w.length > 0).length;
                const isConcise = sentences <= 3;

                const displayAnswer = answer.length > 120 ? answer.substring(0, 120) + '...' : answer;
                console.log(`        A: ${displayAnswer}`);
                console.log(`        Stats: ${sentences} sent | ${words} words | Emoji: ${hasEmoji}`);

                results.push({
                    question,
                    answer,
                    sentences,
                    words,
                    hasEmoji,
                    isConcise
                });

                successCount++;
                if (hasEmoji) emojiCount++;
                if (isConcise) conciseCount++;
                totalSentences += sentences;
                totalWords += words;

                await page.waitForTimeout(500);

            } catch (error) {
                console.log(`        ERROR: ${error.message}`);
                results.push({
                    question,
                    answer: `ERROR: ${error.message}`,
                    sentences: 0,
                    words: 0,
                    hasEmoji: false,
                    isConcise: false,
                    error: true
                });
            }

            console.log('');
        }

        console.log('='.repeat(80));
        console.log('COMPREHENSIVE ANALYSIS');
        console.log('='.repeat(80));

        const avgSentences = totalSentences / successCount;
        const avgWords = totalWords / successCount;

        console.log(`\n📊 RESULTS:`);
        console.log(`   Total Questions: ${TEST_QUESTIONS.length}`);
        console.log(`   Successful: ${successCount} (${(successCount / TEST_QUESTIONS.length * 100).toFixed(1)}%)`);
        console.log(`   Failed: ${TEST_QUESTIONS.length - successCount}`);
        console.log(`   No Emojis: ${successCount - emojiCount}/${successCount} (${((successCount - emojiCount) / successCount * 100).toFixed(1)}%)`);
        console.log(`   Concise (≤3 sent): ${conciseCount}/${successCount} (${(conciseCount / successCount * 100).toFixed(1)}%)`);
        console.log(`   Avg Sentences: ${avgSentences.toFixed(1)}`);
        console.log(`   Avg Words: ${avgWords.toFixed(1)}`);

        fs.writeFileSync(
            'chatbot_100q_ui_results.json',
            JSON.stringify(results, null, 2)
        );

        console.log(`\n✅ Test Complete!`);
        console.log(`📄 Results saved to: chatbot_100q_ui_results.json`);
        console.log(`🕐 Completed: ${new Date().toLocaleString()}`);
        console.log('='.repeat(80));

        expect(successCount).toBeGreaterThan(90);
        expect(emojiCount).toBe(0);
        expect(conciseCount / successCount).toBeGreaterThan(0.95);
    });
});
