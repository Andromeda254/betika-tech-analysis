/**
 * Betika.com Network Analysis & API Discovery Script
 * Advanced browser automation for identifying external odds sources and APIs
 */

const puppeteer = require('puppeteer');
const fs = require('fs').promises;

class BetikaAPIAnalyzer {
    constructor() {
        this.apiCalls = [];
        this.websocketConnections = [];
        this.externalSources = [];
        this.oddsData = [];
        this.networkRequests = [];
    }

    /**
     * Main analysis function
     */
    async analyzeBetikaAPIs() {
        console.log('🚀 Starting Betika API analysis...');
        
        const browser = await puppeteer.launch({
            headless: false, // Set to true for production
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--window-size=1920,1080',
                '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        });

        const page = await browser.newPage();
        
        // Enhanced network interception
        await this.setupNetworkInterception(page);
        
        try {
            // Navigate to Betika and analyze
            await this.analyzeMainPage(page);
            await this.analyzeSportsPages(page);
            await this.analyzeAPIEndpoints(page);
            
            // Generate comprehensive report
            const report = await this.generateAnalysisReport();
            
            // Save results
            await this.saveResults(report);
            
            console.log('✅ Analysis completed successfully!');
            
        } catch (error) {
            console.error('❌ Analysis failed:', error);
        } finally {
            await browser.close();
        }
    }

    /**
     * Setup comprehensive network interception
     */
    async setupNetworkInterception(page) {
        // Enable request interception
        await page.setRequestInterception(true);
        
        page.on('request', (request) => {
            const url = request.url();
            const method = request.method();
            const headers = request.headers();
            const postData = request.postData();
            
            // Log all requests
            this.networkRequests.push({
                url,
                method,
                headers,
                postData,
                timestamp: new Date().toISOString(),
                type: this.categorizeRequest(url)
            });
            
            // Identify API calls
            if (this.isAPICall(url)) {
                this.apiCalls.push({
                    url,
                    method,
                    headers,
                    postData,
                    timestamp: new Date().toISOString()
                });
                console.log(`🔍 API Call: ${method} ${url}`);
            }
            
            // Identify external sources
            if (this.isExternalSource(url)) {
                this.externalSources.push({
                    url,
                    provider: this.identifyProvider(url),
                    timestamp: new Date().toISOString()
                });
                console.log(`🌐 External Source: ${url}`);
            }
            
            request.continue();
        });

        // Monitor responses
        page.on('response', async (response) => {
            const url = response.url();
            
            if (this.isAPICall(url) || this.isJSONResponse(response)) {
                try {
                    const responseBody = await response.text();
                    
                    // Parse and store JSON responses
                    if (this.isJSONContent(responseBody)) {
                        const jsonData = JSON.parse(responseBody);
                        
                        if (this.containsOddsData(jsonData)) {
                            this.oddsData.push({
                                url,
                                data: jsonData,
                                timestamp: new Date().toISOString()
                            });
                            console.log(`📊 Odds Data Found: ${url}`);
                        }
                    }
                } catch (error) {
                    console.log(`Warning: Failed to parse response from ${url}`);
                }
            }
        });

        // Monitor WebSocket connections
        const client = await page.target().createCDPSession();
        await client.send('Runtime.enable');
        
        client.on('Runtime.bindingCalled', (event) => {
            if (event.name === 'websocket') {
                this.websocketConnections.push({
                    url: event.payload,
                    timestamp: new Date().toISOString()
                });
                console.log(`🔄 WebSocket Connection: ${event.payload}`);
            }
        });
    }

    /**
     * Analyze main Betika page
     */
    async analyzeMainPage(page) {
        console.log('📄 Analyzing main page...');
        
        await page.goto('https://www.betika.com/en-ke/', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });
        
        await page.waitForTimeout(5000);
        
        // Extract embedded scripts and configuration
        const pageData = await page.evaluate(() => {
            const scripts = Array.from(document.querySelectorAll('script'));
            const configData = [];
            
            scripts.forEach(script => {
                const content = script.textContent || script.innerHTML;
                if (content && (
                    content.includes('api') || 
                    content.includes('endpoint') || 
                    content.includes('config') ||
                    content.includes('odds') ||
                    content.includes('ws://') ||
                    content.includes('wss://')
                )) {
                    configData.push({
                        src: script.src || 'inline',
                        content: content.substring(0, 2000) // Limit content size
                    });
                }
            });
            
            return {
                url: window.location.href,
                title: document.title,
                configData: configData,
                metaData: Array.from(document.querySelectorAll('meta')).map(meta => ({
                    name: meta.name,
                    property: meta.property,
                    content: meta.content
                }))
            };
        });
        
        console.log(`📋 Found ${pageData.configData.length} potentially relevant scripts`);
    }

    /**
     * Analyze sports-specific pages
     */
    async analyzeSportsPages(page) {
        const sportsUrls = [
            'https://www.betika.com/en-ke/sport/football',
            'https://www.betika.com/en-ke/sport/1', // Football ID
            'https://www.betika.com/en-ke/live-betting'
        ];
        
        for (const url of sportsUrls) {
            console.log(`⚽ Analyzing sports page: ${url}`);
            
            try {
                await page.goto(url, {
                    waitUntil: 'networkidle2',
                    timeout: 30000
                });
                
                await page.waitForTimeout(5000);
                
                // Look for odds data in the DOM
                const sportsData = await page.evaluate(() => {
                    // Common selectors for betting odds
                    const selectors = [
                        '[class*="odd"]',
                        '[class*="bet"]',
                        '[class*="match"]',
                        '[data-odd]',
                        '[data-match-id]',
                        '.odds-container',
                        '.match-odds',
                        '.betting-odds'
                    ];
                    
                    const extractedData = [];
                    
                    selectors.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach((el, index) => {
                            if (index < 20) { // Limit extraction
                                extractedData.push({
                                    selector,
                                    text: el.textContent?.trim().substring(0, 200),
                                    className: el.className,
                                    dataset: {...el.dataset},
                                    innerHTML: el.innerHTML.substring(0, 500)
                                });
                            }
                        });
                    });
                    
                    return extractedData;
                });
                
                console.log(`📈 Extracted ${sportsData.length} odds-related elements`);
                
            } catch (error) {
                console.log(`⚠️  Failed to analyze ${url}: ${error.message}`);
            }
        }
    }

    /**
     * Test common API endpoints
     */
    async analyzeAPIEndpoints(page) {
        const potentialEndpoints = [
            '/api/odds/football',
            '/api/matches/live',
            '/ajax/odds/update',
            '/api/sports/1', // Football
            '/ws/odds',
            '/api/v1/odds',
            '/api/v2/sports/football'
        ];
        
        console.log('🔍 Testing potential API endpoints...');
        
        for (const endpoint of potentialEndpoints) {
            try {
                const fullUrl = `https://www.betika.com${endpoint}`;
                
                await page.evaluate((url) => {
                    // Test endpoint with fetch
                    fetch(url, {
                        method: 'GET',
                        headers: {
                            'Accept': 'application/json',
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    }).catch(() => {}); // Ignore errors, we're just triggering network activity
                }, fullUrl);
                
                await page.waitForTimeout(1000);
                
            } catch (error) {
                // Expected - just testing endpoints
            }
        }
    }

    /**
     * Helper functions
     */
    categorizeRequest(url) {
        if (url.includes('/api/')) return 'api';
        if (url.includes('/ajax/')) return 'ajax';
        if (url.includes('ws://') || url.includes('wss://')) return 'websocket';
        if (this.isExternalSource(url)) return 'external';
        if (url.includes('.js')) return 'javascript';
        if (url.includes('.css')) return 'css';
        return 'other';
    }

    isAPICall(url) {
        return url.includes('/api/') || 
               url.includes('/ajax/') || 
               url.includes('odds') ||
               url.includes('json') ||
               (url.includes('betika.com') && url.includes('sport'));
    }

    isExternalSource(url) {
        const externalProviders = [
            'sportradar.com', 'betradar.com', 'lsports.eu',
            'betconstruct.com', 'kambi.com', 'sbtech.com',
            'pinnacle.com', 'oddsapi.io', 'the-odds-api.com',
            'api.the-odds-api.com', 'odds.com'
        ];
        
        return !url.includes('betika.com') && 
               externalProviders.some(provider => url.includes(provider));
    }

    identifyProvider(url) {
        if (url.includes('sportradar') || url.includes('betradar')) return 'Sportradar/Betradar';
        if (url.includes('lsports')) return 'LSports';
        if (url.includes('betconstruct')) return 'BetConstruct';
        if (url.includes('kambi')) return 'Kambi';
        if (url.includes('sbtech')) return 'SBTech';
        if (url.includes('odds-api')) return 'The Odds API';
        return 'Unknown Provider';
    }

    isJSONResponse(response) {
        const contentType = response.headers()['content-type'] || '';
        return contentType.includes('application/json') || contentType.includes('text/json');
    }

    isJSONContent(content) {
        try {
            JSON.parse(content);
            return true;
        } catch {
            return false;
        }
    }

    containsOddsData(jsonData) {
        const oddsKeywords = ['odds', 'bet', 'match', 'team', 'league', 'sport', 'game'];
        const jsonString = JSON.stringify(jsonData).toLowerCase();
        return oddsKeywords.some(keyword => jsonString.includes(keyword));
    }

    /**
     * Generate comprehensive analysis report
     */
    async generateAnalysisReport() {
        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                total_requests: this.networkRequests.length,
                api_calls: this.apiCalls.length,
                external_sources: this.externalSources.length,
                websocket_connections: this.websocketConnections.length,
                odds_data_found: this.oddsData.length
            },
            network_analysis: {
                api_calls: this.apiCalls,
                external_sources: this.externalSources,
                websocket_connections: this.websocketConnections
            },
            odds_data: this.oddsData,
            external_providers: [...new Set(this.externalSources.map(src => src.provider))],
            recommendations: this.generateRecommendations(),
            raw_data_sources: this.identifyRawDataSources()
        };
        
        return report;
    }

    generateRecommendations() {
        return {
            scraping_strategy: "Use headless browser automation with network interception",
            rate_limiting: "Implement delays between requests (2-5 seconds minimum)",
            authentication: "May require session management and CSRF tokens",
            anti_bot_measures: "Cloudflare protection detected - use residential proxies",
            data_extraction: "Focus on AJAX endpoints and WebSocket connections for live data",
            legal_compliance: "Review terms of service and implement respectful scraping practices"
        };
    }

    identifyRawDataSources() {
        const sources = [];
        
        this.externalSources.forEach(source => {
            sources.push({
                provider: source.provider,
                url: source.url,
                data_type: "External odds feed",
                access_method: "API integration",
                real_time: source.url.includes('ws://') || source.url.includes('wss://')
            });
        });
        
        this.apiCalls.forEach(call => {
            if (call.url.includes('betika.com')) {
                sources.push({
                    provider: "Betika Internal",
                    url: call.url,
                    data_type: "Internal API",
                    access_method: call.method,
                    real_time: call.url.includes('live') || call.url.includes('update')
                });
            }
        });
        
        return sources;
    }

    /**
     * Save analysis results
     */
    async saveResults(report) {
        try {
            await fs.writeFile(
                '/workspace/betika-api-analysis-results.json',
                JSON.stringify(report, null, 2)
            );
            
            // Generate summary report
            const summary = `
# Betika API Analysis Summary

## Overview
- **Total Network Requests**: ${report.summary.total_requests}
- **API Calls Identified**: ${report.summary.api_calls}
- **External Sources Found**: ${report.summary.external_sources}
- **WebSocket Connections**: ${report.summary.websocket_connections}
- **Odds Data Instances**: ${report.summary.odds_data_found}

## External Providers Detected
${report.external_providers.map(provider => `- ${provider}`).join('\n')}

## Key Findings
${JSON.stringify(report.recommendations, null, 2)}

## Raw Data Sources
${report.raw_data_sources.map(source => 
    `- **${source.provider}**: ${source.data_type} (${source.access_method})`
).join('\n')}
`;
            
            await fs.writeFile('/workspace/betika-analysis-summary.md', summary);
            
            console.log('💾 Results saved to:');
            console.log('  - betika-api-analysis-results.json');
            console.log('  - betika-analysis-summary.md');
            
        } catch (error) {
            console.error('❌ Failed to save results:', error);
        }
    }
}

// Usage
async function runAnalysis() {
    const analyzer = new BetikaAPIAnalyzer();
    await analyzer.analyzeBetikaAPIs();
}

// Export for use
module.exports = { BetikaAPIAnalyzer };

// Run if called directly
if (require.main === module) {
    runAnalysis().catch(console.error);
}

/**
 * Installation and Usage:
 * 
 * 1. Install dependencies:
 *    npm install puppeteer
 * 
 * 2. Run analysis:
 *    node betika-api-analysis.js
 * 
 * 3. Check results:
 *    - betika-api-analysis-results.json (detailed data)
 *    - betika-analysis-summary.md (readable summary)
 */