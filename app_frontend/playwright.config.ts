import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: 'tests',
  timeout: 45_000,
  retries: 1,
  reporter: [['html'], ['line'], ['allure-playwright']],
  use: {
    baseURL: process.env.BASE_URL || 'https://forewise.co',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    locale: 'he-IL'
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile',   use: { ...devices['Pixel 7'] } }
  ]
});
