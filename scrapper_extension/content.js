// content.js - MODIFIED
// content.js
console.log("DEBUG: content.js has loaded!"); // Add this line at the very top

// ... rest of your content.js code (delay, scrapePeoplePage, extractProfileDetails, window assignments)
// Helper for delays
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Scrapes LinkedIn company "People" page for profile URLs.
 * This is the existing functionality, now wrapped in a function.
 * @param {string} filename The filename to use for saving data on the server.
 */
async function scrapePeoplePage(filename) {
    console.log("🔄 Starting scroll and scrape for People page...");

    const scrollAndLoad = async () => {
        let lastHeight = 0;
        let retries = 10; // Number of times to retry if scroll height doesn't change

        while (retries > 0) {
            window.scrollTo(0, document.body.scrollHeight);
            await delay(2000); // Wait for page to render new content

            const newHeight = document.body.scrollHeight;

            const seeMoreBtn = [...document.querySelectorAll("button")].find(btn => {
                const text = btn.innerText || btn.textContent || "";
                return text.trim().toLowerCase().includes("show more results");
            });

            if (seeMoreBtn) {
                console.log("✅ Found 'Show more results' button");
                seeMoreBtn.scrollIntoView({ behavior: "smooth", block: "center" });
                await delay(1000); // Give time for scroll
                try {
                    seeMoreBtn.click();
                    console.log("🖱️ Clicked 'Show more results'");
                } catch (err) {
                    console.warn("⚠️ Error clicking button:", err);
                }
                await delay(3000); // Wait for content to load after click
                retries = 10; // Reset retries after a successful click
            } else {
                console.log("❌ 'Show more results' button NOT found on this scroll.");
            }

            if (newHeight === lastHeight) {
                retries--;
                console.log(`Still same height. Retries left: ${retries}`);
            } else {
                retries = 10; // Reset retries if new content loaded
                lastHeight = newHeight;
                console.log(`New height: ${newHeight}`);
            }
        }
    };

    await scrollAndLoad();

    const anchors = [...document.querySelectorAll("a[href*='/in/']")];
    const profileUrls = [...new Set(anchors.map(a => a.href.split("?")[0]))];

    console.log("✅ Final profile count:", profileUrls.length);

    // Send the data to your Flask backend
    try {
        const response = await fetch("http://localhost:5000/save_urls", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ urls: profileUrls, filename: filename })
        });
        const data = await response.json();
        if (response.ok) { // Check if response status is 2xx
            console.log("✅ Profile URLs successfully sent to server:", data.message);
            alert(`✅ ${profileUrls.length} profile URLs saved to ${filename}.json!`);
        } else {
            console.error("❌ Error sending profile URLs to server (Status: " + response.status + "):", data.message);
            alert(`❌ Error saving profile URLs: ${data.message}`);
        }
    } catch (error) {
        console.error("❌ Fetch error when sending profile URLs:", error);
        alert(`❌ Network error saving profile URLs: ${error.message}`);
    }

    console.log("🏁 People page scrape process finished.");
}


/**
 * Extracts experience details from the current LinkedIn profile page.
 * This is the new functionality.
 */
// content.js - MODIFIED extractProfileDetails function

async function extractProfileDetails() {
    console.log("Starting profile experience extraction...");

    const experiences = [];

    // --- START OF ADDED/MODIFIED CODE FOR PROFILE URL AND NAME ---
    const profileUrl = window.location.href.split('?')[0]; // Get current URL, remove query parameters
    let profileName = "Unknown Profile";

    // Attempt to get the profile name from a common LinkedIn element
    // This often corresponds to the H1 tag at the top of the profile
    const profileNameElement = document.querySelector('h1.inline.t-24.v-align-middle.break-words');
    if (profileNameElement) {
        profileName = profileNameElement.textContent.trim();
    } else {
        // Fallback: Try to get the name from the document title
        // e.g., "John Doe | LinkedIn" -> "John Doe"
        const titleMatch = document.title.match(/^(.*?) \| LinkedIn$/);
        if (titleMatch && titleMatch[1]) {
            profileName = titleMatch[1].trim();
        }
    }
    console.log(`Extracting experiences for: ${profileName} (${profileUrl})`);
    // --- END OF ADDED/MODIFIED CODE FOR PROFILE URL AND NAME ---


    // Find the main experience section using its unique ID anchor and then its closest parent section
    const experienceAnchor = document.getElementById("experience");
    const experienceSection = experienceAnchor ? experienceAnchor.closest("section") : null;

    if (experienceSection) {
        // Select each individual experience item.
        // These are typically divs with data-view-name='profile-component-entity' inside list items.
        const experienceItems = experienceSection.querySelectorAll("li.artdeco-list__item > div[data-view-name='profile-component-entity']");

        experienceItems.forEach(item => {
            // Extract Job Title
            const jobTitleElement = item.querySelector("div.t-bold span[aria-hidden='true']");
            const jobTitle = jobTitleElement ? jobTitleElement.textContent.trim() : "";

            // Extract Company and Employment Type
            const companyAndTypeElement = item.querySelector("span.t-14.t-normal span[aria-hidden='true']");
            let company = "";
            let employmentType = "";
            if (companyAndTypeElement) {
                const companyText = companyAndTypeElement.textContent.trim();
                const parts = companyText.split("·").map(s => s.trim());
                company = parts[0] || "";
                employmentType = parts[1] || "";
            }

            // Extract Duration
            const durationElement = item.querySelector("span.t-14.t-normal.t-black--light span[aria-hidden='true']");
            const duration = durationElement ? durationElement.textContent.trim() : "";

            experiences.push({ jobTitle, company, duration });
        });

        // Check for "Show all experiences" button
        const showAllExperiencesButton = document.getElementById("navigation-index-see-all-experiences");
        if (showAllExperiencesButton) {
            console.log("Found 'Show all experiences' button. If more experiences exist, you might need to click this and re-run the script.");
            // OPTIONAL: If you want to automatically click this and re-extract, uncomment below:
            // showAllExperiencesButton.click();
            // await delay(2000); // Wait for content to load after click
            // // You might need to call extractProfileDetails() again here to get newly loaded items
        } else {
            console.log("'Show all experiences' button not found or already clicked/no more experiences to show.");
        }

    } else {
        console.warn("Experience section not found on the page using anchor ID 'experience'. Please ensure you are on a LinkedIn profile page and the structure matches.");
    }

    console.log("Extracted Experiences:", experiences);

    if (experiences.length === 0 && experienceSection) {
        console.warn("No experiences extracted from the found section. This might happen if the HTML structure within the section has changed, or if there's a 'Show all experiences' button that needs clicking to reveal content.");
    }

    // --- START OF MODIFIED CODE FOR FETCH REQUEST BODY ---
    // Send the extracted experiences, profile URL, and profile Name to your Flask backend
    try {
        const response = await fetch("http://localhost:5000/save_experience_details", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ // <-- NOW SENDING PROFILE URL AND NAME
                profileUrl: profileUrl,
                profileName: profileName,
                experiences: experiences
            })
        });
        const data = await response.json();
        if (response.ok) { // Check if response status is 2xx
            console.log("✅ Experience details successfully sent to server:", data.message);
            alert(`✅ ${experiences.length} experiences for ${profileName} saved!`); // Updated alert message
        } else {
            console.error("❌ Error sending experience details to server (Status: " + response.status + "):", data.message);
            alert(`❌ Error saving experiences: ${data.message}`);
        }
    } catch (error) {
        console.error("❌ Fetch error when sending experience details:", error);
        alert(`❌ Network error saving experiences: ${error.message}`);
    }
    // --- END OF MODIFIED CODE FOR FETCH REQUEST BODY ---

    console.log("🏁 Profile experience extraction finished.");
}

// Ensure these functions are accessible from popup.js when executed via chrome.scripting.executeScript
// These functions will be called directly by popup.js
window.scrapePeoplePage = scrapePeoplePage;
window.extractProfileDetails = extractProfileDetails;