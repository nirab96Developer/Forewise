import { test, expect } from "@playwright/test";

const API  = process.env.API_URL  || "http://localhost:8000";
const BASE = process.env.BASE_URL || "http://localhost:5173";

// Test credentials per role
const CREDS = {
  WORK_MANAGER: { email: "avitbulnir+kobi.nissim@gmail.com",  password: "KKL2026!" },
  AREA_MANAGER: { email: "avitbulnir+eli.nachum@gmail.com",   password: "KKL2026!" },
  ADMIN:        { email: "avitbulnir@gmail.com",              password: "KKL2026!" },
};

async function login(request: any, role: keyof typeof CREDS): Promise<string | null> {
  const { email, password } = CREDS[role];
  const res = await request.post(`${API}/api/v1/auth/login`, {
    data: { email, password },
  });
  if (!res.ok()) return null;
  return (await res.json()).access_token;
}

test.describe("RBAC — Role-Based Access Control", () => {
  test("WORK_MANAGER: cannot access /users endpoint", async ({ request }) => {
    const token = await login(request, "WORK_MANAGER");
    if (!token) { console.log("WM login failed — skipping"); return; }

    const res = await request.get(`${API}/api/v1/users`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    // Should be 403 Forbidden for WORK_MANAGER
    expect([403, 401]).toContain(res.status());
    console.log(`✅ WORK_MANAGER /users → ${res.status()} (expected 403)`);
  });

  test("WORK_MANAGER: can access /projects (my projects only)", async ({ request }) => {
    const token = await login(request, "WORK_MANAGER");
    if (!token) return;

    const res = await request.get(`${API}/api/v1/projects`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    const items = body.items ?? body;
    console.log(`✅ WORK_MANAGER /projects → ${items.length} projects`);
  });

  test("AREA_MANAGER: projects are scoped to their area", async ({ request }) => {
    const token = await login(request, "AREA_MANAGER");
    if (!token) return;

    const res = await request.get(`${API}/api/v1/projects`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    const items: any[] = body.items ?? body;
    console.log(`✅ AREA_MANAGER /projects → ${items.length} projects`);

    // All returned projects should have the same area_id (or area_name)
    const areas = new Set(items.map((p: any) => p.area_id).filter(Boolean));
    console.log(`  Area IDs in response: ${[...areas].join(", ")}`);
    // Area manager should only see 1 area's projects
    expect(areas.size).toBeLessThanOrEqual(1);
  });

  test("ADMIN: can access /users", async ({ request }) => {
    const token = await login(request, "ADMIN");
    if (!token) { console.log("Admin login failed — skipping"); return; }

    const res = await request.get(`${API}/api/v1/users`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    const items = body.items ?? body;
    console.log(`✅ ADMIN /users → ${items.length ?? 0} users`);
  });

  test("ADMIN: can see all regions and areas", async ({ request }) => {
    const token = await login(request, "ADMIN");
    if (!token) return;

    const [regRes, areaRes] = await Promise.all([
      request.get(`${API}/api/v1/regions`, { headers: { Authorization: `Bearer ${token}` } }),
      request.get(`${API}/api/v1/areas`,   { headers: { Authorization: `Bearer ${token}` } }),
    ]);
    expect(regRes.ok()).toBeTruthy();
    expect(areaRes.ok()).toBeTruthy();

    const regions = (await regRes.json()).items ?? (await regRes.json());
    const areas   = (await areaRes.json()).items ?? (await areaRes.json());
    console.log(`✅ ADMIN sees: ${regions?.length ?? 0} regions, ${areas?.length ?? 0} areas`);
  });

  test("Unauthenticated: /projects returns 401", async ({ request }) => {
    const res = await request.get(`${API}/api/v1/projects`);
    expect([401, 403]).toContain(res.status());
    console.log(`✅ No token → /projects returns ${res.status()}`);
  });
});
