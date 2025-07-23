// Function to update the extension's action properties (popup and title)
// based on the current tab's URL.
console.log("Service worker started/restarted.");
async function updateExtensionAction(tabId, url) {
    // Check if the URL is a LinkedIn Company People page
    const isLinkedInPeoplePage = url.includes("www.linkedin.com/company/") && url.includes("/people/");
    // Check if the URL is any LinkedIn page
    const isLinkedInPage = url.includes("www.linkedin.com/");

    if (isLinkedInPeoplePage) {
        // Case 1: On a LinkedIn Company People page
        // Set the popup to popup.html
        await chrome.action.setPopup({ tabId: tabId, popup: 'popup.html' });
        // Text shown when you hover over the page
        await chrome.action.setTitle({ tabId: tabId, title: 'Scrap data from this page' });
    } else if (isLinkedInPage) {
        // Case 2: On other LinkedIn pages (not a People page)
        // Set the popup to message.html
        await chrome.action.setPopup({ tabId: tabId, popup: 'message.html' });
        //Text shown when you hover over the page
        await chrome.action.setTitle({ tabId: tabId, title: 'Tribeca: Not on a Company People page' });
    } else {
        // Case 3: Not on LinkedIn at all
        // Set the popup to message.html
        await chrome.action.setPopup({ tabId: tabId, popup: 'message2.html' });
        // Text shown when you hover over the page
        await chrome.action.setTitle({ tabId: tabId, title: 'Tribeca: Not on LinkedIn' });
    }
}

// Listener: Fired when a tab is updated (e.g., URL changes, page finishes loading).
// This is crucial for reacting to navigation within the same tab.
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    // We only care about URL changes and when the page has finished loading (or at least its URL is stable).
    // `changeInfo.url` ensures we only act when the URL has actually changed.
    if (changeInfo.url) {
        await updateExtensionAction(tabId, changeInfo.url);
    }
});

// Listener: Fired when the active tab in the current window changes (user switches tabs).
// This ensures the extension's action updates when the user navigates between tabs.
chrome.tabs.onActivated.addListener(async (activeInfo) => {
    // Get the full tab information for the newly active tab.
    const tab = await chrome.tabs.get(activeInfo.tabId);
    if (tab.url) { // Ensure the tab object has a URL property
        await updateExtensionAction(activeInfo.tabId, tab.url);
    }
});

// Listener: Fired when the extension is first installed or updated.
// This ensures the extension's action is set correctly immediately after installation
// or when the browser starts and the extension becomes active.
chrome.runtime.onInstalled.addListener(() => {
    // Query for the currently active tab in the current window.
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
        if (tabs[0] && tabs[0].url) {
            await updateExtensionAction(tabs[0].id, tabs[0].url);
        }
    });
});

// Listener for messages from popup.js or content.js
// The popup will send a message here when the "Scrap Data" button is clicked.
// Listener for messages from popup.js or content.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // Check if the message is to execute the content script
    if (message.action === 'executeContentScript') {
        // Instead of directly using sender.tab.url, query for the active tab's URL
        // This makes the logic more robust to ensure we're targeting the *currently active* tab
        chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
            if (tabs[0] && tabs[0].url) {
                const currentTabId = tabs[0].id;
                const currentTabUrl = tabs[0].url;

                // Apply the URL validation logic using the queried tab URL
                // Use the more robust regex from our previous discussion or your current includes checks
                const isLinkedInPeoplePage = /^https:\/\/www\.linkedin\.com\/company\/[^/]+\/people\/?(?:[\?#].*)?$/.test(currentTabUrl);
                // OR your original simpler checks if you prefer:
                // const isLinkedInPeoplePage = currentTabUrl.includes("www.linkedin.com/company/") && currentTabUrl.includes("/people/");


                if (isLinkedInPeoplePage) {
                    try {
                        await chrome.scripting.executeScript({
                            target: { tabId: currentTabId }, // Use the queried tab ID
                            files: ['content.js'],
                            args: [message.filename]
                        });
                        sendResponse({ success: true, message: "Content script executed." });
                    } catch (error) {
                        sendResponse({ success: false, message: `Error executing content script: ${error.message}` });
                    }
                } else {
                    sendResponse({ success: false, message: "Content script cannot be executed on this page (URL mismatch)." });
                }
            } else {
                // Handle case where no active tab is found or URL is missing
                sendResponse({ success: false, message: "Could not determine current tab URL to execute script." });
            }
        });

        return true; // Important: Indicate that sendResponse will be called asynchronously
    }
});