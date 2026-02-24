module.exports = {
  // API key from environment variable (set in GitLab CI/CD)
  apiKey: process.env.APPLITOOLS_API_KEY,
  
  // Application name in Applitools dashboard
  appName: 'Forest Management System',
  
  // Batch name for grouping tests
  batchName: process.env.CI ? 'GitLab CI - Visual Tests' : 'Local Development',
  
  // Browsers to test (Ultrafast Grid)
  browser: [
    // Desktop
    { width: 1920, height: 1080, name: 'chrome' },
    { width: 1440, height: 900, name: 'chrome' },
    // Tablet
    { width: 768, height: 1024, name: 'chrome' },
    // Mobile
    { width: 390, height: 844, name: 'chrome' },  // iPhone 14
    { width: 375, height: 812, name: 'chrome' },  // iPhone X
  ],
  
  // Match level for visual comparison
  matchLevel: 'Layout',
  
  // Ignore caret for input fields
  ignoreCaret: true,
  
  // Send DOM snapshot
  sendDom: true,
  
  // Fail on diff
  failCypressOnDiff: true,
};

