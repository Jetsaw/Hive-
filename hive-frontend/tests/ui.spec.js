// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('HIVE User Interface', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('should display welcome section with no emojis', async ({ page }) => {
        const welcomeTitle = page.locator('.welcome-title');
        await expect(welcomeTitle).toBeVisible();
        await expect(welcomeTitle).toContainText('Welcome to HIVE');
        // Verify no emoji in title
        const titleText = await welcomeTitle.textContent();
        expect(titleText).not.toMatch(/[\u{1F300}-\u{1F9FF}]/u);
    });

    test('should have SVG icons instead of emojis', async ({ page }) => {
        // Check theme toggle has SVG
        const themeToggle = page.locator('#themeToggle svg');
        await expect(themeToggle).toBeVisible();

        // Check settings button has SVG
        const settingsBtn = page.locator('#settingsBtn svg');
        await expect(settingsBtn).toBeVisible();

        // Check new session button has SVG
        const newSessionBtn = page.locator('#newSessionBtn svg');
        await expect(newSessionBtn).toBeVisible();
    });

    test('should have proper ARIA labels on icon buttons', async ({ page }) => {
        // Theme toggle
        const themeToggle = page.locator('#themeToggle');
        await expect(themeToggle).toHaveAttribute('aria-label', 'Toggle dark mode');

        // Settings button
        const settingsBtn = page.locator('#settingsBtn');
        await expect(settingsBtn).toHaveAttribute('aria-label', 'Open settings');

        // New session button
        const newSessionBtn = page.locator('#newSessionBtn');
        await expect(newSessionBtn).toHaveAttribute('aria-label', 'Start new session');

        // Attach button
        const attachBtn = page.locator('#attachBtn');
        await expect(attachBtn).toHaveAttribute('aria-label', 'Attach file');

        // Voice button
        const voiceBtn = page.locator('#voiceBtn');
        await expect(voiceBtn).toHaveAttribute('aria-label', 'Start voice input');

        // Send button
        const sendBtn = page.locator('#sendBtn');
        await expect(sendBtn).toHaveAttribute('aria-label', 'Send message');
    });

    test('should toggle theme correctly', async ({ page }) => {
        const themeToggle = page.locator('#themeToggle');
        const body = page.locator('body');

        // Initial state should be light
        await expect(body).toHaveAttribute('data-theme', 'light');

        // Click to toggle to dark
        await themeToggle.click();
        await expect(body).toHaveAttribute('data-theme', 'dark');
        await expect(body).toHaveClass(/dark-mode/);

        // Click to toggle back to light
        await themeToggle.click();
        await expect(body).toHaveAttribute('data-theme', 'light');
    });

    test('should have visible focus states on keyboard navigation', async ({ page }) => {
        // Tab to theme toggle
        await page.keyboard.press('Tab');
        const themeToggle = page.locator('#themeToggle');
        await expect(themeToggle).toBeFocused();

        // Verify focus ring is visible (check for outline)
        const outlineWidth = await themeToggle.evaluate((el) => {
            return window.getComputedStyle(el, ':focus-visible').outlineWidth;
        });
        expect(outlineWidth).not.toBe('0px');
    });

    test('should open and close settings modal', async ({ page }) => {
        const settingsBtn = page.locator('#settingsBtn');
        const settingsModal = page.locator('#settingsModal');
        const closeBtn = page.locator('#closeSettings');

        // Modal should be hidden initially
        await expect(settingsModal).not.toHaveClass(/active/);

        // Open modal
        await settingsBtn.click();
        await expect(settingsModal).toHaveClass(/active/);

        // Close modal
        await closeBtn.click();
        await expect(settingsModal).not.toHaveClass(/active/);
    });

    test('should have proper form label for message input', async ({ page }) => {
        const messageInput = page.locator('#messageInput');
        const label = page.locator('label[for="messageInput"]');

        // Label should exist
        await expect(label).toBeInViewport();

        // Input should have aria-label
        await expect(messageInput).toHaveAttribute('aria-label', 'Chat message input');
    });

    test('should send message and show loading state', async ({ page }) => {
        const messageInput = page.locator('#messageInput');
        const sendBtn = page.locator('#sendBtn');

        // Type a message
        await messageInput.fill('Test message');

        // Click send
        await sendBtn.click();

        // Button should be disabled and have loading class
        await expect(sendBtn).toBeDisabled();
        await expect(sendBtn).toHaveClass(/loading/);

        // Wait for response (button should re-enable)
        await expect(sendBtn).toBeEnabled({ timeout: 10000 });
        await expect(sendBtn).not.toHaveClass(/loading/);
    });

    test('should have quick action cards with SVG icons', async ({ page }) => {
        const quickActionCards = page.locator('.quick-action-card');
        await expect(quickActionCards).toHaveCount(3);

        // Each card should have SVG icon
        for (let i = 0; i < 3; i++) {
            const card = quickActionCards.nth(i);
            const svg = card.locator('svg');
            await expect(svg).toBeVisible();

            // Card should have aria-label
            await expect(card).toHaveAttribute('aria-label');
        }
    });

    test('should click quick action card and send query', async ({ page }) => {
        const firstCard = page.locator('.quick-action-card').first();
        const messageInput = page.locator('#messageInput');

        // Click first quick action card
        await firstCard.click();

        // Message should be sent (check for user message in chat)
        const userMessage = page.locator('.message.user').first();
        await expect(userMessage).toBeVisible({ timeout: 5000 });
    });

    test('should meet minimum touch target sizes on mobile', async ({ page }) => {
        // Set mobile viewport
        await page.setViewportSize({ width: 375, height: 667 });

        // Check send button size
        const sendBtn = page.locator('#sendBtn');
        const sendBtnBox = await sendBtn.boundingBox();
        expect(sendBtnBox.width).toBeGreaterThanOrEqual(44);
        expect(sendBtnBox.height).toBeGreaterThanOrEqual(44);

        // Check voice button size
        const voiceBtn = page.locator('#voiceBtn');
        const voiceBtnBox = await voiceBtn.boundingBox();
        expect(voiceBtnBox.width).toBeGreaterThanOrEqual(44);
        expect(voiceBtnBox.height).toBeGreaterThanOrEqual(44);
    });

    test('should respect prefers-reduced-motion', async ({ page }) => {
        // Enable reduced motion
        await page.emulateMedia({ reducedMotion: 'reduce' });
        await page.reload();

        const quickActionCard = page.locator('.quick-action-card').first();

        // Hover over card
        await quickActionCard.hover();

        // Check that transform is not applied (no lift effect)
        const transform = await quickActionCard.evaluate((el) => {
            return window.getComputedStyle(el).transform;
        });
        expect(transform).toBe('none');
    });

    test('should have no horizontal scroll on mobile', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 667 });

        const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
        const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);

        expect(scrollWidth).toBeLessThanOrEqual(clientWidth);
    });
});
