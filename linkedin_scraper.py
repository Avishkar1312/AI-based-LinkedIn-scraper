# playwright_scraper.py
import asyncio
import json
import os
import random
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

async def extract_profile_data(page, url):
    try:
        print(f"🔗 Visiting: {url}")
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state("networkidle")

        # Simulate scrolling to load lazy content
        for y in range(0, 4000, 500):
            await page.evaluate(f"window.scrollTo(0, {y})")
            await page.wait_for_timeout(random.randint(300, 600))

        # Name
        name = ""
        try:
            name = await page.locator("h1.text-heading-xlarge").first.text_content()
        except:
            print("⚠️ Name not found")

        # About
        about = ""
        try:
            about = await page.locator("section:has(h2:has-text('About')) div.break-words").first.text_content()
        except:
            print("⚠️ About section not found")

        # Location
        location = ""
        try:
            location = await page.locator("span.text-body-small.inline.t-black--light").first.text_content()
        except:
            print("⚠️ Location not found")

        # Experience
        experience = ""
        try:
            exp_section = page.locator("section:has(h2:has-text('Experience')) ul")
            experience = await exp_section.first.text_content() if await exp_section.count() else ""
        except:
            print("⚠️ Experience section not found")

        # Education
        education = ""
        try:
            edu_section = page.locator("section:has(h2:has-text('Education')) ul")
            education = await edu_section.first.text_content() if await edu_section.count() else ""
        except:
            print("⚠️ Education section not found")

        # Skills
        skills = ""
        try:
            skills_section = page.locator("section:has(h2:has-text('Skills')) ul")
            skills = await skills_section.first.text_content() if await skills_section.count() else ""
        except:
            print("⚠️ Skills section not found")

        return {
            "url": url,
            "name": name.strip() if name else "",
            "about": about.strip() if about else "",
            "location": location.strip() if location else "",
            "experience": experience.strip() if experience else "",
            "education": education.strip() if education else "",
            "skills": skills.strip() if skills else ""
        }

    except PlaywrightTimeout:
        print(f"❌ Timeout scraping {url}")
        return {
            "url": url,
            "name": "Timeout",
            "about": "",
            "location": "",
            "experience": "",
            "education": "",
            "skills": ""
        }

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return {
            "url": url,
            "name": "Error",
            "about": "",
            "location": "",
            "experience": "",
            "education": "",
            "skills": ""
        }



async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        if not os.path.exists("linkedin_session.json"):
            raise Exception("❌ Session not found! Run save_session.py first.")

        context = await browser.new_context(
            storage_state="linkedin_session.json",
            locale='en-US',
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )

        page = await context.new_page()
        await page.set_extra_http_headers({
            "accept-language": "en-US,en;q=0.9",
            "referer": "https://www.google.com/"
        })

        input_file = "server/HR Girlfriends.json"
        with open(input_file, "r") as f:
            data = json.load(f)
            profile_urls = data["urls"]

        results = []
        for idx, url in enumerate(profile_urls):
            print(f"🔍 Scraping profile {idx+1}/{len(profile_urls)}: {url}")
            result = await extract_profile_data(page, url)
            results.append(result)

        output_file = input_file.replace(".json", "_profiles.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"✅ Done! Saved scraped data to {output_file}")
        await context.close()
        await browser.close()


asyncio.run(main())
