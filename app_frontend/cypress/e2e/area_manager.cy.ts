describe('Area Manager flows', () => {
  beforeEach(() => cy.loginAsAdmin())

  it('ניווט ראשי', () => {
    cy.visitApp('/dashboard/area-manager')
    cy.get('[data-testid=nav-area-projects]').click()
    cy.url().should('include', '/projects/area')
  })

  it('ניהול פרויקטים באזור', () => {
    cy.visitApp('/projects/area')
    cy.get('[data-testid=area-project-new]').click()
    cy.url().should('include', '/project/new')
    cy.go('back')
    cy.get('[data-testid=area-assign-manager]').first().click()
    cy.findByText('בחר מנהל').should('exist')
  })

  it('אישורים נדרשים', () => {
    cy.visitApp('/approvals')
    cy.get('[data-testid=approve-overtime]').first().click()
    cy.toastShouldContain('אושר')
  })
})
