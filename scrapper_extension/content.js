(async function () {                                           //runs as soon as the script is injected into the html
    console.log("🔄 Starting scroll and scrape...");

    const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms)); //delay function

    const scrollAndLoad = async () => {
        let lastHeight = 0;                              //keeps track of the page height so that we could cehck at the last if there is a change in height
        let retries = 10;                                //no of retries to be given to check for the show more button

        while (retries > 0) {
            window.scrollTo(0, document.body.scrollHeight);            //scroll to the bottom of the page
            await delay(2000);                                        //wait for it to load

            const newHeight = document.body.scrollHeight;            //update the new height of the page

            // CLICK LOGIC for "Show more results"  ...finds the show more Button
            const showMoreBtn = [...document.querySelectorAll("button")].find(btn => {
                const text = btn.innerText || btn.textContent || "";
                return text.trim().toLowerCase().includes("show more results");
            });

            //console.log("All buttons found on this scroll:", [...document.querySelectorAll("button")]);

            if (showMoreBtn) {
                console.log("✅ Found 'Show more results' button");

                showMoreBtn.scrollIntoView({ behavior: "smooth", block: "center" });
                await delay(1000);

                try {
                    showMoreBtn.click();                                   //clicks the show more button so taht new content loads
                    console.log("🖱️ Clicked 'Show more results'");
                } catch (err) {
                    console.warn("⚠️ Error clicking button:", err);
                }

                await delay(3000); // Wait for content to load
            } else {
                console.log("❌ 'Show more results' button NOT found on this scroll.");
            }

            if (newHeight === lastHeight) {                          //there is no new content if the height of the oage doesn't change
                retries--;
            } else {
                retries = 10; 
                lastHeight = newHeight;                             //if the height changes then new content has loaded
            }
        }
    };

    await scrollAndLoad();                                   //calls the scroll and load function

    const anchors = [...document.querySelectorAll("a[href*='/in/']")];          //extarcts all the urls having /in/ from the page
    const profileUrls = [...new Set(anchors.map(a => a.href.split("?")[0]))];   //extracts only the imp part of the url

    console.log("✅ Final profile count:", profileUrls.length);               //displays the total number of profiles extracted

    const filename = window.filenameForScrape || "profile_urls";              //scaros out the filename given into the extension

    await fetch("http://localhost:5000/save_urls", {                         //the data is sent to the local system 
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ urls: profileUrls, filename: filename })
    });

    alert(`✅ ${profileUrls.length} profile URLs saved to ${filename}.json!`);
})();
