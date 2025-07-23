document.addEventListener('DOMContentLoaded', function () {
    // Existing scrape people page button logic
    // Assuming 'scrape-btn' is the ID for your "scrape-button" as per your latest popup.js
    const scrapeButton = document.getElementById('scrape-btn');
    if (scrapeButton) {
        scrapeButton.addEventListener('click', function () {
            const filenameInput = document.getElementById('filename-input');
            const filename = filenameInput ? filenameInput.value : 'profile_urls';

            // Use chrome.scripting.executeScript with 'func' to call scrapePeoplePage
            chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
                chrome.scripting.executeScript({
                    target: { tabId: tabs[0].id },
                    func: (targetFilename) => { // This function runs in the content script's isolated world
                        // Call the scrapePeoplePage function defined in content.js
                        if (typeof window.scrapePeoplePage === 'function') {
                            window.scrapePeoplePage(targetFilename);
                        } else {
                            console.error("scrapePeoplePage function not found in content script. Ensure content.js is loaded correctly.");
                        }
                    },
                    args: [filename] // Pass the filename as an argument to scrapePeoplePage
                }, () => {
                    // This callback runs after the script injection attempts
                    if (chrome.runtime.lastError) {
                        console.error('Script injection failed:', chrome.runtime.lastError.message);
                    }
                });
            });
            window.close(); // Close the popup
        });
    }

    // --- NEW LOGIC FOR EXTRACT CURRENT PROFILE DETAILS BUTTON ---
    const extractProfileButton = document.getElementById('extract-profile-btn');
    if (extractProfileButton) {
        extractProfileButton.addEventListener('click', function () {
            // Use chrome.scripting.executeScript with 'func' to call extractProfileDetails
            chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
                chrome.scripting.executeScript({
                    target: { tabId: tabs[0].id },
                    func: () => { // This function runs in the content script's isolated world
                        // Call the extractProfileDetails function defined in content.js
                        if (typeof window.extractProfileDetails === 'function') {
                            window.extractProfileDetails();
                        } else {
                            console.error("extractProfileDetails function not found in content script. Ensure content.js is loaded correctly.");
                        }
                    }
                }, () => {
                    // This callback runs after the script injection attempts
                    if (chrome.runtime.lastError) {
                        console.error('Script injection failed:', chrome.runtime.lastError.message);
                    }
                });
            });
            window.close(); // Close the popup
        });
    }
});