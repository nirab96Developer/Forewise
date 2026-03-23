import os, json
from playwright.sync_api import sync_playwright

OUT = "/root/forewise/screenshots"
os.makedirs(OUT, exist_ok=True)
BASE = "https://forewise.co"
EMAIL = "avitbulnir+admin@gmail.com"
PASSWORD = "Nir321654!"

PAGES = [
    ("02-dashboard-admin", "/", "Admin Dashboard"),
    ("03-projects-list", "/projects", "Projects List"),
    ("04-project-workspace", "/projects/YR-001/workspace", "Project Workspace"),
    ("05-new-work-order", "/projects/YR-001/workspace/work-orders/new", "New Work Order"),
    ("06-order-coordination", "/order-coordination", "Order Coordination"),
    ("07-work-order-detail", "/work-orders/158", "Work Order Detail"),
    ("08-accountant-inbox", "/accountant-inbox", "Accountant Inbox"),
    ("09-pricing-reports", "/reports/pricing", "Pricing Reports"),
    ("10-supplier-management", "/settings/suppliers", "Supplier Management"),
    ("11-equipment-scan", "/equipment/scan", "Equipment Scan"),
    ("12-user-management", "/settings/admin/users", "User Management"),
    ("13-roles-permissions", "/settings/admin/roles", "Roles & Permissions"),
    ("14-forest-map", "/map", "Forest Map"),
    ("15-system-settings", "/settings", "System Settings"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="he-IL")
    page = ctx.new_page()

    # Screenshot login page
    print("01. Login page...")
    page.goto(f"{BASE}/login", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2000)
    page.screenshot(path=f"{OUT}/01-login.png", full_page=True)
    print("   OK")

    # Login via API to get token, then inject into localStorage
    print("Logging in via API...")
    resp = page.evaluate("""async () => {
        const r = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: '""" + EMAIL + """', password: '""" + PASSWORD + """'})
        });
        return {status: r.status, body: await r.json()};
    }""")
    print(f"   Login response: {resp['status']}")
    
    if resp['status'] == 200:
        token = resp['body'].get('access_token', '')
        user = resp['body'].get('user', {})
        print(f"   Token: {token[:30]}...")
        # Store in localStorage like the app does
        page.evaluate(f"""() => {{
            localStorage.setItem('access_token', '{token}');
            localStorage.setItem('token', '{token}');
            localStorage.setItem('user', JSON.stringify({json.dumps(user)}));
        }}""")
        print("   Token stored in localStorage")
    else:
        print(f"   Login failed: {resp['body']}")
        # Try alternate credentials
        resp2 = page.evaluate("""async () => {
            const r = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username: 'avitbulnir+admin@gmail.com', password: 'Admin123!'})
            });
            return {status: r.status, body: await r.json()};
        }""")
        print(f"   Alt login: {resp2['status']}")
        if resp2['status'] == 200:
            token = resp2['body'].get('access_token', '')
            user = resp2['body'].get('user', {})
            page.evaluate(f"""() => {{
                localStorage.setItem('access_token', '{token}');
                localStorage.setItem('token', '{token}');
                localStorage.setItem('user', JSON.stringify({json.dumps(user)}));
            }}""")

    # Now take all screenshots
    for fn, path, desc in PAGES:
        print(f"{fn}. {desc}...")
        try:
            page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(3000)
            page.screenshot(path=f"{OUT}/{fn}.png", full_page=True)
            cur = page.url
            is_login = "/login" in cur
            print(f"   {'REDIRECT TO LOGIN!' if is_login else 'OK'} ({cur})")
        except Exception as e:
            print(f"   ERR: {e}")

    browser.close()

print(f"\nDone! {len([f for f in os.listdir(OUT) if f.endswith('.png')])} screenshots")
for f in sorted(os.listdir(OUT)):
    if f.endswith(".png"):
        print(f"  {f} ({os.path.getsize(OUT+'/'+f)//1024}KB)")
