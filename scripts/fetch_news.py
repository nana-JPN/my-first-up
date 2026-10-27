#!/usr/bin/env python3
"""Fetch RSS / Atom / RDF feeds listed in feeds.json and write news.json.

Standard library only, so it runs on GitHub Actions without pip install.

Usage:
    python scripts/fetch_news.py [output_path]
"""

import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
FEEDS_FILE = HERE / "feeds.json"
DEFAULT_OUTPUT = HERE.parent / "site" / "news.json"

MAX_PER_FEED = 15
MAX_AGE = timedelta(days=4)
TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (compatible; it-news-dashboard/1.0)"

# Articles from non-AI feeds whose title matches this are also shown in the AI column.
AI_KEYWORDS = re.compile(
    r"\bAI\b|生成AI|人工知能|LLM|ChatGPT|GPT-?\d|OpenAI|Claude|Anthropic|Gemini|"
    r"Copilot|機械学習|深層学習|ディープラーニング|Llama|Mistral|エージェント|\bagents?\b",
    re.IGNORECASE,
)

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "rss1": "http://purl.org/rss/1.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}


def text(el, path):
    if el is None:
        return ""
    found = el.find(path, NS)
    if found is None or found.text is None:
        return ""
    return found.text.strip()


def parse_date(value):
    if not value:
        return None
    value = value.strip()
    try:
        dt = parsedate_to_datetime(value)  # RFC 822 (RSS 2.0)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))  # ISO 8601 (Atom / dc:date)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def clean_summary(raw, limit=120):
    s = re.sub(r"<[^>]+>", " ", raw or "")
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= limit else s[: limit - 1] + "…"


def parse_feed(xml_bytes):
    """Return a list of {title, link, published, summary} from RSS 2.0, Atom or RSS 1.0 (RDF)."""
    root = ET.fromstring(xml_bytes)
    items = []

    if root.tag == f"{{{NS['atom']}}}feed":
        for e in root.findall("atom:entry", NS):
            link = ""
            for l in e.findall("atom:link", NS):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
                    break
            items.append({
                "title": text(e, "atom:title"),
                "link": link,
                "published": text(e, "atom:published") or text(e, "atom:updated"),
                "summary": text(e, "atom:summary") or text(e, "atom:content"),
            })
    elif root.tag.endswith("RDF"):
        for e in root.findall("rss1:item", NS):
            items.append({
                "title": text(e, "rss1:title"),
                "link": text(e, "rss1:link"),
                "published": text(e, "dc:date"),
                "summary": text(e, "rss1:description"),
            })
    else:
        for e in root.iter("item"):
            items.append({
                "title": text(e, "title"),
                "link": text(e, "link"),
                "published": text(e, "pubDate") or text(e, "dc:date"),
                "summary": text(e, "description") or text(e, "content:encoded"),
            })
    return items


def fetch(feed):
    req = Request(feed["url"], headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=TIMEOUT) as res:
        return res.read()


def collect(feed, now):
    try:
        raw_items = parse_feed(fetch(feed))
    except Exception as exc:  # one broken feed must not stop the others
        print(f"[skip] {feed['name']}: {exc}", file=sys.stderr)
        return [], False

    out = []
    for it in raw_items:
        dt = parse_date(it["published"])
        if not it["title"] or not it["link"]:
            continue
        if dt and now - dt > MAX_AGE:
            continue
        title = html.unescape(it["title"])
        out.append({
            "title": title,
            "link": it["link"],
            "source": feed["name"],
            "category": feed["category"],
            "ai": feed["category"] == "ai" or bool(AI_KEYWORDS.search(title)),
            "published": dt.isoformat() if dt else None,
            "summary": clean_summary(it["summary"]),
        })
        if len(out) >= MAX_PER_FEED:
            break
    print(f"[ok]   {feed['name']}: {len(out)} items", file=sys.stderr)
    return out, True


def build(feeds, now=None):
    now = now or datetime.now(timezone.utc)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda f: collect(f, now), feeds))

    seen, items = set(), []
    for feed_items, _ in results:
        for it in feed_items:
            if it["link"] in seen:
                continue
            seen.add(it["link"])
            items.append(it)
    # Newest first; undated items go last.
    items.sort(key=lambda x: x["published"] or "", reverse=True)

    return {
        "generated_at": now.isoformat(),
        "sources": [
            {"name": f["name"], "category": f["category"], "ok": ok}
            for f, (_, ok) in zip(feeds, results)
        ],
        "items": items,
    }


def main():
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    feeds = json.loads(FEEDS_FILE.read_text(encoding="utf-8"))
    data = build(feeds)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = sum(s["ok"] for s in data["sources"])
    print(f"wrote {len(data['items'])} items from {ok}/{len(feeds)} feeds -> {output}", file=sys.stderr)
    if ok == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
