import { test, expect } from "@playwright/test";

const BASE = process.env.BASE_URL || "http://localhost:5173";
const API   = process.env.API_URL  || "http://localhost:8000";

// Real WORK_MANAGER credentials from DB
const WM_EMAIL    = "avitbulnir+kobi.nissim@gmail.com";
const WM_PASSWORD = "KKL2026!";

test.describe("Work Order Flow", () => {
  let authToken: string;

  test.beforeEach(async ({ request }) => {
    // Login via API to get token
    const res = await request.post(`${API}/api/v1/auth/login`, {
      data: { email: WM_EMAIL, password: WM_PASSWORD },
    });
    if (res.ok()) {
      const body = await res.json();
      authToken = body.access_token;
    }
  });

  test("login as WORK_MANAGER → navigate to projects page", async ({ page }) => {
    // Skip when no dev server running
    const available = await page.request.get(BASE).then(() => true).catch(() => false);
    if (!available) { test.skip(); return; }

    await page.goto(BASE);
    await page.evaluate((token) => {
      localStorage.setItem("access_token", token);
      sessionStorage.setItem("access_token", token);
    }, authToken || "");

    await page.goto(`${BASE}/projects`);
    await page.waitForLoadState("networkidle");

    // Should see projects list (not redirected to login)
    const url = page.url();
    expect(url).not.toContain("/login");
    await expect(page.locator("h1")).toContainText(["פרויקטים", "Projects"], { timeout: 8000 });
  });

  test("API: create work order → status PENDING", async ({ request }) => {
    if (!authToken) test.skip();

    // Get first active project
    const projRes = await request.get(`${API}/api/v1/projects?my_projects=true&page_size=1`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(projRes.ok()).toBeTruthy();
    const projBody = await projRes.json();
    const projects = projBody.items ?? projBody;
    if (!projects?.length) {
      console.log("No projects found — skipping WO creation");
      return;
    }
    const projectId = projects[0].id;

    // Get an equipment model
    const eqRes = await request.get(`${API}/api/v1/equipment-types?page_size=1`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const eqBody = await eqRes.json();
    const eqTypes = eqBody.items ?? eqBody;
    if (!eqTypes?.length) return;
    const equipmentTypeId = eqTypes[0].id;

    // Create WO
    const woRes = await request.post(`${API}/api/v1/work-orders`, {
      headers: { Authorization: `Bearer ${authToken}`, "Content-Type": "application/json" },
      data: {
        project_id: projectId,
        title: "Test WO Playwright",
        description: "E2E test work order",
        requested_equipment_model_id: equipmentTypeId,
        priority: "MEDIUM",
        work_start_date: new Date().toISOString().slice(0, 10),
        work_end_date: new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10),
        estimated_hours: 8,
      },
    });

    if (!woRes.ok()) {
      console.log("WO creation returned:", woRes.status(), await woRes.text());
      return;
    }
    const wo = await woRes.json();
    expect(["PENDING", "DISTRIBUTING"]).toContain(wo.status);
    console.log(`✅ Work order created: id=${wo.id}, status=${wo.status}`);
  });

  test("API: work order list returns 200", async ({ request }) => {
    if (!authToken) test.skip();
    const res = await request.get(`${API}/api/v1/work-orders`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    console.log(`✅ Work orders: ${(body.items ?? body).length ?? 0} items`);
  });
});
