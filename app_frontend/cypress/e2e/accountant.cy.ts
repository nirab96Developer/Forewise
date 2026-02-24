describe('Accountant flows', () => {
  beforeEach(() => cy.loginAsAdmin())

  it('עיבוד דיווחים', () => {
    cy.visitApp('/worklogs/pending')
    cy.get('[data-testid=worklog-view-details]').first().click()
    cy.get('[data-testid=worklog-approve]').first().click()
    cy.toastShouldContain('דוח אושר')
  })

  it('הפקת חשבונית', () => {
    cy.visitApp('/invoices/new')
    cy.get('[data-testid=invoice-pick-supplier]').click().contains('ספק הדגמה').click()
    cy.get('[data-testid=invoice-pick-range]').type('2025-10-01 - 2025-10-31')
    cy.get('[data-testid=invoice-attach-worklogs]').click()
    cy.get('[data-testid=invoice-calc]').click()
    cy.get('[data-testid=invoice-generate]').click()
    cy.toastShouldContain('חשבונית הופקה')
  })
})
