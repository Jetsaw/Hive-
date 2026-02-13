// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('HIVE Admin Dashboard', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/admin.html');
    });

    test('should display admin header with SVG logo', async ({ page }) => {
        const logo = page.locator('.logo-icon');
        await expect(logo).toBeVisible();

        const title = page.locator('.brand span');
        await expect(title).toContainText('HIVE Admin');
    });

    test('should have back to chat button with SVG icon', async ({ page }) => {
        const backBtn = page.locator('.new-session-btn').filter({ hasText: 'Back to Chat' });
        await expect(backBtn).toBeVisible();

        // Should have SVG icon
        const svg = backBtn.locator('svg');
        await expect(svg).toBeVisible();

        // Should have aria-label
        await expect(backBtn).toHaveAttribute('aria-label', 'Back to chat');
    });

    test('should display stats grid with 4 cards', async ({ page }) => {
        const statCards = page.locator('.stat-card');
        await expect(statCards).toHaveCount(4);

        // Check labels
        await expect(page.locator('.stat-label').nth(0)).toContainText('Pending');
        await expect(page.locator('.stat-label').nth(1)).toContainText('Answered');
        await expect(page.locator('.stat-label').nth(2)).toContainText('Ignored');
        await expect(page.locator('.stat-label').nth(3)).toContainText('Total');
    });

    test('should have filter buttons', async ({ page }) => {
        const filterBtns = page.locator('.filter-btn');
        await expect(filterBtns).toHaveCount(4);

        // All button should be active by default
        const allBtn = page.locator('.filter-btn[data-status="all"]');
        await expect(allBtn).toHaveClass(/active/);
    });

    test('should have refresh button with SVG icon', async ({ page }) => {
        const refreshBtn = page.locator('.new-session-btn').filter({ hasText: 'Refresh' });
        await expect(refreshBtn).toBeVisible();

        // Should have SVG icon
        const svg = refreshBtn.locator('svg');
        await expect(svg).toBeVisible();

        // Should have aria-label
        await expect(refreshBtn).toHaveAttribute('aria-label', 'Refresh questions');
    });

    test('should display questions list or empty state', async ({ page }) => {
        const questionsList = page.locator('#questionsList');
        await expect(questionsList).toBeVisible();

        // Should show either loading, questions, or empty state
        const hasContent = await questionsList.evaluate((el) => el.children.length > 0);
        expect(hasContent).toBeTruthy();
    });

    test('should have close button with aria-label in modal', async ({ page }) => {
        const closeBtn = page.locator('.close-modal');
        await expect(closeBtn).toHaveAttribute('aria-label', 'Close modal');
    });

    test('should navigate back to chat', async ({ page }) => {
        const backBtn = page.locator('.new-session-btn').filter({ hasText: 'Back to Chat' });

        // Click back button
        await backBtn.click();

        // Should navigate to index.html
        await expect(page).toHaveURL('/');
    });

    test('should have responsive stats grid on mobile', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 667 });

        const statsGrid = page.locator('.stats-grid');

        // Check grid layout (should be 2 columns on mobile)
        const gridTemplateColumns = await statsGrid.evaluate((el) => {
            return window.getComputedStyle(el).gridTemplateColumns;
        });

        // Should have 2 columns (not 4)
        const columnCount = gridTemplateColumns.split(' ').length;
        expect(columnCount).toBe(2);
    });

    test('should have keyboard accessible filter buttons', async ({ page }) => {
        const pendingBtn = page.locator('.filter-btn[data-status="pending"]');

        // Tab to button
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');

        // Press Enter to activate
        await page.keyboard.press('Enter');

        // Button should become active
        await expect(pendingBtn).toHaveClass(/active/);
    });
});
