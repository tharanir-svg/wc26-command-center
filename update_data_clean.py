```python
import os
import json
import requests
from datetime import datetime
import google.generativeai as genai

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

NEWS_API_KEY = os.environ["NEWS_API_KEY"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")

# --------------------------------------------------
# FETCH WORLD CUP NEWS
# --------------------------------------------------

url = (
    "https://newsapi.org/v2/everything?"
    'q=("FIFA World Cup 2026" OR '
    '"2026 World Cup" OR '
    '"World Cup security" OR '
    '"World Cup stadium" OR '
    '"World Cup host city" OR '
    '"World Cup fan zone" OR '
    '"MetLife Stadium" OR '
    '"SoFi Stadium" OR '
    '"Estadio Azteca" OR '
    '"BMO Field")'
    "&language=en"
    "&sortBy=publishedAt"
    "&pageSize=50"
    f"&apiKey={NEWS_API_KEY}"
)

print("Fetching articles...")

response = requests.get(url, timeout=30)
news = response.json()

articles = news.get("articles", [])

print(f"Articles returned: {len(articles)}")

# --------------------------------------------------
# FILTERS
# --------------------------------------------------

required_terms = [
    "fifa",
    "world cup",
    "2026 world cup",
    "host city",
    "stadium",
    "security",
    "fan zone",
    "crowd",
    "transportation",
    "protest",
    "terror",
    "terrorism",
    "metlife",
    "sofi",
    "azteca",
    "bmo field",
    "hard rock stadium",
    "mercedes-benz stadium",
    "gillette stadium",
    "lincoln financial field",
    "lumen field",
    "levi's stadium"
]

blocked_terms = [
    "sensex",
    "nifty",
    "stock",
    "stocks",
    "share market",
    "teacher",
    "school",
    "education",
    "mining",
    "bitcoin",
    "crypto",
    "movie",
    "celebrity",
    "music",
    "gaming",
    "review",
    "monitor",
    "iphone",
    "android",
    "baseball",
    "mlb",
    "nba",
    "nfl",
    "nhl",
    "fashion"
]

trusted_sources = [
    "reuters",
    "associated press",
    "ap",
    "bbc",
    "cnn",
    "abc",
    "cbs",
    "fox",
    "espn",
    "the athletic"
]

# --------------------------------------------------
# PROCESS ARTICLES
# --------------------------------------------------

risks = []
timeline = []

for article in articles:

    title = article.get("title", "")

    if not title:
        continue

    title_lower = title.lower()

    # Block junk articles
    if any(term in title_lower for term in blocked_terms):
        continue

    # Require WC terms
    if not any(term in title_lower for term in required_terms):
        continue

    # Trusted sources only
    source_name = article.get("source", {}).get("name", "").lower()

    if source_name:
        if not any(src in source_name for src in trusted_sources):
            continue

    # --------------------------------------------------
    # GEMINI RELEVANCE CHECK
    # --------------------------------------------------

    try:

        relevance = model.generate_content(
f"""
You are a FIFA World Cup 2026 intelligence analyst.

Headline:
{title}

Return YES only if this headline directly relates to:

- FIFA World Cup 2026
- Host city operations
- Stadium operations
- Security incidents
- Public safety
- Transportation disruption
- Fan zones
- Crowd management
- Protest activity
- Terror threats

Return NO for:

- Finance
- Stocks
- Entertainment
- Product reviews
- Education
- Mining
- Unrelated sports

Return only YES or NO.
"""
        )

        if "YES" not in relevance.text.upper():
            continue

        severity_response = model.generate_content(
f"""
Classify this World Cup headline.

Headline:
{title}

Return only:

P1
P2
P3

Definitions:

P1 = Critical threat
P2 = Operational disruption
P3 = Advisory / informational
"""
        )

        severity = severity_response.text.strip().upper()

    except Exception as e:

        print("Gemini error:", e)
        severity = "P3"

    # --------------------------------------------------
    # SEVERITY MAPPING
    # --------------------------------------------------

    if severity == "P1":
        risk_level = "high"
        severity_text = "P1 CRITICAL"

    elif severity == "P2":
        risk_level = "medium"
        severity_text = "P2 MEDIUM"

    else:
        risk_level = "low"
        severity_text = "P3 LOW"

    # --------------------------------------------------
    # CITY DETECTION
    # --------------------------------------------------

    city = "Global"

    city_map = {
        "metlife": "New York / New Jersey",
        "sofi": "Los Angeles",
        "azteca": "Mexico City",
        "bmo field": "Toronto",
        "hard rock": "Miami",
        "mercedes-benz": "Atlanta",
        "gillette": "Boston",
        "lincoln financial": "Philadelphia",
        "lumen": "Seattle",
        "levi": "San Francisco"
    }

    for key, value in city_map.items():
        if key in title_lower:
            city = value
            break

    # --------------------------------------------------
    # DASHBOARD RISK CARD
    # --------------------------------------------------

    risks.append({
        "title": title,
        "risk": risk_level,
        "severityText": severity_text,
        "status": "VERIFIED",
        "description": article.get("description", ""),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "links": [
            {
                "label": "Source",
                "url": article.get("url", "")
            }
        ]
    })

    timeline.append({
        "date": datetime.utcnow().strftime("%b %d"),
        "loc": city,
        "event": title,
        "type": "News",
        "confidence": "Confirmed",
        "risk": risk_level,
        "impact": severity_text
    })

# --------------------------------------------------
# FALLBACK
# --------------------------------------------------

if len(risks) == 0:

    risks = [
        {
            "title": "No active public safety incidents detected",
            "risk": "low",
            "severityText": "P3 LOW",
            "status": "VERIFIED",
            "description": "No significant World Cup operational disruptions found during latest monitoring cycle.",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "links": []
        }
    ]

    timeline = [
        {
            "date": datetime.utcnow().strftime("%b %d"),
            "loc": "Global",
            "event": "Monitoring cycle completed",
            "type": "System",
            "confidence": "Confirmed",
            "risk": "low",
            "impact": "No significant events"
        }
    ]

# --------------------------------------------------
# LOAD STATIC DATA
# --------------------------------------------------

with open("static-data.json", "r") as f:
    data = json.load(f)

# --------------------------------------------------
# METRICS
# --------------------------------------------------

p1 = len([r for r in risks if r["risk"] == "high"])
p2 = len([r for r in risks if r["risk"] == "medium"])
p3 = len([r for r in risks if r["risk"] == "low"])

data["metrics"] = {
    "p1": p1,
    "p2": p2,
    "p3": p3
}

# --------------------------------------------------
# MERGE
# --------------------------------------------------

data["lastUpdated"] = datetime.utcnow().isoformat() + "Z"
data["risks"] = risks
data["timeline"] = timeline

# --------------------------------------------------
# SAVE
# --------------------------------------------------

with open("data.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Saved {len(risks)} risk items")
print("data.json updated successfully")
```
