import os
import json
from datetime import datetime
import google.generativeai as genai

genai.configure(
    api_key=os.environ["GEMINI_API_KEY"]
)

model = genai.GenerativeModel("gemini-1.5-flash")

response = model.generate_content(
    """
    You are a FIFA World Cup security analyst.

    Generate one realistic low-risk event
    that could affect a World Cup host city.

    Return only a short sentence.
    """
)

data = {
    "lastUpdated": datetime.utcnow().isoformat() + "Z",
    "risks": [
        {
            "title": response.text.strip(),
            "severityText": "P3 LOW",
            "severityColor": "amber",
            "status": "AI GENERATED",
            "statusColor": "emerald",
            "description": response.text.strip(),
            "links": []
        }
    ],
    "timeline": []
}

with open("data.json", "w") as f:
    json.dump(data, f, indent=2)
