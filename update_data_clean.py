```python
import os
import json
import requests
from datetime import datetime
import google.generativeai as genai

# ==================================================
# CONFIG
# ==================================================

NEWS_API_KEY = os.environ["NEWS_API_KEY"]

genai.configure(
    api_key=os.environ["GEMINI_API_KEY"]
)

model = genai.GenerativeModel("gemini-1.5-flash")

# ==================================================
# NEWS SEARCH
# ==================================================

url = (
    "https://newsapi.org/v2/everything?"
    'q=("FIFA World Cup 2026" OR '
    '"World Cup security" OR '
    '"World Cup host city" OR '
    '"World Cup transportation" OR '
    '"World Cup protest" OR '
    '"World Cup disruption" OR '
    '"World Cup fan zone" OR '
    '"stadium security" OR '
    '"crowd control" OR '
    '"public safety")'
    "&language=en"
    "&sortBy=publishedAt"
    "&pageSize=50"
    f"&apiKey={NEWS_API_KEY}"
)

print("Fetching articles...")

news = requests.get(url, timeout=30).json()

articles = news.get("articles", [])

print(f"Articles returned: {len(articles)}")

# ==================================================
# FILTERS
# ==================================================

positive_terms = [
    "fifa",
    "world cup",
    "host city",
    "stadium",
    "fan zone",
    "security",
    "police",
    "protest",
    "crowd",
    "transport",
    "incident",
    "emergency",
    "public safety",
    "terror",
    "evacuation",
    "disruption"
]

blocked_terms = [
    "sensex",
    "nifty",
    "stock",
    "share market",
    "crypto",
    "bitcoin",
    "teacher",
    "school",
    "movie",
    "celebrity",
    "music",
    "earnings",
    "investor",
    "shareholder"
]

risks = []
timeline = []

# ==================================================
# PROCESS ARTICLES
# ==================================================

for article in articles:

    headline = article.get("title", "") or ""
    description = article.get("description", "") or ""

    if not headline:
        continue

    text = f"{headline} {description}".lower()

    # ---------------------------
    # HARD BLOCK
    # ---------------------------

    if any(term in text for term in blocked_terms):
        continue

    # ---------------------------
    # REQUIRE SIGNALS
    # ---------------------------

    matches = sum(
        1 for term in positive_terms
        if term in text
    )

    if matches < 2:
        continue

    # ---------------------------
    # GEMINI RELEVANCE CHECK
    # ---------------------------

    try:

        relevance = model.generate_content(
f"""
You are a FIFA World Cup 2026 Security Intelligence Analyst.

Only approve stories that could affect:

- stadium operations
- host city readiness
- transportation
- public safety
- protests
- terrorism
- security operations
- emergency response
- crowd management
- fan zones

Reject:

- stock markets
- finance
- celebrity news
- player transfers
- match scores
- entertainment
- general sports news

Headline:
{headline}

Description:
{description}

Return ONLY:

YES

or

NO
"""
        )

        if "YES" not in relevance.text.upper():
            continue

    except Exception as e:

        print("Gemini relevance error:", e)
        continue

    # ---------------------------
    # SEVERITY
    # ---------------------------

    try:

        severity_response = model.generate_content(
f"""
You are a World Cup Security Operations Analyst.

Classify the operational impact.

Headline:
{headline}

Description:
{description}

Return ONLY:

P1
P2
P3

Definitions:

P1 = Critical threat
     Terrorism
     Major protest
     Fatal incident
     Large disruption

P2 = Operational disruption
     Transit issues
     Security concerns
     Venue impacts

P3 = Advisory
     Planning updates
     Readiness updates
     General information
"""
        )

        severity = severity_response.text.strip().upper()

        if severity not in ["P1", "P2", "P3"]:
            severity = "P3"

    except Exception as e:

        print("Gemini severity error:", e)

        severity = "P3"

    # ---------------------------
    # MAP COLORS
    # ---------------------------

    if severity == "P1":

        severity_text = "P1 CRITICAL"
        level = "critical"

    elif severity == "P2":

        severity_text = "P2 MEDIUM"
        level = "medium"

    else:

        severity_text = "P3 LOW"
        level = "low"

    # ---------------------------
    # DASHBOARD RISK CARD
    # ---------------------------

    risks.append({

        "title": headline,

        "level": level,

        "severityText": severity_text,

        "status": "VERIFIED",

        "statusClass": "verified",

        "description": description,

        "links": [
            {
                "label": "Source",
                "url": article.get("url", "")
            }
        ]
    })

    # ---------------------------
    # TIMELINE
    # ---------------------------

    timeline.append({

        "date": datetime.utcnow().strftime("%b %d"),

        "title": headline,

        "description": description,

        "level": level
    })

print(f"Relevant articles found: {len(risks)}")

# ==================================================
# LOAD STATIC DATA
# ==================================================

with open("static-data.json", "r") as f:
    data = json.load(f)

# ==================================================
# MERGE
# ==================================================

data["lastUpdated"] = datetime.utcnow().isoformat() + "Z"

data["risks"] = risks

data["timeline"] = timeline

# ==================================================
# SAVE
# ==================================================

with open("data.json", "w") as f:
    json.dump(data, f, indent=2)

print("data.json updated successfully")
```
