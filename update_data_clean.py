import os
import json
import requests
from datetime import datetime
import google.generativeai as genai

# ----------------------------
# API KEYS
# ----------------------------

NEWS_API_KEY = os.environ["NEWS_API_KEY"]

genai.configure(
    api_key=os.environ["GEMINI_API_KEY"]
)

model = genai.GenerativeModel("gemini-flash-latest")

# ----------------------------
# NEWS QUERY
# ----------------------------

url = (
    "https://newsapi.org/v2/everything?"
    "q=FIFA%20World%20Cup%202026"
    "&language=en"
    "&sortBy=publishedAt"
    "&pageSize=20"
    f"&apiKey={NEWS_API_KEY}"
)

print("Fetching news...")

news = requests.get(url).json()

risks = []
timeline = []

# ----------------------------
# PROCESS ARTICLES
# ----------------------------

for article in news.get("articles", []):

    headline = article.get("title", "")
    description = article.get("description", "")

    print(f"Checking: {headline}")

    try:

        response = model.generate_content(f"""
You are a FIFA World Cup 2026 intelligence analyst.

Determine whether this news item is relevant to:

- FIFA World Cup 2026
- Host cities
- Stadium operations
- Fan zones
- Public safety
- Transportation
- Crowd management
- Terrorism
- Protests
- Security threats
- Border issues
- Severe weather affecting tournament operations

Headline:
{headline}

Description:
{description}

Answer ONLY:

YES
or
NO
""")

        decision = response.text.strip().upper()

        if "YES" not in decision:
            print("Rejected")
            continue

        print("Accepted")

    except Exception as e:
        print(f"Gemini filter error: {e}")
        continue

    severity = "P3 LOW"
    color = "amber"

    risks.append({
        "title": headline,
        "severityText": severity,
        "severityColor": color,
        "status": "VERIFIED",
        "statusColor": "emerald",
        "description": description,
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
        "impact": severity
    })

# ----------------------------
# LOAD STATIC CONTENT
# ----------------------------

with open("static-data.json", "r") as f:
    data = json.load(f)

# ----------------------------
# MERGE LIVE CONTENT
# ----------------------------

data["lastUpdated"] = datetime.utcnow().isoformat() + "Z"
data["risks"] = risks
data["timeline"] = timeline

# ----------------------------
# SAVE
# ----------------------------

with open("data.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Saved {len(risks)} FIFA-relevant articles")
