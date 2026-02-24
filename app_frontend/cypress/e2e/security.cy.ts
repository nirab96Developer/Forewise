describe('Security checks', () => {
  it('גישה בלי טוקן מפנה ל-Login', () => {
    cy.visitApp('/projects/my')
    cy.url().should('include', '/login')
  })

  it('403 ללא הרשאה מציג הודעה מתאימה', () => {
    cy.loginAsAdmin()
    // מדמים תשובת 403 לאנדפוינט מסוים
    cy.intercept('GET', '**/api/v1/projects*', { statusCode: 403, body: { detail: 'forbidden' } })
    cy.visitApp('/projects/my')
    cy.get('[data-testid=toast-error]').should('exist')
  })
})
