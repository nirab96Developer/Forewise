describe('Region Manager flows', () => {
  beforeEach(() => cy.loginAsAdmin())

  it('תקציב אזורי', () => {
    cy.visitApp('/budget/region')
    cy.get('[data-testid=budget-allocate]').click()
    cy.findByText('הקצאת תקציב').should('exist')
    cy.get('[data-testid=budget-transfer]').click()
    cy.findByText('העברת תקציב').should('exist')
  })
})
