describe('Offline behaviour', () => {
  it('שומר טיוטה ומתריע על Offline', () => {
    cy.visitApp('/project/123/report-hours')

    // מדמים כשל רשת ב-API
    cy.intercept('POST', '**/api/v1/worklogs', { forceNetworkError: true }).as('submitOffline')

    cy.get('[data-testid=hours-standard]').click()
    cy.get('[data-testid=hours-submit]').click()

    cy.get('[data-testid=toast-error]').should('exist')
    cy.contains('אתה במצב לא מקוון').should('exist')
    cy.contains('הנתונים יסונכרנו בחיבור הבא').should('exist')
  })
})
