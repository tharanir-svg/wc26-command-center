import os
import json
import requests
from datetime import datetime
import google.generativeai as genai

NEWS_API_KEY = os.environ["NEWS_API_KEY"]

genai.configure(
api_key=os.environ["GEMINI_API_KEY"]
)

model = genai.GenerativeModel("gemini-1.5-flash")

url = (
f"https://newsapi.org/v2/everything?"
f"q=(FIFA OR World Cup OR stadium OR fan zone)"
f"&language=en"
f"&sortBy=publishedAt"
f"&pageSize=5"
f"&apiKey={NEWS_API_KEY}"
)

news = requests.get(url).json()

risks = []
timeline = []

for article in news.get("articles", []):

```
headline = article["title"]

prompt = f"""
```

You are a FIFA World Cup security analyst.

Classify this headline:

{headline}

Return ONLY one of:

P1 CRITICAL
P2 MEDIUM
P3 LOW
"""

```
result = model.generate_content(prompt)

severity = result.text.strip()

color = "amber"

if "P1" in severity:
    color = "red"

risks.append({
    "title": headline,
    "severityText": severity,
    "severityColor": color,
    "status": "VERIFIED",
    "statusColor": "emerald",
    "description": article.get("description", ""),
    "links": [
        {
            "label": "Source",
            "url": article["url"]
        }
    ]
})

timeline.append({
    "date": datetime.utcnow().strftime("%b %d"),
    "loc": "Global",
    "event": headline,
    "impact": severity
})
```

data = {
"lastUpdated": datetime.utcnow().isoformat() + "Z",
"risks": risks,
"timeline": timeline
}

with open("data.json", "w") as f:
json.dump(data, f, indent=2)
