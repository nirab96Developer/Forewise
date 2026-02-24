describe('Supplier portal 3h window', () => {
  it('אישור הזמנה בזמן', () => {
    cy.visitApp('/portal/supplier/token123')
    cy.get('[data-testid=supplier-plate]').type('12-345-67')
    cy.get('[data-testid=supplier-approve]').click()
    cy.url().should('include', '/portal/confirmed')
  })
})
