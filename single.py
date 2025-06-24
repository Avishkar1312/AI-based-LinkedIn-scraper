# linkedin_single_profile_scraper.py
import asyncio
from playwright.async_api import async_playwright

async def scrape_profile(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="linkedin_session.json")
        page = await context.new_page()

        print(f"🔗 Visiting: {url}")
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state('networkidle')

        # 🧭 Scroll dynamically to bottom
        scroll_height = await page.evaluate("document.body.scrollHeight")
        for y in range(0, scroll_height, 300):
            await page.evaluate(f"window.scrollTo(0, {y})")
            await page.wait_for_timeout(800)
        await page.wait_for_timeout(2000)  # Wait for any lazy-loaded content

        try:
            name = await page.locator("h1.text-heading-xlarge").first.text_content() or ""
        except:
            name = ""
        try:
            about = await page.locator("section:has(h2:has-text('About')) div.break-words").first.text_content() or ""
        except:
            about = ""
        try:
            location = await page.locator("span.text-body-small.inline.t-black--light").first.text_content() or ""
        except:
            location = ""
        try:
            experience = await page.locator("section:has(h2:has-text('Experience')) ul").first.text_content() or ""
        except:
            experience = ""
        try:
            education = await page.locator("section:has(h2:has-text('Education')) ul").first.text_content() or ""
        except:
            education = ""
        try:
            skills = await page.locator("section:has(h2:has-text('Skills')) ul").first.text_content() or ""
        except:
            skills = ""

        print("\n📄 Scraped Data:")
        print(f"Name: {name.strip()}")
        print(f"About: {about.strip()}")
        print(f"Location: {location.strip()}")
        print(f"Experience: {experience.strip()}")
        print(f"Education: {education.strip()}")
        print(f"Skills: {skills.strip()}")

        await context.close()
        await browser.close()

# 🔁 Replace this with the profile you want to test
test_profile_url = "https://www.linkedin.com/in/naseem-ullah-a62966301"
asyncio.run(scrape_profile(test_profile_url))
