import { test, expect } from '@playwright/test';

test.describe('Sources UI Accessibility', () => {
  test('Verify Sources UI Accessibility', async ({ page, context }) => {
    // Navigate and capture errors
    page.on('console', msg => console.log('Browser log:', msg.text()));
    page.on('pageerror', error => console.error('Browser error:', error.message));

    // Wait for vite to be ready
    await page.waitForTimeout(2000);

    // Mock ALL API responses to prevent 500 errors from backend which might not be running
    await context.route('**/api/v1/**', async (route, request) => {
      const url = request.url();
      if (url.includes('/sources')) {
        const json = [
          {
            id: '1',
            name: 'Test Source',
            source_type: 'rss',
            url: 'https://test.com/rss',
            category: 'local',
            enabled: true,
            created_at: new Date().toISOString()
          }
        ];
        await route.fulfill({ status: 200, json });
      } else {
        await route.fulfill({ status: 200, json: {} });
      }
    });

    await page.goto('http://localhost:3000/sources', { waitUntil: 'networkidle' });

    // Take screenshot to see what's loaded
    await page.screenshot({ path: '/home/jules/verification/sources-debug.png' });

    // Wait for the sources list to load
    await expect(page.locator('text=Test Source')).toBeVisible({ timeout: 10000 });

    // Test row buttons
    const editButton = page.getByRole('button', { name: 'Edit source' });
    await expect(editButton).toBeVisible();
    await editButton.focus();

    // To visualize focus, press tab to move to the next item
    await page.keyboard.press('Tab');

    // Take screenshot of focused edit button
    await page.screenshot({ path: '/home/jules/verification/sources-row-focus.png' });

    // Test modal
    await page.getByRole('button', { name: 'Add Source' }).click();
    await expect(page.getByRole('heading', { name: 'Add Source' })).toBeVisible();

    // Test label associations
    const nameInput = page.getByLabel('Name');
    await expect(nameInput).toBeVisible();

    // Click label to focus input
    await page.locator('label:has-text("Name")').click();
    await expect(nameInput).toBeFocused();

    const typeSelect = page.getByLabel('Type');
    await expect(typeSelect).toBeVisible();

    const urlInput = page.getByLabel('RSS Feed URL');
    await expect(urlInput).toBeVisible();

    const categorySelect = page.getByLabel('Category');
    await expect(categorySelect).toBeVisible();

    const enabledCheckbox = page.getByLabel('Enabled');
    await expect(enabledCheckbox).toBeVisible();

    // Take screenshot of open modal
    await page.screenshot({ path: '/home/jules/verification/sources-modal.png' });
  });
});