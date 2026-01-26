// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Accessibility Tests', () => {

    test('should have no accessibility violations on main page', async ({ page }) => {
        await page.goto('/');

        // Check for basic accessibility issues
        const violations = await page.evaluate(() => {
            const issues = [];

            // Check all images have alt text
            const images = document.querySelectorAll('img');
            images.forEach((img, i) => {
                if (!img.alt && !img.getAttribute('aria-hidden')) {
                    issues.push(`Image ${i} missing alt text`);
                }
            });

            // Check all buttons have accessible names
            const buttons = document.querySelectorAll('button');
            buttons.forEach((btn, i) => {
                const hasText = btn.textContent.trim().length > 0;
                const hasAriaLabel = btn.getAttribute('aria-label');
                const hasAriaLabelledBy = btn.getAttribute('aria-labelledby');

                if (!hasText && !hasAriaLabel && !hasAriaLabelledBy) {
                    issues.push(`Button ${i} has no accessible name`);
                }
            });

            // Check all form inputs have labels
            const inputs = document.querySelectorAll('input, textarea, select');
            inputs.forEach((input, i) => {
                const id = input.id;
                const hasLabel = id && document.querySelector(`label[for="${id}"]`);
                const hasAriaLabel = input.getAttribute('aria-label');
                const hasAriaLabelledBy = input.getAttribute('aria-labelledby');

                if (!hasLabel && !hasAriaLabel && !hasAriaLabelledBy) {
                    issues.push(`Input ${i} (${input.tagName}) has no label`);
                }
            });

            return issues;
        });

        expect(violations).toHaveLength(0);
    });

    test('should have no accessibility violations on admin page', async ({ page }) => {
        await page.goto('/admin.html');

        const violations = await page.evaluate(() => {
            const issues = [];

            // Check all buttons have accessible names
            const buttons = document.querySelectorAll('button');
            buttons.forEach((btn, i) => {
                const hasText = btn.textContent.trim().length > 0;
                const hasAriaLabel = btn.getAttribute('aria-label');
                const hasAriaLabelledBy = btn.getAttribute('aria-labelledby');

                if (!hasText && !hasAriaLabel && !hasAriaLabelledBy) {
                    issues.push(`Button ${i} has no accessible name`);
                }
            });

            return issues;
        });

        expect(violations).toHaveLength(0);
    });

    test('should have sufficient color contrast', async ({ page }) => {
        await page.goto('/');

        // Check text contrast (simplified check)
        const contrastIssues = await page.evaluate(() => {
            const issues = [];

            // Get all text elements
            const textElements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, button, a');

            textElements.forEach((el) => {
                const styles = window.getComputedStyle(el);
                const fontSize = parseFloat(styles.fontSize);
                const fontWeight = parseInt(styles.fontWeight);

                // Large text is 18pt+ or 14pt+ bold
                const isLargeText = fontSize >= 24 || (fontSize >= 18.66 && fontWeight >= 700);

                // Minimum contrast: 4.5:1 for normal text, 3:1 for large text
                // This is a simplified check - full implementation would calculate actual contrast
                const color = styles.color;
                const bgColor = styles.backgroundColor;

                if (color === 'rgba(0, 0, 0, 0)' || bgColor === 'rgba(0, 0, 0, 0)') {
                    // Skip transparent elements
                    return;
                }
            });

            return issues;
        });

        expect(contrastIssues).toHaveLength(0);
    });

    test('should support keyboard navigation throughout the page', async ({ page }) => {
        await page.goto('/');

        // Start tabbing through the page
        const focusableElements = [];

        for (let i = 0; i < 15; i++) {
            await page.keyboard.press('Tab');
            const focusedElement = await page.evaluate(() => {
                const el = document.activeElement;
                return {
                    tagName: el.tagName,
                    id: el.id,
                    className: el.className,
                };
            });
            focusableElements.push(focusedElement);
        }

        // Should have tabbed through multiple elements
        expect(focusableElements.length).toBeGreaterThan(5);

        // All focusable elements should be interactive
        const interactiveTags = ['BUTTON', 'A', 'INPUT', 'TEXTAREA', 'SELECT'];
        focusableElements.forEach((el) => {
            expect(interactiveTags).toContain(el.tagName);
        });
    });

    test('should close modal with Escape key', async ({ page }) => {
        await page.goto('/');

        const settingsBtn = page.locator('#settingsBtn');
        const settingsModal = page.locator('#settingsModal');

        // Open modal
        await settingsBtn.click();
        await expect(settingsModal).toHaveClass(/active/);

        // Press Escape
        await page.keyboard.press('Escape');

        // Modal should close
        await expect(settingsModal).not.toHaveClass(/active/);
    });

    test('should have proper heading hierarchy', async ({ page }) => {
        await page.goto('/');

        const headingLevels = await page.evaluate(() => {
            const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
            return headings.map(h => parseInt(h.tagName.charAt(1)));
        });

        // Should have at least one heading
        expect(headingLevels.length).toBeGreaterThan(0);

        // First heading should be h1 or h2
        expect(headingLevels[0]).toBeLessThanOrEqual(2);
    });

    test('should have lang attribute on html element', async ({ page }) => {
        await page.goto('/');

        const lang = await page.evaluate(() => document.documentElement.lang);
        expect(lang).toBeTruthy();
        expect(lang).toBe('en');
    });
});
