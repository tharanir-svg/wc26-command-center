import os
import json
import requests
from datetime import datetime
import google.generativeai as genai

print("=" * 60)
print("RUNNING UPDATE_DATA_CLEAN.PY")
print("=" * 60)

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
    '"Hard Rock Stadium" OR '
    '"Mercedes-Benz Stadium")'
    "&language=en"
    "&sortBy=publishedAt"
    "&pageSize=100"
    f"&apiKey={NEWS_API_KEY}"
)

print("Fetching articles...")

response = requests.get(url, timeout=30)

print("News API status:", response.status_code)

news = response.json()

articles = news.get("articles", [])

print(f"Articles returned: {len(articles)}")

print("\n===== ARTICLES RETURNED =====")

for article in articles[:50]:
    print("-", article.get("title", "NO TITLE"))

print("=============================\n")

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
    "recruitment",
    "mining",
    "bitcoin",
    "crypto",
    "gaming",
    "monitor",
    "review",
    "movie",
    "music",
    "celebrity",
    "fashion",
    "iphone",
    "android",
    "baseball",
    "mlb",
    "nba",
    "nhl",
    "golf",
    "tennis"
]

# --------------------------------------------------
# PROCESS ARTICLES
# --------------------------------------------------

risks = []
timeline = []

for article in articles:

    title = article.get("title", "")
    description = article.get("description", "") or ""

    if not title:
        continue

    content = f"{title} {description}".lower()

    # ----------------------------------------------
    # BLOCK OBVIOUS JUNK
    # ----------------------------------------------

    if any(term in content for term in blocked_terms):
        print("BLOCKED:", title)
        continue

    # ----------------------------------------------
    # REQUIRE WC26 TERMS
    # ----------------------------------------------

    if not any(term in content for term in required_terms):
        continue

    # ----------------------------------------------
    # GEMINI RELEVANCE CHECK
    # ----------------------------------------------

    try:

        relevance = model.generate_content(
f"""
You are a FIFA World Cup 2026 intelligence analyst.

Headline:
{title}

Description:
{description}

Return YES only if this article directly relates to:

- FIFA World Cup 2026
- Host city operations
- Stadium operations
- Public safety
- Security
- Transportation disruption
- Fan zones
- Crowd management
- Protest activity
- Terror threats

Return NO for:

- Finance
- Stocks
- Mining
- Education
- Product reviews
- Entertainment
- Unrelated sports

Output ONLY YES or NO.
"""
        )

        relevance_text = relevance.text.strip().upper()

        print("Gemini relevance:", relevance_text)

        if "YES" not in relevance_text:
            print("REJECTED:", title)
            continue

        severity_response = model.generate_content(
f"""
Classify this FIFA World Cup 2026 event.

Headline:
{title}

Description:
{description}

Return ONLY:

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

        print("Severity:", severity)

    except Exception as e:

        print("Gemini error:", e)

        severity = "P3"

    # ----------------------------------------------
    # SEVERITY
    # ----------------------------------------------

    if severity == "P1":

        risk_level = "high"
        severity_text = "P1 CRITICAL"

    elif severity == "P2":

        risk_level = "medium"
        severity_text = "P2 MEDIUM"

    else:

        risk_level = "low"
        severity_text = "P3 LOW"

    # ----------------------------------------------
    # CITY DETECTION
    # ----------------------------------------------

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

    print("NO RELEVANT ARTICLES FOUND")

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
# UPDATE DATASET
# --------------------------------------------------

data["lastUpdated"] = datetime.utcnow().isoformat() + "Z"
data["risks"] = risks
data["timeline"] = timeline

# --------------------------------------------------
# SAVE
# --------------------------------------------------

with open("data.json", "w") as f:
    json.dump(data, f, indent=2)

print()
print("=" * 60)
print(f"Saved {len(risks)} risk items")
print("data.json updated successfully")
print("=" * 60)
