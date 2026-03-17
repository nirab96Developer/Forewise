import { test, expect } from '@playwright/test';

// ── Health ──
test('site loads and shows login page', async ({ page }) => {
  await page.goto('/login');
  await expect(page).toHaveTitle(/Forewise/i);
  await expect(page.locator('button[type="submit"], button:has-text("כניסה")')).toBeVisible();
});

test('API health endpoint returns OK', async ({ request }) => {
  const res = await request.get('/api/v1/health');
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  expect(body.status).toBe('ok');
});

// ── Login Flow ──
test('login with valid credentials → dashboard', async ({ page }) => {
  await page.goto('/login');

  await page.locator('input[type="text"], input[name="username"]').first().fill('admin');
  await page.locator('input[type="password"]').first().fill('N123321ir!');
  await page.locator('button[type="submit"], button:has-text("כניסה")').first().click();

  // Should redirect to dashboard or welcome
  await page.waitForURL(/\/(welcome|$)/, { timeout: 15000 });
  // Page should have content (not blank)
  await expect(page.locator('body')).not.toBeEmpty();
});

test('login with wrong password → error', async ({ page }) => {
  await page.goto('/login');

  await page.locator('input[type="text"], input[name="username"]').first().fill('admin');
  await page.locator('input[type="password"]').first().fill('wrongpassword');
  await page.locator('button[type="submit"], button:has-text("כניסה")').first().click();

  // Should stay on login page
  await page.waitForTimeout(3000);
  expect(page.url()).toContain('/login');
});

// ── Navigation ──
test('sidebar navigation items are visible after login', async ({ page }) => {
  // Login first
  await page.goto('/login');
  await page.locator('input[type="text"], input[name="username"]').first().fill('admin');
  await page.locator('input[type="password"]').first().fill('N123321ir!');
  await page.locator('button[type="submit"], button:has-text("כניסה")').first().click();
  await page.waitForURL(/\/(welcome|$)/, { timeout: 15000 });

  // If welcome page, wait for redirect or navigate
  if (page.url().includes('welcome')) {
    await page.waitForURL(/\/$/, { timeout: 10000 }).catch(() => {});
    if (page.url().includes('welcome')) {
      await page.goto('/');
    }
  }

  // Check sidebar has navigation items
  await page.waitForTimeout(2000);
  const nav = page.locator('aside[role="navigation"], nav');
  await expect(nav.first()).toBeVisible({ timeout: 5000 });
});

// ── Key Pages Load ──
test('projects page loads', async ({ page }) => {
  await page.goto('/login');
  await page.locator('input[type="text"], input[name="username"]').first().fill('admin');
  await page.locator('input[type="password"]').first().fill('N123321ir!');
  await page.locator('button[type="submit"], button:has-text("כניסה")').first().click();
  await page.waitForURL(/\/(welcome|$)/, { timeout: 15000 });

  await page.goto('/projects');
  await page.waitForTimeout(3000);
  expect(page.url()).toContain('/projects');
});

test('settings page loads', async ({ page }) => {
  await page.goto('/login');
  await page.locator('input[type="text"], input[name="username"]').first().fill('admin');
  await page.locator('input[type="password"]').first().fill('N123321ir!');
  await page.locator('button[type="submit"], button:has-text("כניסה")').first().click();
  await page.waitForURL(/\/(welcome|$)/, { timeout: 15000 });

  await page.goto('/settings');
  await page.waitForTimeout(3000);
  expect(page.url()).toContain('/settings');
});

// ── Supplier Portal ──
test('supplier portal with invalid token shows error', async ({ page }) => {
  await page.goto('/supplier-portal/invalid-token-test');
  await page.waitForTimeout(3000);
  // Should show some content (error or expired message), not blank page
  await expect(page.locator('body')).not.toBeEmpty();
});

// ── API Endpoints ──
test('API /suppliers returns data', async ({ request }) => {
  // Login to get token
  const loginRes = await request.post('/api/v1/auth/login', {
    data: { username: 'admin', password: 'N123321ir!' }
  });
  expect(loginRes.ok()).toBeTruthy();
  const { access_token } = await loginRes.json();

  // Fetch suppliers
  const res = await request.get('/api/v1/suppliers', {
    headers: { Authorization: `Bearer ${access_token}` }
  });
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  expect(body.items.length).toBeGreaterThan(0);
});

test('API /equipment returns data', async ({ request }) => {
  const loginRes = await request.post('/api/v1/auth/login', {
    data: { username: 'admin', password: 'N123321ir!' }
  });
  const { access_token } = await loginRes.json();

  const res = await request.get('/api/v1/equipment?page_size=5', {
    headers: { Authorization: `Bearer ${access_token}` }
  });
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  expect(body.items.length).toBeGreaterThan(0);
});
