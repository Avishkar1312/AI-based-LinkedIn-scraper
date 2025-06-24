// popup.js
document.getElementById('scrape-btn').addEventListener('click', () => {
    const filename = document.getElementById('filename-input').value.trim();
    if (!filename) {
        alert("❗ Please enter a filename.");
        return;
    }

    const button = document.getElementById('scrape-btn');
    button.disabled = true;
    button.textContent = "Scraping...";

    // --- NEW: Retry mechanism for sending message ---
    const MAX_RETRIES = 3;
    let retries = 0;

    function sendMessageToBackground() {
        chrome.runtime.sendMessage({
            action: 'executeContentScript',
            filename: filename
        }, (response) => {
            // Check for chrome.runtime.lastError explicitly
            if (chrome.runtime.lastError) {
                console.error("Popup: chrome.runtime.lastError:", chrome.runtime.lastError.message);
                if (retries < MAX_RETRIES) {
                    retries++;
                    console.log(`Popup: Retrying message to background (<span class="math-inline">\{retries\}/</span>{MAX_RETRIES})...`);
                    setTimeout(sendMessageToBackground, 200); // Wait 200ms before retrying
                } else {
                    console.error("Popup: Max retries reached. No response from background script.");
                    alert("An unknown error occurred. Please try again.");
                    button.disabled = false;
                    button.textContent = "Scrape People Page";
                }
                return; // Exit this callback early
            }

            // Handle successful or explicit error response from background
            if (response && response.success) {
                console.log(response.message);
                button.textContent = "Scraping Complete!";
                setTimeout(() => {
                    window.close();
                }, 700);
            } else if (response) {
                console.error(response.message);
                alert(`Error: ${response.message}`);
                button.disabled = false;
                button.textContent = "Scrape People Page";
            } else {
                // Fallback for no response (should be caught by chrome.runtime.lastError now, but good to keep)
                console.error("Popup: No response from background script (unexpectedly).");
                alert("An unknown error occurred. Please try again.");
                button.disabled = false;
                button.textContent = "Scrape People Page";
            }
        });
    }

    sendMessageToBackground(); // Start sending the message
});