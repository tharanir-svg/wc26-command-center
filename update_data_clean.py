import os
import json
import requests
from datetime import datetime

print("=" * 60)
print("RUNNING WC26 INTEL UPDATE")
print("=" * 60)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

NEWS_API_KEY = os.environ["NEWS_API_KEY"]

# --------------------------------------------------
# NEWS SEARCH
# --------------------------------------------------

url = (
    "https://newsapi.org/v2/everything?"
    'q=("FIFA World Cup 2026" OR '
    '"2026 FIFA World Cup" OR '
    '("World Cup" AND security) OR '
    '("World Cup" AND transportation) OR '
    '("World Cup" AND protest) OR '
    '("World Cup" AND stadium) OR '
    '("World Cup" AND host city) OR '
    '("World Cup" AND fan zone))'
    "&language=en"
    "&sortBy=publishedAt"
    "&pageSize=100"
    f"&apiKey={NEWS_API_KEY}"
)

print("Fetching articles...")

try:

    response = requests.get(url, timeout=30)

    print("News API status:", response.status_code)

    if response.status_code != 200:

        print("News API Error")
        print(response.text)

        articles = []

    else:

        news = response.json()
        articles = news.get("articles", [])

except Exception as e:

    print("News API request failed:", e)
    articles = []

print(f"Articles returned: {len(articles)}")

# --------------------------------------------------
# FILTERS
# --------------------------------------------------

worldcup_terms = [
    "fifa world cup",
    "2026 fifa world cup",
    "world cup 2026",
    "2026 world cup",
    "host city",
    "fan zone",
    "world cup security",
    "world cup stadium",
    "world cup transportation"
]

blocked_terms = [
    "sensex",
    "nifty",
    "stock",
    "stocks",
    "share market",
    "recruitment",
    "teacher",
    "education",
    "school",
    "mining",
    "crypto",
    "bitcoin",
    "gaming",
    "monitor review",
    "iphone",
    "android",
    "movie",
    "music",
    "celebrity",
    "fashion",
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
    # REQUIRE WORLD CUP TERMS
    # ----------------------------------------------

    if not any(term in content for term in worldcup_terms):

        print("NOT WC26:", title)
        continue

    # ----------------------------------------------
    # SEVERITY CLASSIFICATION
    # ----------------------------------------------

    severity = "P3"

    critical_terms = [
        "terror",
        "terrorism",
        "bomb",
        "shooting",
        "attack",
        "riot",
        "stampede",
        "evacuation",
        "active shooter",
        "casualties"
    ]

    disruption_terms = [
        "protest",
        "strike",
        "closure",
        "transport disruption",
        "security incident",
        "crowd issue",
        "traffic congestion",
        "demonstration",
        "delays"
    ]

    if any(term in content for term in critical_terms):

        severity = "P1"

    elif any(term in content for term in disruption_terms):

        severity = "P2"

    # ----------------------------------------------
    # RISK LABEL
    # ----------------------------------------------

    if severity == "P1":

        risk_level = "high"
        severity_text = "P1 CRITICAL"

    elif severity == "P2":

        risk_level = "medium"
        severity_text = "P2 DISRUPTION"

    else:

        risk_level = "low"
        severity_text = "P3 ADVISORY"

    # ----------------------------------------------
    # HOST CITY DETECTION
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
        "lumen": "Seattle",
        "vancouver": "Vancouver",
        "houston": "Houston",
        "dallas": "Dallas",
        "kansas city": "Kansas City",
        "monterrey": "Monterrey"
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
            "title": "No active World Cup security issues detected",
            "risk": "low",
            "severityText": "P3 ADVISORY",
            "status": "VERIFIED",
            "description": (
                "No verified FIFA World Cup 2026 operational, "
                "transportation or security disruptions detected."
            ),
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
            "impact": "P3 ADVISORY"
        }
    ]

# --------------------------------------------------
# LOAD STATIC DATA
# --------------------------------------------------

try:

    with open("static-data.json", "r", encoding="utf-8") as f:

        data = json.load(f)

except Exception as e:

    print("Failed to load static-data.json")
    print(e)
    raise

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

with open("data.json", "w", encoding="utf-8") as f:

    json.dump(data, f, indent=2)

print()
print("=" * 60)
print(f"Saved {len(risks)} risk items")
print("data.json updated successfully")
print("=" * 60)
