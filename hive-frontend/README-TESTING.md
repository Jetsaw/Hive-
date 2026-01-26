# HIVE Automated Testing Guide

## Overview

This project uses Playwright for automated end-to-end testing of both the user interface and admin dashboard.

## Setup

### 1. Install Node.js

Download and install Node.js from https://nodejs.org/ (LTS version recommended)

### 2. Install Dependencies

```bash
cd hive-frontend
npm install
```

### 3. Install Playwright Browsers

```bash
npx playwright install
```

## Running Tests

### Run All Tests

```bash
npm test
```

### Run Tests in UI Mode (Interactive)

```bash
npm run test:ui
```

### Run Tests in Headed Mode (See Browser)

```bash
npm run test:headed
```

### Run Specific Test File

```bash
npx playwright test tests/ui.spec.js
```

### Run Tests in Specific Browser

```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### View Test Report

```bash
npm run test:report
```

## Test Structure

```
hive-frontend/
├── tests/
│   ├── ui.spec.js           # User interface tests
│   ├── admin.spec.js        # Admin dashboard tests
│   └── accessibility.spec.js # Accessibility tests
├── playwright.config.js      # Playwright configuration
└── package.json             # Dependencies and scripts
```

## Test Coverage

### User Interface Tests (`ui.spec.js`)

- ✅ Welcome section displays without emojis
- ✅ All icons are SVG (not emoji)
- ✅ ARIA labels on all icon buttons
- ✅ Theme toggle functionality
- ✅ Visible focus states for keyboard navigation
- ✅ Settings modal open/close
- ✅ Form labels properly associated
- ✅ Loading state on send button
- ✅ Quick action cards with SVG icons
- ✅ Minimum touch target sizes (44x44px)
- ✅ Reduced motion support
- ✅ No horizontal scroll on mobile

### Admin Dashboard Tests (`admin.spec.js`)

- ✅ Admin header with SVG logo
- ✅ Back to chat button with SVG icon
- ✅ Stats grid with 4 cards
- ✅ Filter buttons functionality
- ✅ Refresh button with SVG icon
- ✅ Questions list display
- ✅ Modal close button with aria-label
- ✅ Navigation back to chat
- ✅ Responsive stats grid on mobile
- ✅ Keyboard accessible filter buttons

### Accessibility Tests (`accessibility.spec.js`)

- ✅ No accessibility violations
- ✅ All images have alt text
- ✅ All buttons have accessible names
- ✅ All form inputs have labels
- ✅ Sufficient color contrast
- ✅ Keyboard navigation support
- ✅ Modal closes with Escape key
- ✅ Proper heading hierarchy
- ✅ HTML lang attribute present

## Continuous Integration

To run tests in CI/CD pipeline:

```bash
# GitHub Actions example
- name: Install dependencies
  run: npm ci
  
- name: Install Playwright browsers
  run: npx playwright install --with-deps
  
- name: Run tests
  run: npm test
```

## Debugging Tests

### Debug Specific Test

```bash
npx playwright test tests/ui.spec.js --debug
```

### Generate Test Code

```bash
npx playwright codegen http://localhost:8080
```

### View Trace

```bash
npx playwright show-trace trace.zip
```

## Writing New Tests

Example test structure:

```javascript
const { test, expect } = require('@playwright/test');

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should do something', async ({ page }) => {
    const element = page.locator('#elementId');
    await expect(element).toBeVisible();
    await element.click();
    // Add assertions
  });
});
```

## Best Practices

1. **Use data-testid attributes** for stable selectors
2. **Wait for elements** instead of using fixed timeouts
3. **Test user behavior** not implementation details
4. **Keep tests independent** - each test should work in isolation
5. **Use descriptive test names** that explain what is being tested
6. **Group related tests** using `test.describe()`

## Troubleshooting

### Tests Fail with "Timeout"

Increase timeout in `playwright.config.js`:

```javascript
use: {
  timeout: 30000, // 30 seconds
}
```

### Browser Not Found

Reinstall browsers:

```bash
npx playwright install --force
```

### Port Already in Use

Change port in `playwright.config.js`:

```javascript
webServer: {
  command: 'python -m http.server 8081',
  url: 'http://localhost:8081',
}
```

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Accessibility Testing](https://playwright.dev/docs/accessibility-testing)
