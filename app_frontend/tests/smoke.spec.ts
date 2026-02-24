import { test, expect } from '@playwright/test';

test('login -> dashboard KPIs visible', async ({ page }) => {
  await page.goto('/login');
  await page.getByRole('textbox', { name: /user|email|׳©׳ ׳׳©׳×׳׳©/i }).fill('admin');
  await page.getByRole('textbox', { name: /pass|׳¡׳™׳¡׳׳”/i }).fill('admin123');
  await page.keyboard.press('Enter');

  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByText(/׳׳•׳— ׳‘׳§׳¨׳”|׳׳ ׳”׳ ׳׳¢׳¨׳›׳×/i)).toBeVisible();
  await expect(page.getByText(/׳₪׳¨׳•׳™׳§׳˜׳™׳ ׳₪׳¢׳™׳׳™׳|׳“׳™׳•׳•׳—׳™׳ ׳׳׳×׳™׳ ׳™׳/i)).toBeVisible();
});
