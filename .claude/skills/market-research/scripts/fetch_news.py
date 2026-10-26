"""외신(FT·WSJ·Economist) 공개 RSS에서 최근 기사 제목·요약을 모은다.

로그인하지 않는다. 각 매체가 공개한 RSS만 읽으므로 본문 전체가 아니라 제목·1–2문장 요약·발행 시각·링크만 얻는다.
Barron's는 공개 RSS가 없어 제외한다.

사용:
    python3 -I fetch_news.py [--hours 72] [--out data/news/YYYY-MM-DD.json]
"""

import argparse
import datetime as dt
import email.utils
import html
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

FEEDS = {
    "FT": [
        "https://www.ft.com/rss/home/international",
        "https://www.ft.com/markets?format=rss",
        "https://www.ft.com/world?format=rss",
        "https://www.ft.com/technology?format=rss",
    ],
    "WSJ": [
        "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain",
        "https://feeds.content.dowjones.io/public/rss/RSSWorldNews",
        "https://feeds.content.dowjones.io/public/rss/RSSWSJD",
        "https://feeds.content.dowjones.io/public/rss/WSJcomUSBusiness",
        "https://feeds.content.dowjones.io/public/rss/RSSUSnews",
    ],
    "Economist": [
        "https://www.economist.com/finance-and-economics/rss.xml",
        "https://www.economist.com/business/rss.xml",
        "https://www.economist.com/united-states/rss.xml",
        "https://www.economist.com/asia/rss.xml",
        "https://www.economist.com/the-world-this-week/rss.xml",
    ],
}
ALLOWED = ("ft.com", "wsj.com", "economist.com")
KST = dt.timezone(dt.timedelta(hours=9))
UA = "market-research-rss/1.0 (personal RSS reader)"  # 기본 Python UA는 FT·Economist가 거부함


def fetch(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as resp:
                return resp.read()
        except Exception as e:  # 연결이 가끔 끊기므로 짧게 재시도
            if attempt == 2:
                print(f"[skip] {url}: {e}", file=sys.stderr)
                return None
            time.sleep(2 ** attempt)


def clean(text):
    text = re.sub(r"<[^>]+>", " ", html.unescape(text or ""))
    return re.sub(r"\s+", " ", text).strip()


def parse(source, raw, since):
    items = []
    for it in ET.fromstring(raw).iter("item"):
        link = (it.findtext("link") or "").strip()
        host = re.sub(r"^https?://([^/]+).*", r"\1", link)
        if not any(host == d or host.endswith("." + d) for d in ALLOWED):
            continue
        pub = it.findtext("pubDate")
        try:
            when = email.utils.parsedate_to_datetime(pub)
        except (TypeError, ValueError):
            continue
        if when < since:
            continue
        items.append({
            "source": source,
            "title": clean(it.findtext("title")),
            "summary": clean(it.findtext("description"))[:400],
            "published_kst": when.astimezone(KST).strftime("%Y-%m-%d %H:%M"),
            "link": link.split("?")[0],
        })
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=72)
    ap.add_argument("--out")
    args = ap.parse_args()

    now = dt.datetime.now(dt.timezone.utc)
    since = now - dt.timedelta(hours=args.hours)
    seen, items = set(), []
    for source, urls in FEEDS.items():
        for url in urls:
            raw = fetch(url)
            if not raw:
                continue
            for item in parse(source, raw, since):
                if item["link"] not in seen:
                    seen.add(item["link"])
                    items.append(item)
    items.sort(key=lambda x: x["published_kst"], reverse=True)

    out = Path(args.out or f"data/news/{now.astimezone(KST):%Y-%m-%d}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    counts = {s: sum(1 for i in items if i["source"] == s) for s in FEEDS}
    print(f"{len(items)}건 {counts} → {out}")


if __name__ == "__main__":
    main()
