"""
Betika.com Firecrawl Configuration for Kenya Soccer Odds Analysis
Advanced web crawling and data extraction for betting odds analysis
"""

import json
import requests
import time
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BetikaFirecrawlAnalyzer:
    """
    Advanced Firecrawl implementation for Betika.com analysis
    Focuses on API discovery and odds data extraction
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.firecrawl.dev/v0"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def crawl_betika_comprehensive(self) -> Dict[str, Any]:
        """
        Comprehensive Betika crawling configuration
        """
        crawl_config = {
            "url": "https://www.betika.com/en-ke/",
            "crawlOptions": {
                "includes": [
                    "https://www.betika.com/en-ke/sport/*",
                    "https://www.betika.com/en-ke/api/*",
                    "https://www.betika.com/**/football**",
                    "https://www.betika.com/**/soccer**",
                    "https://www.betika.com/**/odds**"
                ],
                "excludes": [
                    "https://www.betika.com/en-ke/casino/*",
                    "https://www.betika.com/en-ke/jackpot/*",
                    "https://www.betika.com/**/terms**",
                    "https://www.betika.com/**/privacy**"
                ],
                "generateImagesAltText": False,
                "returnOnlyUrls": False,
                "maxDepth": 3,
                "mode": "scrape",
                "limit": 100,
                "allowBackwardCrawling": False,
                "allowExternalContentLinks": True
            },
            "pageOptions": {
                "headers": {
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                },
                "includeHtml": True,
                "includeRawHtml": True,
                "onlyMainContent": False,
                "includeLinks": True,
                "screenshot": True,
                "waitFor": 5000,
                "timeout": 30000
            },
            "extractorOptions": {
                "extractionSchema": {
                    "odds_data": {
                        "type": "array",
                        "items": {
                            "type": "object", 
                            "properties": {
                                "match_id": {"type": "string"},
                                "team_home": {"type": "string"},
                                "team_away": {"type": "string"},
                                "odds_home": {"type": "number"},
                                "odds_draw": {"type": "number"},
                                "odds_away": {"type": "number"},
                                "league": {"type": "string"},
                                "match_time": {"type": "string"},
                                "live_status": {"type": "boolean"}
                            }
                        }
                    },
                    "api_endpoints": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "endpoint_url": {"type": "string"},
                                "method": {"type": "string"},
                                "data_type": {"type": "string"}
                            }
                        }
                    },
                    "javascript_apis": {
                        "type": "array", 
                        "items": {
                            "type": "string"
                        }
                    },
                    "websocket_connections": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    }
                }
            }
        }
        
        return crawl_config

    def scrape_specific_endpoints(self) -> List[Dict[str, Any]]:
        """
        Target specific Betika endpoints for detailed analysis
        """
        target_urls = [
            "https://www.betika.com/en-ke/sport/football",
            "https://www.betika.com/en-ke/sport/1",  # Football category ID
            "https://www.betika.com/en-ke/live-betting",
            "https://www.betika.com/en-ke/api/odds/football",  # Potential API endpoint
            "https://www.betika.com/en-ke/ajax/odds/update",   # Potential AJAX endpoint
        ]
        
        scrape_configs = []
        
        for url in target_urls:
            config = {
                "url": url,
                "pageOptions": {
                    "headers": {
                        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                        "Accept": "application/json, text/plain, */*",
                        "Referer": "https://www.betika.com/en-ke/",
                        "X-Requested-With": "XMLHttpRequest"
                    },
                    "includeHtml": True,
                    "includeRawHtml": True,
                    "includeLinks": True,
                    "screenshot": True,
                    "waitFor": 3000,
                    "actions": [
                        {
                            "type": "wait",
                            "milliseconds": 2000
                        },
                        {
                            "type": "screenshot"
                        }
                    ]
                },
                "extractorOptions": {
                    "mode": "llm-extraction",
                    "extractionPrompt": """
                    Extract all soccer/football betting odds data from this page. 
                    Look for:
                    1. Match information (teams, leagues, dates)
                    2. Betting odds (1X2, Over/Under, etc.)
                    3. API endpoints or AJAX calls in the source code
                    4. WebSocket connections
                    5. External data source references
                    6. JSON data embedded in JavaScript
                    
                    Return the data in structured JSON format.
                    """
                }
            }
            scrape_configs.append(config)
            
        return scrape_configs

    def execute_crawl(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Firecrawl crawling with the provided configuration
        """
        try:
            response = requests.post(
                f"{self.base_url}/crawl",
                headers=self.headers,
                json=config,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get('jobId')
                logger.info(f"Crawl job started with ID: {job_id}")
                return self.monitor_crawl_job(job_id)
            else:
                logger.error(f"Crawl failed: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            logger.error(f"Crawl execution error: {str(e)}")
            return {"error": str(e)}

    def execute_scrape(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Firecrawl scraping for single pages
        """
        try:
            response = requests.post(
                f"{self.base_url}/scrape",
                headers=self.headers,
                json=config,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Scrape failed: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            logger.error(f"Scrape execution error: {str(e)}")
            return {"error": str(e)}

    def monitor_crawl_job(self, job_id: str, max_wait: int = 300) -> Dict[str, Any]:
        """
        Monitor crawling job progress and retrieve results
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(
                    f"{self.base_url}/crawl/status/{job_id}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get('status', 'unknown')
                    
                    logger.info(f"Job {job_id} status: {status}")
                    
                    if status == 'completed':
                        logger.info("Crawl job completed successfully!")
                        return status_data
                    elif status == 'failed':
                        logger.error("Crawl job failed!")
                        return status_data
                    
                    time.sleep(10)  # Wait 10 seconds before next check
                else:
                    logger.error(f"Status check failed: {response.status_code}")
                    return {"error": f"Status check failed: {response.status_code}"}
                    
            except Exception as e:
                logger.error(f"Job monitoring error: {str(e)}")
                return {"error": str(e)}
        
        logger.warning(f"Job {job_id} timed out after {max_wait} seconds")
        return {"error": "Job timeout"}

    def analyze_betting_patterns(self) -> Dict[str, Any]:
        """
        Comprehensive analysis execution
        """
        logger.info("Starting comprehensive Betika analysis...")
        
        results = {
            "comprehensive_crawl": None,
            "endpoint_analysis": [],
            "api_discovery": [],
            "external_sources": [],
            "odds_patterns": []
        }
        
        # 1. Comprehensive crawling
        crawl_config = self.crawl_betika_comprehensive()
        logger.info("Executing comprehensive crawl...")
        results["comprehensive_crawl"] = self.execute_crawl(crawl_config)
        
        # 2. Specific endpoint scraping
        scrape_configs = self.scrape_specific_endpoints()
        for i, config in enumerate(scrape_configs):
            logger.info(f"Scraping endpoint {i+1}/{len(scrape_configs)}: {config['url']}")
            result = self.execute_scrape(config)
            results["endpoint_analysis"].append({
                "url": config["url"],
                "data": result
            })
            time.sleep(2)  # Rate limiting
        
        logger.info("Analysis complete!")
        return results

def main():
    """
    Main execution function for Betika analysis
    """
    # Initialize analyzer (API key would be provided)
    # analyzer = BetikaFirecrawlAnalyzer("your-firecrawl-api-key")
    
    # Example usage:
    example_config = BetikaFirecrawlAnalyzer("dummy-key").crawl_betika_comprehensive()
    
    print("=== FIRECRAWL BETIKA CONFIGURATION ===")
    print(json.dumps(example_config, indent=2))
    
    print("\n=== USAGE INSTRUCTIONS ===")
    print("""
    1. Sign up for Firecrawl API at https://firecrawl.dev
    2. Get your API key
    3. Install required packages: pip install requests
    4. Initialize analyzer: analyzer = BetikaFirecrawlAnalyzer("your-api-key")
    5. Run analysis: results = analyzer.analyze_betting_patterns()
    6. Process results to identify API endpoints and data sources
    """)

if __name__ == "__main__":
    main()

"""
Expected Output Analysis:

1. API Endpoints Discovery:
   - /api/odds/football/live
   - /ajax/odds/update
   - /ws/odds (WebSocket connections)
   - /api/matches/upcoming

2. External Data Sources:
   - Betradar/Sportradar API calls
   - LSports data feeds
   - Real-time odds providers
   - Live score services

3. Internal Data Flow:
   - Odds calculation algorithms
   - Risk management systems
   - User betting patterns
   - Margin calculations

4. Raw JSON Data Extraction:
   - Structured odds data
   - Match metadata
   - League information
   - Historical trends
"""