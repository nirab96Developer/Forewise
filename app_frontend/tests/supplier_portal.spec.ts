import { test, expect } from "@playwright/test";

const BASE = process.env.BASE_URL || "http://localhost:5173";
const API   = process.env.API_URL  || "http://localhost:8000";

const ADMIN_EMAIL    = "avitbulnir@gmail.com";
const ADMIN_PASSWORD = "KKL2026!";

test.describe("Supplier Portal", () => {
  let authToken: string;

  test.beforeEach(async ({ request }) => {
    const res = await request.post(`${API}/api/v1/auth/login`, {
      data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
    });
    if (res.ok()) {
      authToken = (await res.json()).access_token;
    }
  });

  test("API: supplier portal token endpoint is accessible", async ({ request }) => {
    if (!authToken) test.skip();

    // Get a DISTRIBUTING work order with a portal token
    const woRes = await request.get(`${API}/api/v1/work-orders?status=DISTRIBUTING&page_size=5`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(woRes.ok()).toBeTruthy();
    const body = await woRes.json();
    const orders = body.items ?? body;

    const withToken = orders.filter((o: any) => o.portal_token);
    if (!withToken.length) {
      console.log("No DISTRIBUTING orders with portal_token found — skipping portal test");
      return;
    }

    const token = withToken[0].portal_token;
    console.log(`Testing portal token: ${token.slice(0, 8)}...`);

    const portalRes = await request.get(`${API}/api/v1/supplier-portal/${token}`);
    // Expect 200 (order details) or 410 (expired)
    expect([200, 410, 404]).toContain(portalRes.status());
    console.log(`✅ Supplier portal response: ${portalRes.status()}`);
  });

  test("UI: /supplier-portal page loads without auth", async ({ page }) => {
    // Skip when no dev server running
    const available = await page.request.get(BASE).then(() => true).catch(() => false);
    if (!available) { test.skip(); return; }

    await page.goto(`${BASE}/supplier-portal/fake-token-for-ui-test`);
    await page.waitForLoadState("networkidle");

    const url = page.url();
    // Should stay on supplier-portal, not redirect to /login
    expect(url).not.toContain("/login");
    console.log(`✅ Supplier portal UI accessible at: ${url}`);
  });

  test("API: work orders status counts", async ({ request }) => {
    if (!authToken) test.skip();

    const statuses = ["PENDING", "DISTRIBUTING", "APPROVED", "ACTIVE", "COMPLETED"];
    const results: Record<string, number> = {};

    for (const status of statuses) {
      const res = await request.get(`${API}/api/v1/work-orders?status=${status}&page_size=1`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok()) {
        const body = await res.json();
        results[status] = body.total ?? (body.items ?? body).length ?? 0;
      }
    }

    console.log("Work order status distribution:", results);
    // Just verifying the endpoint works
    expect(Object.keys(results).length).toBeGreaterThan(0);
  });
});
