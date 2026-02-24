describe('Work Manager flows', () => {
  beforeEach(() => cy.loginAsAdmin())

  it('ניווט בתפריט ראשי', () => {
    cy.visitApp('/dashboard/work-manager')
    cy.get('[data-testid=nav-my-projects]').click()
    cy.url().should('include', '/projects/my')
    cy.get('[data-testid=nav-activity]').click()
    cy.url().should('include', '/activity-log')
  })

  it('דף פרויקטים – צפייה, הזמנה, דיווח, היסטוריה', () => {
    cy.visitApp('/projects/my')
    cy.get('[data-testid=project-view]').first().click()
    cy.url().should('match', /\/project\/[0-9]+/)

    cy.get('[data-testid=project-order-supplier]').click()
    cy.url().should('include', '/order-supplier')

    cy.go('back')
    cy.get('[data-testid=project-report-hours]').click()
    cy.url().should('include', '/report-hours')

    cy.go('back')
    cy.get('[data-testid=project-history]').click()
    cy.url().should('include', '/history')
  })

  it('הזמנת ספק – סבב הוגן', () => {
    cy.visitApp('/project/123/order-supplier/fair')
    cy.get('[data-testid=fair-tool-type]').click().contains('מחלץ').click()
    cy.get('[data-testid=fair-start-date]').type('2025-10-26')
    cy.get('[data-testid=fair-days]').clear().type('3')
    cy.get('[data-testid=fair-add-tool]').click().click() // שני כלים
    cy.get('[data-testid=fair-submit]').click()
    cy.toastShouldContain('נשלחו הזמנות')
  })

  it('דיווח שעות – תקן ואז שליחה', () => {
    cy.visitApp('/project/123/report-hours')
    cy.get('[data-testid=hours-standard]').click()
    cy.get('[data-testid=hours-activity]').click().contains('גיזום').click()
    cy.get('[data-testid=hours-submit]').click()
    cy.toastShouldContain('הדוח נשלח')
  })
})
