/// <reference types="cypress" />

Cypress.Commands.add('loginAsAdmin', () => {
  const api = Cypress.env('API_BASE_URL')
  cy.request('POST', `${api}/api/v1/auth/login`, {
    email: Cypress.env('ADMIN_EMAIL'),
    password: Cypress.env('ADMIN_PASSWORD')
  }).then(({ body }) => {
    window.localStorage.setItem('access_token', body.access_token)
  })
})

Cypress.Commands.add('visitApp', (path: string) => {
  cy.visit(`${Cypress.env('APP_BASE_URL')}${path}`)
})

Cypress.Commands.add('toastShouldContain', (text: string) => {
  cy.get('[data-testid=toast-success],[data-testid=toast-error]').contains(text).should('exist')
})

declare global {
  namespace Cypress {
    interface Chainable {
      loginAsAdmin(): Chainable<void>
      visitApp(path: string): Chainable<void>
      toastShouldContain(text: string): Chainable<void>
    }
  }
}
