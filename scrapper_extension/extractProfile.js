// extractProfile.js

(async function () {
    console.log("➡️ Starting single profile extraction...");

    const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

    let profile = {
        name: null,
        about: null,
        location: null,
        experience: [],
        education: [],
        skills: []
    };

    // --- Helper to get text content safely ---
    const getText = (selector) => {
        const el = document.querySelector(selector);
        return el ? el.textContent.trim() : null;
    };

    // --- Helper to click "Show more" buttons ---
    const clickShowMore = async (selector, maxAttempts = 3) => {
        let attempts = 0;
        while (attempts < maxAttempts) {
            const button = document.querySelector(selector);
            if (button && button.offsetParent !== null) { // Check if visible
                try {
                    button.scrollIntoView({ behavior: "smooth", block: "center" });
                    await delay(500); // Allow scroll to complete
                    button.click();
                    await delay(1000); // Wait for content to load
                    return true;
                } catch (e) {
                    console.warn(`Click failed for ${selector}:`, e);
                }
            }
            attempts++;
            await delay(500); // Wait before next attempt
        }
        return false;
    };

    // --- General scroll function for dynamic content ---
    const scrollAndLoad = async () => {
        let lastHeight = 0;
        let retries = 5; // Reduced retries for single profile, can adjust
        while (retries > 0) {
            window.scrollTo(0, document.body.scrollHeight);
            await delay(1500);
            const newHeight = document.body.scrollHeight;
            if (newHeight === lastHeight) {
                retries--;
            } else {
                retries = 5;
                lastHeight = newHeight;
            }
        }
    };

    // --- Extract Name ---
    profile.name = getText("h1.top-card-layout__title");
    if (!profile.name) { // Fallback for some profile types
        profile.name = getText("h1[data-test-id='profile-content__title']");
    }
    console.log("Name:", profile.name);

    // --- Extract Location ---
    profile.location = getText("div.top-card-layout__entity-info-container span.top-card-layout__locality");
    if (!profile.location) { // Fallback
        profile.location = getText("div[data-test-id='profile-content__primary-info'] span.top-card__location");
    }
    console.log("Location:", profile.location);

    // --- Extract About ---
    await clickShowMore("button[aria-label^='Expand About']"); // Try to expand
    profile.about = getText("div.pv-about-section div[data-test-id='about-section-content'] span.visually-hidden");
    if (!profile.about) { // Fallback
        profile.about = getText("section.summary-card__content div.core-section-container__content");
    }
    console.log("About:", profile.about);

    // --- Scroll to load Experience/Education/Skills (dynamic sections) ---
    await scrollAndLoad();
    await delay(1000); // Give a moment for new content to render

    // --- Extract Experience ---
    const experienceSection = document.querySelector("section.experience-section");
    if (experienceSection) {
        // You might need to click "Show all positions" or "Show all companies" if these exist.
        await clickShowMore("button[aria-label^='Show all positions']");
        await clickShowMore("button[aria-label^='Show all companies']");

        const experienceItems = experienceSection.querySelectorAll(".pvs-list__item");
        experienceItems.forEach(item => {
            const title = getTextFromElement(item, "div.pvs-entity__content-wrapper div.t-bold");
            let companyRaw = getTextFromElement(item, "div.pvs-entity__content-wrapper span.t-normal");
            const duration = getTextFromElement(item, "div.pvs-entity__content-wrapper span.t-normal:nth-of-type(2)");

            // Clean up company string (e.g., remove "Full-time", "Part-time")
            const company = companyRaw ? companyRaw.replace(/\s*\b(Full-time|Part-time|Contract|Self-employed|Freelance|Internship)\b.*$/i, '').trim() : null;

            if (title) { // Only add if a title is found
                profile.experience.push({ title, company, duration });
            }
        });
    }
    console.log("Experience:", profile.experience);

    // --- Extract Education ---
    const educationSection = document.querySelector("section.education-section");
    if (educationSection) {
        await clickShowMore("button[aria-label^='Show all education']");
        const educationItems = educationSection.querySelectorAll(".pvs-list__item");
        educationItems.forEach(item => {
            const school = getTextFromElement(item, "div.pvs-entity__content-wrapper div.t-bold");
            const degree = getTextFromElement(item, "div.pvs-entity__content-wrapper span.t-normal");
            const field = getTextFromElement(item, "div.pvs-entity__content-wrapper span.t-normal:nth-of-type(2)");
            if (school) { // Only add if a school is found
                profile.education.push({ school, degree, field });
            }
        });
    }
    console.log("Education:", profile.education);

    // --- Extract Skills ---
    await clickShowMore("button[aria-label^='Show all skills']");
    // Wait for the modal or expanded skills to appear
    await delay(1000); // Give a moment for new content to render
    let skills = [];
    // Try selecting skills from the main section or the modal
    const skillElements = document.querySelectorAll(".pv-skill-category-list__item span.t-bold");
    skillElements.forEach(el => {
        const skillName = el.textContent.trim();
        if (skillName && !skills.includes(skillName)) {
            skills.push(skillName);
        }
    });
    profile.skills = skills;
    console.log("Skills:", profile.skills);

    // --- Helper to get text from within an element's scope ---
    function getTextFromElement(parent, selector) {
        const el = parent.querySelector(selector);
        return el ? el.textContent.trim() : null;
    }


    // --- Send extracted data back to popup.js ---
    try {
        const response = await chrome.runtime.sendMessage({
            action: 'profileDataExtracted',
            data: profile
        });
        console.log("Response from popup:", response);
    } catch (error) {
        console.error("Error sending message to popup:", error);
    }
})();