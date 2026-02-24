import { test, expect } from '@playwright/test';
import { AxeBuilder } from '@axe-core/playwright';

test('a11y on /projects', async ({ page }) => {
  await page.goto('/projects');
  const results = await new AxeBuilder({ page }).withTags(['wcag2a','wcag2aa']).analyze();
  // ׳ ׳›׳©׳™׳ ׳¨׳§ ׳›׳©׳™׳© ׳‘׳¢׳™׳•׳× ׳§׳¨׳™׳˜׳™׳•׳× ׳›׳“׳™ ׳׳ ׳׳—׳¡׳•׳ ׳‘׳×׳—׳׳”
  const critical = results.violations.filter(v => ['critical','serious'].includes(v.impact as any));
  expect(critical, JSON.stringify(critical, null, 2)).toHaveLength(0);
});
