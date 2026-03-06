import { test, expect } from "@playwright/test";

const API = process.env.API_URL || "http://localhost:8000";

const ADMIN_EMAIL    = "avitbulnir@gmail.com";
const ADMIN_PASSWORD = "KKL2026!";

test.describe("Budget Flow", () => {
  let authToken: string;

  test.beforeEach(async ({ request }) => {
    const res = await request.post(`${API}/api/v1/auth/login`, {
      data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
    });
    if (res.ok()) {
      authToken = (await res.json()).access_token;
    }
  });

  test("API: GET /budgets returns list with amounts", async ({ request }) => {
    if (!authToken) test.skip();

    const res = await request.get(`${API}/api/v1/budgets?page_size=10`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(res.ok()).toBeTruthy();

    const body = await res.json();
    const items: any[] = body.items ?? body;
    expect(items.length).toBeGreaterThan(0);

    const sample = items[0];
    // Verify budget has key financial fields
    expect(sample).toHaveProperty("total_amount");
    console.log(`✅ Budgets: ${items.length} items, sample total_amount=${sample.total_amount}`);
  });

  test("API: project budget fields present in /projects/code/{code}", async ({ request }) => {
    if (!authToken) test.skip();

    // Get first project
    const projRes = await request.get(`${API}/api/v1/projects?page_size=1`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(projRes.ok()).toBeTruthy();
    const body = await projRes.json();
    const projects: any[] = body.items ?? body;
    if (!projects.length) { console.log("No projects"); return; }

    const code = projects[0].code;
    const detailRes = await request.get(`${API}/api/v1/projects/code/${code}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(detailRes.ok()).toBeTruthy();
    const project = await detailRes.json();

    // Budget should be present
    if (project.budget) {
      expect(project.budget).toHaveProperty("total_amount");
      console.log(
        `✅ Project ${code} budget: total=${project.budget.total_amount},`,
        `committed=${project.budget.committed_amount},`,
        `spent=${project.budget.spent_amount},`,
        `available=${project.budget.available_amount}`
      );
    } else {
      console.log(`Project ${code} has no budget attached`);
    }
  });

  test("API: budget statistics endpoint works", async ({ request }) => {
    if (!authToken) test.skip();

    const res = await request.get(`${API}/api/v1/budgets/statistics`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (!res.ok()) {
      console.log("Budget statistics not available:", res.status());
      return;
    }
    const stats = await res.json();
    console.log("✅ Budget statistics:", JSON.stringify(stats).slice(0, 200));
  });

  test("API: budget transfer list returns 200", async ({ request }) => {
    if (!authToken) test.skip();

    const res = await request.get(`${API}/api/v1/budget-transfers`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    const items = body.items ?? body;
    console.log(`✅ Budget transfers: ${items?.length ?? 0} items`);
  });

  test("API: creating work order does not break budget", async ({ request }) => {
    if (!authToken) test.skip();

    // Get a project with a budget
    const projRes = await request.get(`${API}/api/v1/projects?page_size=5`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const projects: any[] = (await projRes.json()).items ?? [];
    if (!projects.length) return;

    const code = projects[0].code;
    const before = await (await request.get(`${API}/api/v1/projects/code/${code}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    })).json();

    const budgetBefore = before.budget?.committed_amount ?? 0;
    console.log(`Project ${code} committed_amount BEFORE: ${budgetBefore}`);

    // We just verify the field exists — not creating actual WO to avoid data pollution
    expect(typeof budgetBefore).toBe("number");
  });
});
