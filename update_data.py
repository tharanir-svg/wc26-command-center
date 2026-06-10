import os
import json
import feedparser
import google.generativeai as genai

# 1. Connect to Gemini securely
# Use os.environ.get so it can be dynamically passed via GitHub Actions Secrets
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("CRITICAL ERROR: GEMINI_API_KEY is missing from GitHub Secrets!")

genai.configure(api_key=api_key)

# We tell Gemini to strictly output JSON
model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})

# 2. Get the latest news (World Cup Security/Protests)
rss_url = "https://news.google.com/rss/search?q=%22World+Cup+2026%22+threat+OR+protest+OR+strike+OR+security&hl=en-US&gl=US&ceid=US:en"
feed = feedparser.parse(rss_url)
# Grab the top 10 articles
news_items = [{"title": entry.title, "link": entry.link} for entry in feed.entries[:10]]

# 3. Ask Gemini to analyze the news and format it for our dashboard
prompt = f"""
Analyze these recent news headlines regarding the 2026 World Cup: {news_items}.
Create a JSON object exactly matching this structure. Extract maximum 4 risks and 5 timeline events based on the news.

{{
  "risks": [
    {{
      "title": "Short Threat Title",
      "severityText": "P1 HIGH or P2 MED",
      "severityColor": "red or amber",
      "status": "VERIFIED or ONGOING",
      "statusColor": "emerald or blue",
      "timestamp": "2026-06-10T12:00:00Z",
      "description": "1 to 2 sentences explaining the security risk.",
      "links": [ {{"label": "Source link", "url": "the actual url"}} ]
    }}
  ],
  "timeline": [
    {{ "date": "Upcoming Date", "loc": "City/Region", "event": "Short event description", "impact": "Short impact", "impactClass": "bg-amber-500/20 text-amber-300 border-amber-500/20" }}
  ]
}}
"""

try:
    # 4. Generate and save the data
    response = model.generate_content(prompt)
    with open("data.json", "w") as f:
        f.write(response.text)
    print("Successfully updated data.json")
except Exception as e:
    print(f"Error: {e}")
