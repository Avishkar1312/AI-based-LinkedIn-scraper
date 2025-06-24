# save_session.py
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.linkedin.com/login")
        print("🔓 Please log in manually...")
        await page.wait_for_timeout(60000)  # 60 sec to login
        await context.storage_state(path="linkedin_session.json")
        print("✅ Session saved!")

asyncio.run(main())
