import { test, expect } from '@playwright/test';

test.describe('HIVE UI & Chatbot Verification', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:8080');
        // Wait for connection
        await page.waitForTimeout(1000);
    });

    test('UI Components: Title, Dark Mode, Voice Button', async ({ page }) => {
        // 1. Check Title
        await expect(page).toHaveTitle(/HIVE/);
        const headerTitle = page.locator('.brand-title');
        await expect(headerTitle).toHaveText('HIVE MMU Academic Adviser');

        // 2. Check Voice Button
        const voiceBtn = page.locator('#voiceBtn');
        await expect(voiceBtn).toBeVisible();
        await expect(voiceBtn).toHaveClass(/voice-button-large/);
        // Verify it's circular/large (CSS check indirectly via class)

        // 3. Check Dark Mode Toggle
        const themeToggle = page.locator('#themeToggle');
        await expect(themeToggle).toBeVisible();

        // Initial state (assuming light mode default)
        await expect(page.locator('body')).not.toHaveClass(/dark-mode/);

        // Click toggle
        await themeToggle.click();

        // Verify dark mode class added
        await expect(page.locator('body')).toHaveClass(/dark-mode/);

        // Click again to revert
        await themeToggle.click();
        await expect(page.locator('body')).not.toHaveClass(/dark-mode/);
    });

    test('Chatbot Logic: Structure Question (Clarification)', async ({ page }) => {
        // Input question
        await page.fill('#messageInput', 'What subjects are in Year 1?');
        await page.click('#sendBtn');

        // Wait for response
        const responses = page.locator('.message:not(.user) .card-content');
        await expect(responses.last()).toBeVisible({ timeout: 10000 });

        // Get text
        const responseText = await responses.last().innerText();
        console.log('Bot Response (Structure):', responseText);

        // Expect clarification prompt
        expect(responseText).toContain('Which programme?');
        expect(responseText).toContain('Applied AI');
        expect(responseText).toContain('Intelligent Robotics');
    });

    test('Chatbot Logic: Specific Course (Conciseness & No Emojis)', async ({ page }) => {
        await page.fill('#messageInput', 'What is ACE6313?');
        await page.click('#sendBtn');

        const responses = page.locator('.message:not(.user) .card-content');
        await expect(responses.last()).toBeVisible({ timeout: 10000 });

        const responseText = await responses.last().innerText();
        console.log('Bot Response (Course):', responseText);

        // Expect conciseness (arbitrary length check, e.g., < 300 chars)
        expect(responseText.length).toBeLessThan(400);

        // Expect NO emojis (regex check)
        // Ranges: Emoticons, Symbols, Pictographs, etc.
        const emojiRegex = /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}]/u;
        expect(emojiRegex.test(responseText)).toBeFalsy();
    });

    test('Chatbot Logic: Prerequisites (Accuracy)', async ({ page }) => {
        await page.fill('#messageInput', 'Prerequisites for machine learning?');
        await page.click('#sendBtn');

        const responses = page.locator('.message:not(.user) .card-content');
        await expect(responses.last()).toBeVisible({ timeout: 10000 });

        const responseText = await responses.last().innerText();
        console.log('Bot Response (Prereqs):', responseText);

        // Expect specific code mentions
        expect(responseText).toContain('ACE6313');
        // Likely mentions prerequisites like AMT6113 or ACE6113 based on data
        // We'll check for "require" or "prerequisite"
        expect(responseText.toLowerCase()).toMatch(/require|prerequisite/);
    });
});
