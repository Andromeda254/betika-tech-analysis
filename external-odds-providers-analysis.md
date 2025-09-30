# External Odds Providers & API Sources Analysis
## Kenya Betting Market Focus - Betika.com Implementation

### Major Sports Data & Odds Providers

#### 1. Sportradar/Betradar
**Primary Provider for African Markets**
- **API Endpoints**: 
  - `api.sportradar.com/odds/v1/`
  - `api.betradar.com/v1/sports/`
- **Coverage**: Comprehensive soccer coverage including KPL, EPL, Champions League
- **Data Types**: Pre-match odds, live odds, match statistics, player data
- **Integration Method**: RESTful APIs with WebSocket streams for live data
- **JSON Structure**:
```json
{
  "sport_event": {
    "id": "sr:match:12345",
    "competitors": [
      {"id": "sr:competitor:1", "name": "AFC Leopards"},
      {"id": "sr:competitor:2", "name": "Gor Mahia"}
    ]
  },
  "markets": [
    {
      "id": "1x2",
      "outcomes": [
        {"id": "1", "odds": 2.50},
        {"id": "x", "odds": 3.20},
        {"id": "2", "odds": 2.80}
      ]
    }
  ]
}
```

#### 2. LSports (Altenar)
**High-Speed Live Data Provider**
- **API Endpoints**:
  - `api.lsports.eu/v2/`
  - `feed.lsports.eu/soccer/`
- **Specialization**: Ultra-fast live odds updates (<500ms latency)
- **Coverage**: 1000+ leagues worldwide, strong African coverage
- **Integration**: WebSocket feeds, RESTful APIs
- **Raw Data Access**: Available via API subscriptions
```json
{
  "EventId": 123456,
  "HomeTeam": "Tusker FC",
  "AwayTeam": "Kakamega Homeboyz",
  "Markets": {
    "1X2": {
      "1": {"Price": 1.85, "LastUpdate": "2025-09-30T15:30:00Z"},
      "X": {"Price": 3.40, "LastUpdate": "2025-09-30T15:30:00Z"},
      "2": {"Price": 4.20, "LastUpdate": "2025-09-30T15:30:00Z"}
    }
  }
}
```

#### 3. BetConstruct Platform
**White-label Betting Solution**
- **API Structure**: `api.betconstruct.com/v1/`
- **Features**: Complete betting platform with odds engine
- **African Integration**: Used by multiple Kenyan operators
- **Data Flow**: Internal odds calculation with external feed integration

#### 4. Kambi (Previously GAN)
**Sportsbook Platform Provider**
- **API Endpoints**: `api.kambi.com/offering/api/`
- **Market Position**: Premium sportsbook solutions
- **Integration**: Platform-as-a-service model
- **Data Sources**: Aggregated from multiple feed providers

#### 5. SBTech (Now DraftKings)
**Enterprise Sportsbook Platform**
- **Coverage**: Comprehensive African sports coverage
- **Technology**: Cloud-based microservices architecture
- **Real-time Capabilities**: Sub-second odds updates

### API Integration Patterns for Betika

#### Expected Data Flow Architecture
```
External Providers (Sportradar/LSports) 
    ↓ API Calls/WebSocket
Betika Odds Engine
    ↓ Processing/Risk Management
Betika Frontend API
    ↓ AJAX/WebSocket
User Interface
```

#### Potential Betika API Endpoints
Based on industry standards, Betika likely uses:

1. **Odds Retrieval**:
   - `GET /api/v1/sports/football/odds`
   - `GET /api/v1/matches/{match_id}/odds`

2. **Live Updates**:
   - `WSS /ws/odds/live`
   - `GET /api/v1/odds/updates?since={timestamp}`

3. **Match Data**:
   - `GET /api/v1/matches/today`
   - `GET /api/v1/leagues/kenya-premier-league`

#### Raw JSON Data Access Methods

**Method 1: Direct API Interception**
```javascript
// Browser Network Tab Analysis
// Look for XHR/Fetch requests to:
- /api/odds
- /ajax/update
- WebSocket connections (ws:// or wss://)
```

**Method 2: External Provider Access**
```python
# Example LSports API access
import requests

headers = {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
}

response = requests.get(
    'https://api.lsports.eu/v2/fixtures',
    headers=headers,
    params={
        'sports': '6046',  # Football
        'markets': '1,2,3'  # 1X2, O/U, Both Score
    }
)
```

### Betika's Data Consumption Strategy

#### 1. Primary Feed Integration
- **Source**: Likely Sportradar (most common in Africa)
- **Method**: Real-time WebSocket feeds
- **Processing**: Internal risk management layer
- **Storage**: Redis/MongoDB for fast access

#### 2. Odds Calculation Engine
```python
# Simplified odds processing workflow
def process_external_odds(external_odds, risk_params):
    base_odds = external_odds['markets']['1x2']
    
    # Apply house edge (typically 5-8% for African markets)
    house_margin = 0.06
    
    # Risk management adjustments
    risk_multiplier = calculate_risk_factor(match_data)
    
    # Final odds calculation
    final_odds = {
        '1': adjust_odds(base_odds['1'], house_margin, risk_multiplier),
        'X': adjust_odds(base_odds['X'], house_margin, risk_multiplier), 
        '2': adjust_odds(base_odds['2'], house_margin, risk_multiplier)
    }
    
    return final_odds
```

#### 3. Real-time Update Mechanism
- **Frequency**: 1-3 second updates for live matches
- **Technology**: WebSocket connections to frontend
- **Caching**: Multi-layer caching (CDN, Application, Database)

### Reverse Engineering Approach

#### Network Analysis Targets
1. **Main Sports Page**: `www.betika.com/en-ke/sport/football`
2. **Live Betting**: Look for WebSocket connections
3. **API Calls**: Monitor Network tab for AJAX requests
4. **JavaScript Analysis**: Search for API configuration in source

#### Expected API Response Patterns
```json
{
    "status": "success",
    "data": {
        "matches": [
            {
                "id": "12345",
                "league": "Kenya Premier League",
                "home_team": "AFC Leopards",
                "away_team": "Gor Mahia",
                "kick_off": "2025-10-01T15:00:00Z",
                "markets": {
                    "1x2": {
                        "1": 2.45,
                        "x": 3.10,
                        "2": 2.90
                    },
                    "over_under": {
                        "over_2.5": 1.75,
                        "under_2.5": 2.05
                    }
                }
            }
        ]
    },
    "timestamp": "2025-09-30T15:30:00Z"
}
```

### Legal & Compliance Considerations

#### Data Access Rights
- **Terms of Service**: Review Betika's ToS for scraping policies
- **Rate Limiting**: Implement respectful crawling (2-5 second delays)
- **IP Protection**: Use rotating proxies if necessary
- **Data Usage**: Ensure compliance with data protection laws

#### Recommended Approach
1. **API Discovery**: Use browser automation to identify endpoints
2. **Rate Limiting**: Implement conservative request throttling
3. **Data Processing**: Focus on structured data extraction
4. **Monitoring**: Track for anti-bot measures and adapt

### Implementation Recommendations

#### For Apify Implementation
```javascript
const CONFIG = {
    maxConcurrency: 1,
    requestIntervalMillis: 3000,
    retries: 3,
    proxyGroups: ['RESIDENTIAL'],
    browserOptions: {
        headless: true,
        stealth: true
    }
};
```

#### For Firecrawl Implementation
```json
{
    "crawlOptions": {
        "limit": 100,
        "maxDepth": 2,
        "waitFor": 5000,
        "screenshot": true
    },
    "extractorOptions": {
        "mode": "llm-extraction",
        "extractionPrompt": "Extract all soccer betting odds, API endpoints, and external data source references"
    }
}
```

---

**Next Steps:**
1. Execute network analysis on live Betika site
2. Identify specific external provider integrations
3. Map data flow from external sources to frontend
4. Extract raw JSON data samples
5. Analyze odds calculation methodology