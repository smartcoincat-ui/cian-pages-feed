#!/usr/bin/env python3
import json, re, os, hashlib
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

SEARCH_URL = os.getenv("SEARCH_URL", "https://www.cian.ru/kupit-mnogkomnatnuyu-kvartiru/")
LIMIT = int(os.getenv("LIMIT", "10"))
OUT = "docs/data.json"
IMG_DIR = "docs/images"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
}


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def cache_image(url: str, idx: int) -> str:
    if not url:
        return ""
    try:
        ext = ".jpg"
        p = urlparse(url)
        tail = p.path.split("/")[-1]
        if "." in tail:
            ext = "." + tail.split(".")[-1].split("?")[0]
            if len(ext) > 5:
                ext = ".jpg"
        name = hashlib.md5(url.encode("utf-8")).hexdigest()[:12] + f"_{idx}" + ext
        local_path = os.path.join(IMG_DIR, name)
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(r.content)
        return f"images/{name}"
    except Exception:
        return ""


res = requests.get(SEARCH_URL, headers=headers, timeout=30)
res.raise_for_status()
soup = BeautifulSoup(res.text, "html.parser")
os.makedirs(IMG_DIR, exist_ok=True)

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
    text = clean(card_root.get_text(" ", strip=True) if card_root else a.get_text(" ", strip=True))

    img = ""
    if card_root:
        img_tag = card_root.find("img")
        if img_tag:
            img = img_tag.get("src") or img_tag.get("data-src") or ""

    price_m = re.search(r"(\d[\d\s]{3,})\s*₽", text)
    area_m = re.search(r"(\d+[\.,]?\d*)\s*м²", text)
    rooms_m = re.search(r"([4567])\-комн\.", text)
    floor_m = re.search(r"(\d+)\/(\d+)\s*этаж", text)
    metro_m = re.search(r"м\.\s*([^,]+)", text)
    bath_m = re.search(r"(\d+)\s*сануз", text)

    tags = []
    if re.search(r"дизайнер|дизайн", text, re.I):
        tags.append("Дизайнерский ремонт")
    if re.search(r"евроремонт", text, re.I):
        tags.append("Евроремонт")
    if re.search(r"с мебелью", text, re.I):
        tags.append("С мебелью")
    if re.search(r"пентхаус", text, re.I):
        tags.append("Пентхаус")

    local_img = cache_image(img, len(cards) + 1)

    cards.append({
        "id": item_id,
        "title": clean(a.get_text(" ", strip=True))[:120] or text[:120],
        "price": int(price_m.group(1).replace(" ", "")) if price_m else None,
        "price_text": f"{price_m.group(1)} ₽" if price_m else "",
        "area": float(area_m.group(1).replace(",", ".")) if area_m else None,
        "area_text": f"{area_m.group(1)} м²" if area_m else "",
        "rooms": int(rooms_m.group(1)) if rooms_m else None,
        "floor": int(floor_m.group(1)) if floor_m else None,
        "floors_total": int(floor_m.group(2)) if floor_m else None,
        "metro": clean(metro_m.group(1)) if metro_m else "",
        "bathrooms": int(bath_m.group(1)) if bath_m else None,
        "tags": tags,
        "url": href.split("?")[0],
        "image": local_img or img,
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
