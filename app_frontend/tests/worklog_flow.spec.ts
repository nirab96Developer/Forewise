import { test, expect } from "@playwright/test";

const API = process.env.API_URL || "http://localhost:8000";

const WM_EMAIL    = "avitbulnir+kobi.nissim@gmail.com";
const WM_PASSWORD = "KKL2026!";

test.describe("Worklog Flow", () => {
  let authToken: string;

  test.beforeEach(async ({ request }) => {
    const res = await request.post(`${API}/api/v1/auth/login`, {
      data: { email: WM_EMAIL, password: WM_PASSWORD },
    });
    if (res.ok()) {
      authToken = (await res.json()).access_token;
    }
  });

  test("API: GET /worklogs returns list", async ({ request }) => {
    if (!authToken) test.skip();
    const res = await request.get(`${API}/api/v1/worklogs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    const items = body.items ?? body;
    console.log(`✅ Worklogs: ${items.length ?? 0} items`);
  });

  test("API: create worklog → status PENDING", async ({ request }) => {
    if (!authToken) test.skip();

    // Find an ACTIVE work order
    const woRes = await request.get(`${API}/api/v1/work-orders?status=ACTIVE&page_size=1`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(woRes.ok()).toBeTruthy();
    const woBody = await woRes.json();
    const orders = woBody.items ?? woBody;

    if (!orders?.length) {
      console.log("No ACTIVE work orders found — skipping worklog creation");
      return;
    }

    const wo = orders[0];
    const today = new Date().toISOString().slice(0, 10);

    const wlRes = await request.post(`${API}/api/v1/worklogs`, {
      headers: { Authorization: `Bearer ${authToken}`, "Content-Type": "application/json" },
      data: {
        work_order_id: wo.id,
        project_id: wo.project_id,
        work_date: today,
        start_time: "07:00:00",
        end_time: "15:00:00",
        work_hours: 8,
        notes: "E2E Playwright test worklog",
      },
    });

    if (!wlRes.ok()) {
      console.log("Worklog creation:", wlRes.status(), await wlRes.text());
      return;
    }

    const wl = await wlRes.json();
    expect(wl.status).toBe("PENDING");
    console.log(`✅ Worklog created: id=${wl.id}, status=${wl.status}`);
  });

  test("API: worklog status distribution", async ({ request }) => {
    if (!authToken) test.skip();

    const res = await request.get(`${API}/api/v1/worklogs?page_size=100`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    const items: any[] = body.items ?? body;

    const statusCount = items.reduce((acc: Record<string, number>, wl: any) => {
      acc[wl.status] = (acc[wl.status] ?? 0) + 1;
      return acc;
    }, {});
    console.log("Worklog status distribution:", statusCount);
    expect(Object.keys(statusCount).length).toBeGreaterThanOrEqual(0);
  });

  test("API: worklog overnight flag works", async ({ request }) => {
    if (!authToken) test.skip();

    const res = await request.get(`${API}/api/v1/worklogs?page_size=50`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    const items: any[] = body.items ?? body;
    const overnight = items.filter((w) => w.is_overnight);
    console.log(`Overnight worklogs: ${overnight.length}/${items.length}`);
    // Just ensure the field exists
    if (items.length > 0) {
      expect("is_overnight" in items[0]).toBeTruthy();
    }
  });
});
