describe('Topbar & commons', () => {
  beforeEach(() => cy.loginAsAdmin())

  it('התראות/שפה/מצב כהה', () => {
    cy.visitApp('/dashboard/work-manager')
    cy.get('[data-testid=topbar-notifications]').click()
    cy.get('[data-testid=topbar-language]').click().contains('English').click()
    cy.get('[data-testid=topbar-theme]').click()
  })
})
