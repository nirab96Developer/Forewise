import { defineConfig } from 'cypress'

export default defineConfig({
  e2e: {
    // Use CYPRESS_baseUrl from environment (GitLab CI/CD) or fallback to production
    baseUrl: process.env.CYPRESS_baseUrl || 'http://167.99.228.10',
    env: {
      // All sensitive values come from environment variables (GitLab CI/CD Variables)
      API_BASE_URL: process.env.CYPRESS_API_BASE_URL,
      APP_BASE_URL: process.env.CYPRESS_APP_BASE_URL,
      ADMIN_EMAIL: process.env.CYPRESS_ADMIN_EMAIL,
      ADMIN_PASSWORD: process.env.CYPRESS_ADMIN_PASSWORD,
    },
    video: true,
    screenshotOnRunFailure: true,
    viewportWidth: 1366,
    viewportHeight: 900,
    defaultCommandTimeout: 10000,
    retries: {
      runMode: 2,
      openMode: 0
    },
    setupNodeEvents(_on, config) {
      // Applitools Eyes setup is handled via applitools.config.js
      return config
    },
  },
})
