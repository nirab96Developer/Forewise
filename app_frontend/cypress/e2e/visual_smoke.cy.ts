/**
 * Visual Smoke Tests with Applitools
 * These tests capture visual snapshots of key pages across multiple viewports
 */

// Import Applitools commands only for visual tests
import '@applitools/eyes-cypress/commands';

describe('Visual Smoke Tests', () => {
  beforeEach(() => {
    // Clear any previous sessions
    cy.clearCookies();
    cy.clearLocalStorage();
  });

  it('Login page visual check', () => {
    cy.visit('/login');

    cy.eyesOpen({
      appName: 'Forest Management System',
      testName: 'Login Page',
    });

    cy.eyesCheckWindow({
      tag: 'Login Page - Desktop',
      fully: true,
    });

    cy.eyesClose();
  });

  it('Login page - Mobile viewport', () => {
    cy.viewport(390, 844); // iPhone 14
    cy.visit('/login');

    cy.eyesOpen({
      appName: 'Forest Management System',
      testName: 'Login Page - Mobile',
    });

    cy.eyesCheckWindow({
      tag: 'Login Page - Mobile',
      fully: true,
    });

    cy.eyesClose();
  });

  describe('Authenticated pages', () => {
    beforeEach(() => {
      // Login before each test
      cy.visit('/login');
      
      // Wait for login page to load
      cy.get('input[type="text"], input[name="username"], input[placeholder*="משתמש"]', { timeout: 10000 })
        .should('be.visible');
    });

    it('Dashboard visual check after login', () => {
      // Attempt login with test credentials
      cy.get('input[type="text"], input[name="username"], input[placeholder*="משתמש"]')
        .first()
        .type('admin');
      
      cy.get('input[type="password"]')
        .first()
        .type('Admin123!');
      
      cy.get('button[type="submit"]').click();

      // Wait for navigation
      cy.url({ timeout: 15000 }).should('not.include', '/login');

      cy.eyesOpen({
        appName: 'Forest Management System',
        testName: 'Dashboard',
      });

      cy.eyesCheckWindow({
        tag: 'Dashboard - After Login',
        fully: true,
      });

      cy.eyesClose();
    });
  });
});

describe('Responsive Visual Tests', () => {
  const viewports = [
    { name: 'Desktop', width: 1920, height: 1080 },
    { name: 'Laptop', width: 1440, height: 900 },
    { name: 'Tablet', width: 768, height: 1024 },
    { name: 'Mobile', width: 390, height: 844 },
  ];

  viewports.forEach((viewport) => {
    it(`Login page - ${viewport.name} (${viewport.width}x${viewport.height})`, () => {
      cy.viewport(viewport.width, viewport.height);
      cy.visit('/login');

      cy.eyesOpen({
        appName: 'Forest Management System',
        testName: `Responsive - ${viewport.name}`,
      });

      cy.eyesCheckWindow({
        tag: `Login - ${viewport.name}`,
        fully: true,
      });

      cy.eyesClose();
    });
  });
});

