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
# NEWS SEARCH
# --------------------------------------------------

url = (
    "https://newsapi.org/v2/everything?"
    'q=("FIFA World Cup 2026" OR '
    '"2026 FIFA World Cup" OR '
    '"World Cup security" OR '
    '"World Cup host city" OR '
    '"World Cup stadium" OR '
    '"World Cup transportation" OR '
    '"World Cup fan zone" OR '
    '"MetLife Stadium" OR '
    '"SoFi Stadium" OR '
    '"Estadio Azteca" OR '
    '"BMO Field" OR '
    '"Hard Rock Stadium")'
    "&language=en"
    "&sortBy=publishedAt"
    "&pageSize=100"
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
    "2026 fifa world cup",
    "2026 world cup",
    "host city",
    "stadium",
    "fan zone",
    "security",
    "crowd",
    "transport",
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
    "levi's stadium",
    "lumen field"
]

blocked_terms = [
    "sensex",
    "nifty",
    "stock",
    "stocks",
    "share market",
    "teacher",
    "education",
    "school",
    "mining",
    "crypto",
    "bitcoin",
    "gaming",
    "review",
    "monitor",
    "iphone",
    "android",
    "movie",
    "music",
    "celebrity",
    "fashion",
    "baseball",
    "mlb",
    "nba",
    "nhl"
]

# --------------------------------------------------
# PROCESS
# --------------------------------------------------

risks = []
timeline = []

for article in articles:

    title = article.get("title", "")
    description = article.get("description", "") or ""

    if not title:
        continue

    content = f"{title} {description}".lower()

    if any(term in content for term in blocked_terms):
        print("BLOCKED:", title)
        continue

    if not any(term in content for term in required_terms):
        continue

    try:

        relevance = model.generate_content(
f"""
You are a FIFA World Cup 2026 intelligence analyst.

Headline:
{title}

Description:
{description}

Return YES only if directly related to:

- FIFA World Cup 2026
- Host city operations
- Stadium operations
- Public safety
- Transportation
- Fan zones
- Crowd management
- Protests affecting tournament operations
- Security threats
- Terror threats

Return NO otherwise.

Output ONLY YES or NO.
"""
        )

        if "YES" not in relevance.text.upper():
            continue

        severity_response = model.generate_content(
f"""
Classify this World Cup event.

Headline:
{title}

Return ONLY:

P1
P2
P3

P1 = Critical threat
P2 = Operational disruption
P3 = Advisory / informational
"""
        )

        severity = severity_response.text.strip().upper()

    except Exception as e:

        print("Gemini error:", e)
        severity = "P3"

    if severity == "P1":
        risk_level = "high"
        severity_text = "P1 CRITICAL"

    elif severity == "P2":
        risk_level = "medium"
        severity_text = "P2 MEDIUM"

    else:
        risk_level = "low"
        severity_text = "P3 LOW"

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
        "levi": "San Francisco Bay Area",
        "lumen": "Seattle"
    }

    for key, value in city_map.items():
        if key in content:
            city = value
            break

    print("KEEPING:", title)

    risks.append({
        "title": title,
        "risk": risk_level,
        "severityText": severity_text,
        "status": "VERIFIED",
        "description": description,
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
            "description": "No verified FIFA World Cup 2026 operational or security disruptions identified during this monitoring cycle.",
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
            "impact": "P3 LOW"
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

data["metrics"] = {
    "p1": len([r for r in risks if r["risk"] == "high"]),
    "p2": len([r for r in risks if r["risk"] == "medium"]),
    "p3": len([r for r in risks if r["risk"] == "low"])
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
