/**
 * Betika.com Soccer Odds Scraper - Apify Actor
 * Designed for Kenya market soccer odds extraction and analysis
 */

const Apify = require('apify');
const puppeteer = require('puppeteer');

Apify.main(async () => {
    // Configuration
    const input = await Apify.getInput();
    const {
        startUrls = [
            'https://www.betika.com/en-ke/sport/football',
            'https://www.betika.com/en-ke/sport/1'
        ],
        proxyConfiguration,
        maxConcurrency = 1, // Respect rate limits
        waitTime = 3000
    } = input;

    // Initialize request queue
    const requestQueue = await Apify.openRequestQueue();
    
    // Add start URLs to queue
    for (const url of startUrls) {
        await requestQueue.addRequest({ url });
    }

    // Initialize dataset for results
    const dataset = await Apify.openDataset();

    // Network request interceptor to capture API calls
    const interceptedRequests = [];

    // Create crawler
    const crawler = new Apify.PuppeteerCrawler({
        requestQueue,
        proxyConfiguration,
        maxConcurrency,
        launchOptions: {
            headless: false, // For debugging Cloudflare bypass
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--single-process',
                '--disable-gpu',
                '--window-size=1920,1080'
            ]
        },

        handlePageFunction: async ({ page, request }) => {
            console.log(`Processing: ${request.url}`);

            // Enable request interception
            await page.setRequestInterception(true);
            
            page.on('request', (interceptedRequest) => {
                const url = interceptedRequest.url();
                const method = interceptedRequest.method();
                const headers = interceptedRequest.headers();
                
                // Capture API calls
                if (url.includes('api') || url.includes('ajax') || 
                    url.includes('odds') || url.includes('ws://') || url.includes('wss://')) {
                    interceptedRequests.push({
                        url,
                        method,
                        headers,
                        postData: interceptedRequest.postData(),
                        timestamp: new Date().toISOString()
                    });
                    console.log(`🔍 API Call captured: ${method} ${url}`);
                }
                
                interceptedRequest.continue();
            });

            // Monitor network responses
            page.on('response', async (response) => {
                const url = response.url();
                if (url.includes('api') || url.includes('odds') || 
                    url.includes('ajax') || response.headers()['content-type']?.includes('json')) {
                    
                    try {
                        const responseBody = await response.text();
                        console.log(`📡 API Response captured from: ${url}`);
                        
                        // Store API response data
                        await dataset.pushData({
                            type: 'api_response',
                            url,
                            status: response.status(),
                            headers: response.headers(),
                            body: responseBody.substring(0, 10000), // Limit body size
                            timestamp: new Date().toISOString()
                        });
                    } catch (error) {
                        console.log(`Error capturing response from ${url}: ${error.message}`);
                    }
                }
            });

            // Wait for page to load completely
            await page.waitForTimeout(waitTime);

            // Extract soccer odds data
            const oddsData = await page.evaluate(() => {
                const odds = [];
                
                // Generic selectors that might work across different layouts
                const selectors = [
                    '[class*="odds"]',
                    '[class*="match"]',
                    '[class*="game"]',
                    '[data-odds]',
                    '[data-match-id]',
                    '.bet-item',
                    '.match-item',
                    '.odds-item'
                ];

                // Try different selector strategies
                selectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach((el, index) => {
                        if (index < 50) { // Limit to prevent overwhelming data
                            odds.push({
                                selector: selector,
                                innerHTML: el.innerHTML.substring(0, 500),
                                textContent: el.textContent,
                                className: el.className,
                                id: el.id,
                                dataset: {...el.dataset}
                            });
                        }
                    });
                });

                // Look for JSON data in script tags
                const scriptTags = document.querySelectorAll('script');
                const jsonData = [];
                scriptTags.forEach(script => {
                    const content = script.textContent || script.innerText;
                    if (content.includes('odds') || content.includes('match') || content.includes('api')) {
                        jsonData.push({
                            content: content.substring(0, 1000),
                            src: script.src
                        });
                    }
                });

                return {
                    odds: odds,
                    scriptData: jsonData,
                    url: window.location.href,
                    timestamp: new Date().toISOString()
                };
            });

            // Save extracted data
            await dataset.pushData({
                type: 'scraped_data',
                url: request.url,
                oddsData: oddsData,
                interceptedRequests: interceptedRequests,
                timestamp: new Date().toISOString()
            });

            // Look for additional URLs to crawl
            const newUrls = await page.evaluate(() => {
                const links = [];
                const anchors = document.querySelectorAll('a[href*="sport"], a[href*="football"], a[href*="match"]');
                anchors.forEach(anchor => {
                    const href = anchor.href;
                    if (href && href.includes('betika.com')) {
                        links.push(href);
                    }
                });
                return [...new Set(links)]; // Remove duplicates
            });

            // Add new URLs to queue (limited to prevent infinite crawling)
            for (let i = 0; i < Math.min(newUrls.length, 10); i++) {
                await requestQueue.addRequest({ url: newUrls[i] });
            }
        },

        failedRequestHandler: async ({ request, error }) => {
            console.log(`Request ${request.url} failed: ${error.message}`);
            await dataset.pushData({
                type: 'error',
                url: request.url,
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    });

    // Start crawling
    await crawler.run();
    
    console.log('🎉 Scraping completed! Check the dataset for results.');
});

/**
 * Usage Instructions:
 * 
 * 1. Create new Apify Actor
 * 2. Copy this code to the Actor's main.js
 * 3. Add dependencies: apify, puppeteer
 * 4. Configure input JSON:
 *    {
 *      "startUrls": ["https://www.betika.com/en-ke/sport/football"],
 *      "proxyConfiguration": {"useApifyProxy": true, "apifyProxyGroups": ["RESIDENTIAL"]},
 *      "maxConcurrency": 1,
 *      "waitTime": 5000
 *    }
 * 5. Run the Actor
 * 6. Export results as JSON for analysis
 */