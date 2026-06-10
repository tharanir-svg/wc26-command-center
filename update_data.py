import json
import re
import ssl
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape

QUERY = '"World Cup 2026" threat OR protest OR strike OR security'
RSS_URL = (
    'https://news.google.com/rss/search?q='
    + urllib.parse.quote(QUERY)
    + '&hl=en-US&gl=US&ceid=US:en'
)
OUTPUT_FILE = 'data.json'
MAX_RISKS = 4
MAX_TIMELINE = 5
USER_AGENT = 'Mozilla/5.0 (GitHub Actions) Python Data Updater/1.0'


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def clean_text(value: str) -> str:
    value = unescape(value or '').strip()
    value = re.sub(r'\s+', ' ', value)
    return value


def parse_google_news_title(title: str):
    title = clean_text(title)
    if ' - ' in title:
        headline, source = title.rsplit(' - ', 1)
        return headline.strip(), source.strip()
    return title, 'Google News'


def parse_pub_date(pub_date: str) -> datetime:
    try:
        dt = parsedate_to_datetime(pub_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def classify_severity(text: str):
    t = text.lower()
    high_terms = [
        'attack', 'bomb', 'explosion', 'shooting', 'terror', 'evacuation',
        'riot', 'violence', 'fatal', 'dead', 'killed', 'kidnap', 'hostage'
    ]
    medium_terms = [
        'protest', 'strike', 'security', 'threat', 'disruption', 'warning',
        'alert', 'crowd', 'police', 'arrest', 'border', 'incident'
    ]
    if any(term in t for term in high_terms):
        return 'P1 HIGH', 'red', 'ONGOING', 'blue'
    if any(term in t for term in medium_terms):
        return 'P2 MED', 'amber', 'VERIFIED', 'emerald'
    return 'P3 LOW', 'amber', 'VERIFIED', 'emerald'


def build_description(headline: str, source: str) -> str:
    base = clean_text(headline.rstrip('.'))
    return (
        f'{base}. This item was pulled from {source} and converted into a '
        'dashboard-ready risk entry for rapid monitoring.'
    )


def build_impact_class(severity_text: str) -> str:
    if severity_text.startswith('P1'):
        return 'bg-red-500/20 text-red-300 border-red-500/20'
    if severity_text.startswith('P2'):
        return 'bg-amber-500/20 text-amber-300 border-amber-500/20'
    return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/20'


def fetch_rss_items(url: str):
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    context = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=30, context=context) as response:
        xml_bytes = response.read()
    root = ET.fromstring(xml_bytes)
    channel = root.find('channel')
    if channel is None:
        return []
    items = []
    for item in channel.findall('item'):
        raw_title = item.findtext('title', default='')
        link = item.findtext('link', default='')
        pub_date = item.findtext('pubDate', default='')
        headline, source = parse_google_news_title(raw_title)
        items.append({
            'headline': headline,
            'source': source,
            'link': clean_text(link),
            'published_at': parse_pub_date(pub_date),
        })
    return items


def build_dashboard_payload(items):
    risks, timeline = [], []
    for item in items[:MAX_RISKS]:
        severity_text, severity_color, status, status_color = classify_severity(item['headline'])
        risks.append({
            'title': item['headline'][:90],
            'severityText': severity_text,
            'severityColor': severity_color,
            'status': status,
            'statusColor': status_color,
            'timestamp': item['published_at'].replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
            'description': build_description(item['headline'], item['source']),
            'links': [{'label': item['source'], 'url': item['link']}],
        })
    for item in items[:MAX_TIMELINE]:
        severity_text, _, _, _ = classify_severity(item['headline'])
        timeline.append({
            'date': item['published_at'].strftime('%b %d'),
            'loc': item['source'],
            'event': item['headline'][:80],
            'impact': severity_text,
            'impactClass': build_impact_class(severity_text),
        })
    return {
        'lastUpdated': now_iso(),
        'sourceFeed': RSS_URL,
        'articleCount': len(items),
        'risks': risks,
        'timeline': timeline,
    }


def fallback_payload(error_message: str):
    return {
        'lastUpdated': now_iso(),
        'sourceFeed': RSS_URL,
        'articleCount': 0,
        'risks': [{
            'title': 'Intel feed temporarily unavailable',
            'severityText': 'P3 LOW',
            'severityColor': 'amber',
            'status': 'VERIFIED',
            'statusColor': 'emerald',
            'timestamp': now_iso(),
            'description': 'The updater could not fetch live RSS data, but the pipeline successfully generated data.json so the dashboard can load.',
            'links': [],
        }],
        'timeline': [{
            'date': datetime.now(timezone.utc).strftime('%b %d'),
            'loc': 'System',
            'event': 'Fallback dataset generated',
            'impact': clean_text(error_message)[:80] or 'Feed unavailable',
            'impactClass': 'bg-amber-500/20 text-amber-300 border-amber-500/20',
        }],
    }


def write_json(payload: dict, file_path: str):
    with open(file_path, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write('\n')


if __name__ == '__main__':
    try:
        items = fetch_rss_items(RSS_URL)
        payload = build_dashboard_payload(items)
        if not payload['risks'] and not payload['timeline']:
            payload = fallback_payload('No RSS items returned from feed')
        write_json(payload, OUTPUT_FILE)
        print(f'Successfully updated {OUTPUT_FILE} with {payload.get("articleCount", 0)} articles')
    except Exception as exc:
        payload = fallback_payload(str(exc))
        write_json(payload, OUTPUT_FILE)
        print(f'Warning: live fetch failed; wrote fallback {OUTPUT_FILE}. Error: {exc}')
``
