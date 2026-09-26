import json
import os
import re
import requests
from bs4 import BeautifulSoup

LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
CACHE_FILE = "stock_cache.json"

URL = "https://www.apple.com/jp/shop/refurbished/iphone"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja-JP,ja;q=0.9",
}

# 判定パターン
PATTERN_15_16_128GB = re.compile(r"iphone\s*(15)\s+128gb", re.IGNORECASE)
PATTERN_E_SERIES = re.compile(r"iphone\s*(16e|17e)", re.IGNORECASE)


def is_target_model(title: str) -> bool:
  # Pro, Pro Max, Plus などの派生モデルを除外
  if re.search(r"\b(pro|plus|max)\b", title, re.IGNORECASE):
    return False

  # iPhone 15/16 (128GB)
  if PATTERN_15_16_128GB.search(title):
    return True

  # iPhone 16e/17e (全容量)
  if PATTERN_E_SERIES.search(title):
    return True

  return False


def get_current_stock():
  try:
    res = requests.get(URL, headers=HEADERS, timeout=15)
    res.raise_for_status()
  except Exception as e:
    print(f"Fetch failed: {e}")
    return {}

  soup = BeautifulSoup(res.text, "html.parser")
  script = soup.find("script", id="__NEXT_DATA__")
  items = {}

  # 埋め込みJSONが存在する場合はJSONから正確に抽出
  if script and script.string:
    try:
      data = json.loads(script.string)
      tiles = (
          data.get("props", {})
          .get("pageProps", {})
          .get("tiles", {})
          .get("items", [])
      )
      for item in tiles:
        title = item.get("title", "")
        url = item.get("link", {}).get("url", "")
        if title:
          full_url = (
              url
              if url.startswith("http")
              else f"https://www.apple.com{url}"
          )
          items[title] = full_url
    except Exception as e:
      print(f"JSON parse error: {e}")

  # フォールバック (HTMLリンク解析)
  if not items:
    for a in soup.find_all("a", href=True):
      href = a["href"]
      if "/shop/product/" in href:
        title = a.get_text(strip=True)
        if "iPhone" in title and "[整備済製品]" in title:
          full_url = (
              href
              if href.startswith("http")
              else f"https://www.apple.com{href}"
          )
          items[title] = full_url

  return items


def send_broadcast(message):
  if not LINE_ACCESS_TOKEN:
    print("Error: LINE_ACCESS_TOKEN is not set.")
    return

  url = "https://api.line.me/v2/bot/message/broadcast"
  headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
  }
  data = {"messages": [{"type": "text", "text": message}]}
  try:
    res = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"LINE Broadcast Response: {res.status_code}")
  except Exception as e:
    print(f"LINE Broadcast error: {e}")


def main():
  current = get_current_stock()
  print(f"Total refurbished iPhones currently in store: {len(current)}")

  # キャッシュ（前回の在庫一覧）の読み込み
  if os.path.exists(CACHE_FILE):
    try:
      with open(CACHE_FILE, "r", encoding="utf-8") as f:
        previous = json.load(f)
    except Exception:
      previous = {}
  else:
    previous = {}

  # 新規追加された商品
  new_items = {k: v for k, v in current.items() if k not in previous}
  matched_items = {k: v for k, v in new_items.items() if is_target_model(k)}

  if matched_items:
    print(f"Target items detected: {len(matched_items)}")
    text = "【入荷速報】対象のiPhone整備済製品が入荷しました！\n"
    for title, link in list(matched_items.items())[:5]:
      text += f"\n・{title}\n{link}\n"
    send_broadcast(text)
  else:
    print("No new target items detected.")

  # 最新在庫を次回判定用にキャッシュへ保存
  if current:
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
      json.dump(current, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
  main()

