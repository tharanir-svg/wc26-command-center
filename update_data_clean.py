import os
import json
import requests
from datetime import datetime
import google.generativeai as genai

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

NEWS_API_KEY = os.environ["NEWS_API_KEY"]

genai.configure(
    api_key=os.environ["GEMINI_API_KEY"]
)

model = genai.GenerativeModel("gemini-1.5-flash")

# --------------------------------------------------
# WORLD CUP NEWS SEARCH
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
    "&pageSize=25"
    f"&apiKey={NEWS_API_KEY}"
)

print("Fetching articles...")

news = requests.get(url, timeout=30).json()

articles = news.get("articles", [])

print(f"Articles returned: {len(articles)}")

risks = []
timeline = []

# --------------------------------------------------
# FILTERS
# --------------------------------------------------

required_terms = [
    "fifa",
    "world cup",
    "world cup 2026",
    "wc26",
    "host city",
    "stadium",
    "fan zone",
    "metlife",
    "sofi",
    "azteca",
    "bmo field"
]

blocked_terms = [
    "sensex",
    "nifty",
    "stock",
    "share market",
    "teacher",
    "school",
    "education",
    "mining",
    "bitcoin",
    "crypto",
    "entertainment",
    "movie",
    "celebrity",
    "music"
]

# --------------------------------------------------
# PROCESS ARTICLES
# --------------------------------------------------

for article in articles:

    headline = article.get("title", "")

    if not headline:
        continue

    headline_lower = headline.lower()

    # hard block
    if any(term in headline_lower for term in blocked_terms):
        continue

    # must contain wc-related keywords
    if not any(term in headline_lower for term in required_terms):
        continue

    try:

        relevance = model.generate_content(
f"""
You are a FIFA World Cup 2026 intelligence analyst.

Determine whether this headline is DIRECTLY relevant to:

- FIFA World Cup 2026
- Host cities
- Stadium operations
- Security
- Fan zones
- Crowd management
- Transportation
- Public safety
- Terrorism
- Protests affecting tournament operations

Headline:
{headline}

Return ONLY:

YES

or

NO
"""
        )

        if "YES" not in relevance.text.upper():
            continue

        severity_response = model.generate_content(
f"""
You are a World Cup security analyst.

Classify this headline.

Headline:
{headline}

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

    except Exception as e:

        print("Gemini error:", e)

        severity = "P3"

    # --------------------------------------------------
    # COLORS
    # --------------------------------------------------

    if severity == "P1":

        severity_text = "P1 CRITICAL"
        color = "red"

    elif severity == "P2":

        severity_text = "P2 MEDIUM"
        color = "orange"

    else:

        severity_text = "P3 LOW"
        color = "amber"

    # --------------------------------------------------
    # DASHBOARD CARD
    # --------------------------------------------------

    risks.append({
        "title": headline,
        "severityText": severity_text,
        "severityColor": color,
        "status": "VERIFIED",
        "statusColor": "emerald",
        "description": article.get("description", ""),
        "links": [
            {
                "label": "Source",
                "url": article.get("url", "")
            }
        ]
    })

    timeline.append({
        "date": datetime.utcnow().strftime("%b %d"),
        "loc": "Global",
        "event": headline,
        "impact": severity_text
    })

print(f"Relevant articles found: {len(risks)}")

# --------------------------------------------------
# LOAD STATIC DATA
# --------------------------------------------------

with open("static-data.json", "r") as f:
    data = json.load(f)

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

print("data.json updated successfully")
