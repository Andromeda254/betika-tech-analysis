"""
Betika.com Raw JSON Data Extraction & Analysis
Comprehensive script for extracting and analyzing betting odds data
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import re
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BetikaDataExtractor:
    """
    Advanced data extraction for Betika.com
    Focuses on raw JSON data and API endpoint discovery
    """
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        }
        self.base_url = 'https://www.betika.com'
        self.api_endpoints = []
        self.raw_data = []
        self.odds_data = []
        self.external_sources = []
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(ssl=False, limit=10, limit_per_host=2)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def discover_api_endpoints(self) -> List[Dict[str, Any]]:
        """
        Discover API endpoints through multiple methods
        """
        logger.info("🔍 Starting API endpoint discovery...")
        
        endpoints = []
        
        # Method 1: Analyze main page for embedded API references
        main_page_endpoints = await self._analyze_main_page()
        endpoints.extend(main_page_endpoints)
        
        # Method 2: Test common API patterns
        pattern_endpoints = await self._test_common_patterns()
        endpoints.extend(pattern_endpoints)
        
        # Method 3: Analyze JavaScript files for API references
        js_endpoints = await self._analyze_javascript_files()
        endpoints.extend(js_endpoints)
        
        self.api_endpoints = endpoints
        logger.info(f"📊 Discovered {len(endpoints)} potential API endpoints")
        
        return endpoints
    
    async def _analyze_main_page(self) -> List[Dict[str, Any]]:
        """Analyze main page HTML and embedded scripts for API references"""
        logger.info("📄 Analyzing main page for API references...")
        
        endpoints = []
        
        try:
            async with self.session.get(f'{self.base_url}/en-ke/') as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Extract potential API endpoints from JavaScript
                    api_patterns = [
                        r'/api/[^\s\'\"]+',
                        r'/ajax/[^\s\'\"]+', 
                        r'api\.[^\s\'\"]+',
                        r'endpoint[^\s]*:[^\s]*[\'\"](/[^\'\"]+)[\'\"]',
                        r'url[^\s]*:[^\s]*[\'\"](/api/[^\'\"]+)[\'\"]'
                    ]
                    
                    for pattern in api_patterns:
                        matches = re.findall(pattern, html_content, re.IGNORECASE)
                        for match in matches:
                            endpoint_url = match if match.startswith('/') else f'/{match}'
                            endpoints.append({
                                'url': urljoin(self.base_url, endpoint_url),
                                'method': 'GET',
                                'source': 'main_page_analysis',
                                'confidence': 'medium'
                            })
                    
                    # Look for WebSocket endpoints
                    ws_patterns = [
                        r'ws://[^\s\'\"]+',
                        r'wss://[^\s\'\"]+',
                        r'WebSocket\([\'\"](ws[s]?://[^\'\"]+)[\'\"]\)'
                    ]
                    
                    for pattern in ws_patterns:
                        matches = re.findall(pattern, html_content, re.IGNORECASE)
                        for match in matches:
                            endpoints.append({
                                'url': match,
                                'method': 'WebSocket',
                                'source': 'main_page_websocket',
                                'confidence': 'high'
                            })
        
        except Exception as e:
            logger.error(f"❌ Error analyzing main page: {e}")
        
        return endpoints
    
    async def _test_common_patterns(self) -> List[Dict[str, Any]]:
        """Test common API endpoint patterns used by betting sites"""
        logger.info("🎯 Testing common API patterns...")
        
        common_patterns = [
            '/api/v1/sports/football',
            '/api/v1/odds/football', 
            '/api/v1/matches/live',
            '/api/v1/matches/upcoming',
            '/api/odds/football',
            '/ajax/odds/update',
            '/ajax/matches/load',
            '/api/sports/1',  # Football sport ID
            '/api/leagues/kenya',
            '/ws/odds',
            '/websocket/odds',
            '/api/v2/sports/soccer',
            '/rest/odds/football',
            '/services/odds-service',
            '/graphql'  # Modern API pattern
        ]
        
        active_endpoints = []
        
        for pattern in common_patterns:
            try:
                url = urljoin(self.base_url, pattern)
                
                # Test with different headers to simulate AJAX requests
                ajax_headers = {
                    **self.headers,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': f'{self.base_url}/en-ke/',
                    'Accept': 'application/json'
                }
                
                async with self.session.get(url, headers=ajax_headers) as response:
                    content_type = response.headers.get('content-type', '')
                    
                    if response.status in [200, 201, 202]:
                        content = await response.text()
                        
                        # Check if response contains JSON data
                        if 'application/json' in content_type or self._is_json_content(content):
                            active_endpoints.append({
                                'url': url,
                                'method': 'GET',
                                'status': response.status,
                                'content_type': content_type,
                                'source': 'pattern_testing',
                                'confidence': 'high',
                                'response_sample': content[:500]  # First 500 chars
                            })
                            logger.info(f"✅ Active endpoint found: {url} ({response.status})")
                        
                    elif response.status in [401, 403]:
                        # Endpoint exists but requires authentication
                        active_endpoints.append({
                            'url': url,
                            'method': 'GET',
                            'status': response.status,
                            'source': 'pattern_testing',
                            'confidence': 'medium',
                            'note': 'Requires authentication'
                        })
                        logger.info(f"🔐 Protected endpoint found: {url} ({response.status})")
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.debug(f"Pattern {pattern} failed: {e}")
        
        return active_endpoints
    
    async def _analyze_javascript_files(self) -> List[Dict[str, Any]]:
        """Analyze JavaScript files for API endpoint references"""
        logger.info("📜 Analyzing JavaScript files...")
        
        endpoints = []
        
        try:
            # First, get main page to find JavaScript files
            async with self.session.get(f'{self.base_url}/en-ke/') as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Extract JavaScript file URLs
                    js_pattern = r'<script[^>]*src=[\'\"](.*?\.js.*?)[\'\"]'
                    js_files = re.findall(js_pattern, html_content, re.IGNORECASE)
                    
                    # Analyze each JavaScript file
                    for js_file in js_files[:10]:  # Limit to first 10 files
                        try:
                            js_url = urljoin(self.base_url, js_file)
                            
                            async with self.session.get(js_url) as js_response:
                                if js_response.status == 200:
                                    js_content = await js_response.text()
                                    
                                    # Look for API patterns in JavaScript
                                    api_patterns = [
                                        r'[\'\"](/api/[^\'\"]+)[\'\"]',
                                        r'[\'\"](/ajax/[^\'\"]+)[\'\"]',
                                        r'apiUrl[^\w]*[:=][^\w]*[\'\"]([^\'\"]+)[\'\"]',
                                        r'endpoint[^\w]*[:=][^\w]*[\'\"]([^\'\"]+)[\'\"]'
                                    ]
                                    
                                    for pattern in api_patterns:
                                        matches = re.findall(pattern, js_content, re.IGNORECASE)
                                        for match in matches:
                                            endpoint_url = urljoin(self.base_url, match)
                                            endpoints.append({
                                                'url': endpoint_url,
                                                'method': 'GET',
                                                'source': f'javascript_analysis:{js_file}',
                                                'confidence': 'medium'
                                            })
                            
                            await asyncio.sleep(0.5)  # Rate limiting
                            
                        except Exception as e:
                            logger.debug(f"Failed to analyze JS file {js_file}: {e}")
        
        except Exception as e:
            logger.error(f"❌ Error analyzing JavaScript files: {e}")
        
        return endpoints
    
    async def extract_raw_json_data(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract raw JSON data from discovered endpoints
        """
        logger.info("📥 Extracting raw JSON data from endpoints...")
        
        raw_data = []
        
        for endpoint in endpoints:
            if endpoint.get('method') == 'WebSocket':
                continue  # Skip WebSocket endpoints for now
                
            try:
                url = endpoint['url']
                
                # Try different request methods and headers
                request_variants = [
                    {'method': 'GET', 'headers': {**self.headers, 'Accept': 'application/json'}},
                    {'method': 'GET', 'headers': {**self.headers, 'X-Requested-With': 'XMLHttpRequest'}},
                    {'method': 'POST', 'headers': {**self.headers, 'Content-Type': 'application/json'}, 'data': '{}'}
                ]
                
                for variant in request_variants:
                    try:
                        async with self.session.request(
                            variant['method'], 
                            url, 
                            headers=variant['headers'],
                            data=variant.get('data')
                        ) as response:
                            
                            if response.status in [200, 201, 202]:
                                content = await response.text()
                                content_type = response.headers.get('content-type', '')
                                
                                # Check if it's JSON data
                                if ('application/json' in content_type or 
                                    self._is_json_content(content)):
                                    
                                    try:
                                        json_data = json.loads(content)
                                        
                                        # Check if it contains betting/odds related data
                                        if self._contains_betting_data(json_data):
                                            raw_data.append({
                                                'endpoint': url,
                                                'method': variant['method'],
                                                'status': response.status,
                                                'timestamp': datetime.now().isoformat(),
                                                'data': json_data,
                                                'data_type': self._classify_data_type(json_data),
                                                'size': len(content)
                                            })
                                            
                                            logger.info(f"📊 Extracted betting data from: {url}")
                                            break  # Found data, no need to try other variants
                                    
                                    except json.JSONDecodeError:
                                        logger.debug(f"Invalid JSON from {url}")
                    
                    except Exception as e:
                        logger.debug(f"Variant failed for {url}: {e}")
                    
                    await asyncio.sleep(0.5)  # Rate limiting between variants
                
                await asyncio.sleep(1)  # Rate limiting between endpoints
                
            except Exception as e:
                logger.debug(f"Failed to extract data from {url}: {e}")
        
        self.raw_data = raw_data
        logger.info(f"📈 Extracted raw data from {len(raw_data)} endpoints")
        
        return raw_data
    
    def _is_json_content(self, content: str) -> bool:
        """Check if content is valid JSON"""
        try:
            json.loads(content)
            return True
        except:
            return False
    
    def _contains_betting_data(self, data: Any) -> bool:
        """Check if JSON data contains betting/odds related information"""
        data_str = json.dumps(data).lower()
        
        betting_keywords = [
            'odds', 'bet', 'match', 'team', 'league', 'sport', 'game',
            'fixture', 'event', 'market', 'outcome', 'stake', 'win',
            'football', 'soccer', 'kpl', 'premier'
        ]
        
        return any(keyword in data_str for keyword in betting_keywords)
    
    def _classify_data_type(self, data: Any) -> str:
        """Classify the type of betting data"""
        data_str = json.dumps(data).lower()
        
        if any(word in data_str for word in ['live', 'inplay', 'running']):
            return 'live_odds'
        elif any(word in data_str for word in ['upcoming', 'fixture', 'schedule']):
            return 'upcoming_matches'
        elif any(word in data_str for word in ['league', 'competition', 'tournament']):
            return 'league_data'
        elif any(word in data_str for word in ['odds', 'market', 'outcome']):
            return 'odds_data'
        else:
            return 'general_betting_data'
    
    async def analyze_data_consumption_patterns(self) -> Dict[str, Any]:
        """
        Analyze how Betika consumes and processes external data
        """
        logger.info("🔄 Analyzing data consumption patterns...")
        
        analysis = {
            'api_patterns': {},
            'update_frequencies': {},
            'data_sources': {},
            'integration_methods': {},
            'caching_strategies': {}
        }
        
        # Analyze API calling patterns
        for data in self.raw_data:
            endpoint = data['endpoint']
            data_type = data['data_type']
            
            # Pattern analysis
            if 'api' in endpoint:
                analysis['api_patterns']['rest_api'] = analysis['api_patterns'].get('rest_api', 0) + 1
            if 'ajax' in endpoint:
                analysis['api_patterns']['ajax'] = analysis['api_patterns'].get('ajax', 0) + 1
            if 'ws' in endpoint:
                analysis['api_patterns']['websocket'] = analysis['api_patterns'].get('websocket', 0) + 1
            
            # Data type distribution
            analysis['data_sources'][data_type] = analysis['data_sources'].get(data_type, 0) + 1
        
        # Identify external provider integrations
        external_indicators = []
        for data in self.raw_data:
            json_str = json.dumps(data['data'])
            
            # Look for external provider signatures
            providers = {
                'sportradar': ['sportradar', 'betradar', 'sr:', 'unified_odds'],
                'lsports': ['lsports', 'altenar', 'ls_'],
                'betconstruct': ['betconstruct', 'bc_'],
                'kambi': ['kambi', 'kb_']
            }
            
            for provider, signatures in providers.items():
                if any(sig in json_str.lower() for sig in signatures):
                    external_indicators.append(provider)
        
        analysis['external_providers'] = list(set(external_indicators))
        
        return analysis
    
    async def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        logger.info("📋 Generating comprehensive analysis report...")
        
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_endpoints_discovered': len(self.api_endpoints),
                'active_endpoints': len([e for e in self.api_endpoints if e.get('status') == 200]),
                'raw_data_sources': len(self.raw_data),
                'data_types_found': len(set(d['data_type'] for d in self.raw_data))
            },
            'api_endpoints': self.api_endpoints,
            'raw_data_samples': self.raw_data[:5],  # First 5 samples
            'data_consumption_analysis': await self.analyze_data_consumption_patterns(),
            'implementation_strategies': {
                'primary_integration': 'REST API with AJAX updates',
                'real_time_updates': 'WebSocket connections for live odds',
                'caching_strategy': 'Multi-layer caching (CDN + Application)',
                'external_providers': 'Sportradar/LSports integration likely',
                'data_processing': 'JSON-based data exchange'
            },
            'recommendations': {
                'scraping_approach': 'Focus on AJAX endpoints for structured data',
                'rate_limiting': 'Implement 2-3 second delays between requests',
                'authentication': 'May require session management',
                'data_extraction': 'Target JSON endpoints rather than HTML parsing',
                'monitoring': 'Watch for API changes and endpoint deprecation'
            }
        }
        
        return report
    
    async def save_results(self, report: Dict[str, Any]):
        """Save analysis results to files"""
        try:
            # Save comprehensive report
            with open('betika-comprehensive-analysis.json', 'w') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            # Save raw data separately
            with open('betika-raw-data.json', 'w') as f:
                json.dump(self.raw_data, f, indent=2, ensure_ascii=False)
            
            # Save API endpoints
            with open('betika-api-endpoints.json', 'w') as f:
                json.dump(self.api_endpoints, f, indent=2, ensure_ascii=False)
            
            logger.info("💾 Results saved successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")

async def main():
    """
    Main execution function
    """
    logger.info("🚀 Starting Betika comprehensive analysis...")
    
    async with BetikaDataExtractor() as extractor:
        try:
            # Step 1: Discover API endpoints
            endpoints = await extractor.discover_api_endpoints()
            
            # Step 2: Extract raw JSON data
            raw_data = await extractor.extract_raw_json_data(endpoints)
            
            # Step 3: Generate comprehensive report
            report = await extractor.generate_comprehensive_report()
            
            # Step 4: Save results
            await extractor.save_results(report)
            
            # Print summary
            print("\n" + "="*50)
            print("🎉 BETIKA ANALYSIS COMPLETE!")
            print("="*50)
            print(f"📊 Endpoints Discovered: {len(endpoints)}")
            print(f"📥 Raw Data Sources: {len(raw_data)}")
            print(f"🔍 External Providers: {len(report['data_consumption_analysis']['external_providers'])}")
            print("\n📁 Files Generated:")
            print("  - betika-comprehensive-analysis.json")
            print("  - betika-raw-data.json")
            print("  - betika-api-endpoints.json")
            print("="*50)
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(main())

"""
Installation and Usage:

1. Install dependencies:
   pip install aiohttp asyncio

2. Run analysis:
   python betika-raw-data-extraction.py

3. Review results in generated JSON files

4. Use extracted data for:
   - API endpoint mapping
   - External provider identification
   - Data consumption pattern analysis
   - Implementation strategy development
"""