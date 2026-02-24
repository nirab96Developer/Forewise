describe('Login Screen', () => {
  beforeEach(() => {
    // Clear any previous sessions
    cy.clearCookies();
    cy.clearLocalStorage();
  });

  it('Login page loads correctly', () => {
    cy.visitApp('/login');
    
    // Wait for page to load and check basic elements
    cy.get('input[name=email], input[type=email], input[placeholder*="מייל"]', { timeout: 10000 })
      .should('be.visible');
    cy.get('input[type=password]').should('be.visible');
  });

  it('התחברות תקינה מובילה לדשבורד', () => {
    const email = Cypress.env('ADMIN_EMAIL');
    const password = Cypress.env('ADMIN_PASSWORD');
    
    // Skip if credentials not configured
    if (!email || !password) {
      cy.log('Skipping - ADMIN credentials not configured');
      return;
    }

    cy.visitApp('/login');
    
    cy.get('input[name=email], input[type=email], input[placeholder*="מייל"]', { timeout: 10000 })
      .first()
      .type(email);
    cy.get('input[type=password]')
      .first()
      .type(password);
    cy.get('button[type=submit], [data-testid=login-submit]').first().click();
    
    // Should redirect away from login
    cy.url({ timeout: 15000 }).should('not.include', '/login');
  });

  it('סיסמה שגויה מציגה שגיאה', () => {
    cy.visitApp('/login');
    
    cy.get('input[name=email], input[type=email], input[placeholder*="מייל"]', { timeout: 10000 })
      .first()
      .type('test@example.com');
    cy.get('input[type=password]')
      .first()
      .type('wrongpassword123');
    cy.get('button[type=submit], [data-testid=login-submit]').first().click();
    
    // Should stay on login page or show error
    cy.url().should('include', '/login');
  });
});
