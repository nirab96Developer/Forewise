import asyncio
from playwright.async_api import async_playwright

DIAGRAMS = [
    ("https://forewise.co/usecase-diagram.html", "forewise-usecase-diagram.png", 1300),
    ("https://forewise.co/usecase-full.html", "forewise-usecase-full.png", 1400),
    ("https://forewise.co/usecase-roles.html", "forewise-usecase-by-role.png", 1200),
    ("https://forewise.co/activity-diagram.html", "forewise-activity-diagram.png", 1100),
    ("https://forewise.co/class-diagram.html", "forewise-class-diagram.png", 1500),
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        for url, filename, width in DIAGRAMS:
            page = await browser.new_page(
                viewport={"width": width, "height": 800},
                device_scale_factor=3
            )
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            path = f"/root/forewise/docs/{filename}"
            await page.screenshot(path=path, full_page=True, type="png")
            print(f"Saved: {path}")
            await page.close()

        await browser.close()
        print("\nAll diagrams exported at 3x resolution!")

asyncio.run(main())
