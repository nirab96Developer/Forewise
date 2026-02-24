import fs from "fs/promises";
import path from "path";
import { chromium, devices } from "playwright";

const BASE_URL = "http://127.0.0.1:5173";
const LOGIN_USER = "admin";
const LOGIN_PASS = "StrongPass123!";
const RESET_EMAIL = "avitbulnir+admin@gmail.com";
const OUT_DIR = "/root/kkl-forest/evidence/login-step1";

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function storageSnapshot(page) {
  return page.evaluate(() => ({
    localStorage: Object.fromEntries(
      Array.from({ length: localStorage.length }, (_, i) => {
        const k = localStorage.key(i);
        return [k, localStorage.getItem(k)];
      })
    ),
    sessionStorage: Object.fromEntries(
      Array.from({ length: sessionStorage.length }, (_, i) => {
        const k = sessionStorage.key(i);
        return [k, sessionStorage.getItem(k)];
      })
    ),
    url: location.href,
  }));
}

async function writeJson(name, data) {
  await fs.writeFile(path.join(OUT_DIR, name), JSON.stringify(data, null, 2), "utf-8");
}

async function fillAndLogin(page, remember) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await page.fill('[name="username"]', LOGIN_USER);
  await page.fill('[name="password"]', LOGIN_PASS);
  const checkbox = page.locator('input[type="checkbox"]');
  const checked = await checkbox.isChecked();
  if (remember && !checked) await checkbox.check();
  if (!remember && checked) await checkbox.uncheck();
  await page.click('[data-testid="login-submit"]');
  await page.waitForTimeout(1800);
}

async function main() {
  await ensureDir(OUT_DIR);

  const userDataOn = "/tmp/pw-remember-on";
  const userDataOff = "/tmp/pw-remember-off";
  await fs.rm(userDataOn, { recursive: true, force: true });
  await fs.rm(userDataOff, { recursive: true, force: true });

  // 1) Remember ON
  let context = await chromium.launchPersistentContext(userDataOn, {
    headless: true,
    viewport: { width: 1440, height: 900 },
  });
  let page = context.pages()[0] ?? (await context.newPage());
  await fillAndLogin(page, true);
  await page.screenshot({ path: path.join(OUT_DIR, "1-remember-on-after-login.png"), fullPage: true });
  await writeJson("1-remember-on-storage.json", await storageSnapshot(page));
  await context.close();

  // Reopen profile: should stay logged in
  context = await chromium.launchPersistentContext(userDataOn, {
    headless: true,
    viewport: { width: 1440, height: 900 },
  });
  page = context.pages()[0] ?? (await context.newPage());
  await page.goto(`${BASE_URL}/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(OUT_DIR, "1-remember-on-reopen.png"), fullPage: true });
  await writeJson("1-remember-on-reopen-storage.json", await storageSnapshot(page));

  // 2) Auto refresh from refresh token
  const refreshCalls = [];
  page.on("response", async (resp) => {
    if (resp.url().includes("/api/v1/auth/refresh")) {
      refreshCalls.push({ url: resp.url(), status: resp.status() });
    }
  });
  await page.evaluate(() => localStorage.removeItem("access_token"));
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  await writeJson("2-auto-refresh-network.json", refreshCalls);
  await page.screenshot({ path: path.join(OUT_DIR, "2-auto-refresh-after-reload.png"), fullPage: true });
  await context.close();

  // 3) Remember OFF
  context = await chromium.launchPersistentContext(userDataOff, {
    headless: true,
    viewport: { width: 1440, height: 900 },
  });
  page = context.pages()[0] ?? (await context.newPage());
  await fillAndLogin(page, false);
  await page.screenshot({ path: path.join(OUT_DIR, "1-remember-off-after-login.png"), fullPage: true });
  await writeJson("1-remember-off-storage.json", await storageSnapshot(page));
  await context.close();

  context = await chromium.launchPersistentContext(userDataOff, {
    headless: true,
    viewport: { width: 1440, height: 900 },
  });
  page = context.pages()[0] ?? (await context.newPage());
  await page.goto(`${BASE_URL}/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(OUT_DIR, "1-remember-off-reopen.png"), fullPage: true });
  await writeJson("1-remember-off-reopen-storage.json", await storageSnapshot(page));

  // 4) Forgot password (request)
  await page.goto(`${BASE_URL}/forgot-password`, { waitUntil: "networkidle" });
  await page.fill('input[type="email"]', RESET_EMAIL);
  await page.click('button[type="submit"]');
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(OUT_DIR, "3-forgot-password-request.png"), fullPage: true });
  await context.close();

  // 5) Biometric desktop visibility
  const browser = await chromium.launch({ headless: true });
  context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  page = await context.newPage();
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  const desktopBioVisible = await page.locator('[data-testid="login-bio"]').isVisible().catch(() => false);
  await page.screenshot({ path: path.join(OUT_DIR, "4-biometric-desktop.png"), fullPage: true });
  await writeJson("4-biometric-desktop.json", { visible: desktopBioVisible });
  await context.close();

  // 6) Biometric mobile visibility
  context = await browser.newContext({
    ...devices["iPhone 13"],
  });
  page = await context.newPage();
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  const mobileBioVisible = await page.locator('[data-testid="login-bio"]').isVisible().catch(() => false);
  await page.screenshot({ path: path.join(OUT_DIR, "4-biometric-mobile.png"), fullPage: true });
  await writeJson("4-biometric-mobile.json", { visible: mobileBioVisible });
  await context.close();

  // 7) PWA manifest + SW
  context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  page = await context.newPage();
  await page.goto(`${BASE_URL}/`, { waitUntil: "networkidle" });
  const manifestResp = await page.request.get(`${BASE_URL}/manifest.webmanifest`);
  await writeJson("5-pwa-manifest.json", {
    status: manifestResp.status(),
    body: await manifestResp.json(),
  });
  const swInfo = await page.evaluate(async () => {
    const regs = await navigator.serviceWorker.getRegistrations();
    return {
      supported: "serviceWorker" in navigator,
      registrations: regs.map((r) => ({
        scope: r.scope,
        active: !!r.active,
      })),
    };
  });
  await writeJson("5-pwa-sw.json", swInfo);
  await page.screenshot({ path: path.join(OUT_DIR, "5-pwa-home.png"), fullPage: true });
  await context.close();
  await browser.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
