/**
 * Betika.com Soccer Odds Scraper - Standalone Version
 * Real-time data extraction for Betika.com
 */

const puppeteer = require('puppeteer');
const fs = require('fs');

class BetikaScraper {
    constructor() {
        this.browser = null;
        this.page = null;
        this.data = [];
        this.apiEndpoints = [];
    }

    async init() {
        console.log('🚀 Initializing Betika scraper...');
        
        this.browser = await puppeteer.launch({
            headless: false, // Set to true for production
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
        });

        this.page = await this.browser.newPage();
        
        // Set user agent
        await this.page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        
        // Enable request interception
        await this.page.setRequestInterception(true);
        
        // Monitor network requests
        this.page.on('request', (request) => {
            const url = request.url();
            if (url.includes('api') || url.includes('ajax') || url.includes('odds')) {
                this.apiEndpoints.push({
                    url: url,
                    method: request.method(),
                    headers: request.headers(),
                    timestamp: new Date().toISOString()
                });
                console.log(`🔍 API Call: ${request.method()} ${url}`);
            }
            request.continue();
        });

        // Monitor network responses
        this.page.on('response', async (response) => {
            const url = response.url();
            if (url.includes('api') || url.includes('odds') || url.includes('ajax')) {
                try {
                    const content = await response.text();
                    if (content && content.length > 0) {
                        console.log(`📡 API Response: ${url} (${response.status()})`);
                        
                        // Try to parse as JSON
                        try {
                            const jsonData = JSON.parse(content);
                            this.data.push({
                                type: 'api_response',
                                url: url,
                                status: response.status(),
                                data: jsonData,
                                timestamp: new Date().toISOString()
                            });
                        } catch (e) {
                            // Not JSON, store as text
                            this.data.push({
                                type: 'api_response',
                                url: url,
                                status: response.status(),
                                data: content.substring(0, 1000),
                                timestamp: new Date().toISOString()
                            });
                        }
                    }
                } catch (error) {
                    console.log(`Error processing response from ${url}: ${error.message}`);
                }
            }
        });
    }

    async scrapeBetika() {
        console.log('📊 Starting Betika data extraction...');
        
        try {
            // Navigate to Betika football page
            await this.page.goto('https://www.betika.com/en-ke/sport/football', {
                waitUntil: 'networkidle2',
                timeout: 30000
            });

            // Wait for page to load
            await this.page.waitForTimeout(5000);

            // Extract odds data from page
            const oddsData = await this.page.evaluate(() => {
                const odds = [];
                
                // Look for common betting elements
                const selectors = [
                    '[class*="odds"]',
                    '[class*="match"]',
                    '[class*="game"]',
                    '[data-odds]',
                    '[data-match-id]',
                    '.bet-item',
                    '.match-item',
                    '.odds-item',
                    '.event-item',
                    '.fixture-item'
                ];

                selectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach((el, index) => {
                        if (index < 20) { // Limit to prevent overwhelming data
                            odds.push({
                                selector: selector,
                                textContent: el.textContent?.trim(),
                                className: el.className,
                                id: el.id,
                                dataset: {...el.dataset},
                                innerHTML: el.innerHTML.substring(0, 200)
                            });
                        }
                    });
                });

                // Look for JSON data in script tags
                const scriptTags = document.querySelectorAll('script');
                const jsonData = [];
                scriptTags.forEach(script => {
                    const content = script.textContent || script.innerText;
                    if (content && (content.includes('odds') || content.includes('match') || content.includes('api'))) {
                        jsonData.push({
                            content: content.substring(0, 500),
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

            // Store extracted data
            this.data.push({
                type: 'scraped_data',
                url: 'https://www.betika.com/en-ke/sport/football',
                oddsData: oddsData,
                timestamp: new Date().toISOString()
            });

            console.log(`✅ Extracted ${oddsData.odds.length} odds elements`);
            console.log(`📊 Found ${oddsData.scriptData.length} script tags with potential data`);

        } catch (error) {
            console.error(`❌ Error scraping Betika: ${error.message}`);
        }
    }

    async saveResults() {
        console.log('💾 Saving results...');
        
        const results = {
            timestamp: new Date().toISOString(),
            summary: {
                totalDataPoints: this.data.length,
                apiEndpoints: this.apiEndpoints.length,
                scrapedElements: this.data.filter(d => d.type === 'scraped_data').length
            },
            data: this.data,
            apiEndpoints: this.apiEndpoints
        };

        // Save to JSON file
        fs.writeFileSync('betika-scraper-results.json', JSON.stringify(results, null, 2));
        
        // Save API endpoints separately
        fs.writeFileSync('betika-api-endpoints.json', JSON.stringify(this.apiEndpoints, null, 2));
        
        console.log('✅ Results saved to betika-scraper-results.json');
        console.log('✅ API endpoints saved to betika-api-endpoints.json');
    }

    async close() {
        if (this.browser) {
            await this.browser.close();
        }
    }
}

async function main() {
    const scraper = new BetikaScraper();
    
    try {
        await scraper.init();
        await scraper.scrapeBetika();
        await scraper.saveResults();
        
        console.log('\n🎉 Scraping completed successfully!');
        console.log('📁 Check the generated JSON files for results.');
        
    } catch (error) {
        console.error(`❌ Scraping failed: ${error.message}`);
    } finally {
        await scraper.close();
    }
}

// Run the scraper
if (require.main === module) {
    main().catch(console.error);
}

module.exports = BetikaScraper;
