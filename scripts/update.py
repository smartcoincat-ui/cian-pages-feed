#!/usr/bin/env python3
import json, re, os
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

SEARCH_URL = os.getenv("SEARCH_URL", "https://www.cian.ru/kupit-mnogkomnatnuyu-kvartiru/")
LIMIT = int(os.getenv("LIMIT", "10"))
OUT = "docs/data.json"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
}

res = requests.get(SEARCH_URL, headers=headers, timeout=30)
res.raise_for_status()
soup = BeautifulSoup(res.text, "html.parser")

cards = []
for a in soup.select('a[href*="/sale/flat/"]'):
    href = a.get("href")
    if not href:
        continue
    if href.startswith("/"):
        href = "https://www.cian.ru" + href
    m = re.search(r"/sale/flat/(\d+)/", href)
    if not m:
        continue
    item_id = m.group(1)
    if any(x["id"] == item_id for x in cards):
        continue

    card_root = a.find_parent("article") or a.parent
    text = " ".join((card_root.get_text(" ", strip=True) if card_root else a.get_text(" ", strip=True)).split())

    img = None
    if card_root:
        img_tag = card_root.find("img")
        if img_tag:
            img = img_tag.get("src") or img_tag.get("data-src")

    price_match = re.search(r"([\d\s]{2,}₽)", text)
    sqm_match = re.search(r"(\d+[\s\d]*[\.,]?\d*\s*м²)", text)

    cards.append({
        "id": item_id,
        "title": text[:140],
        "price": price_match.group(1) if price_match else "",
        "area": sqm_match.group(1) if sqm_match else "",
        "url": href.split("?")[0],
        "image": img,
    })

    if len(cards) >= LIMIT:
        break

payload = {
    "source_url": SEARCH_URL,
    "count": len(cards),
    "items": cards,
}

os.makedirs("docs", exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print(f"Saved {len(cards)} items to {OUT}")
