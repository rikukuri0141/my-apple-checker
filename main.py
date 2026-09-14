import json
import os
import re
import requests
from bs4 import BeautifulSoup

LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
USER_ID = os.environ.get("LINE_USER_ID")
CACHE_FILE = "stock_cache.json"

URL = "https://www.apple.com/jp/shop/refurbished/iphone"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9",
}

# 監視対象: iPhone 16e または 17e
TARGET_PATTERN = re.compile(r"iphone\s*(16e|17e)", re.IGNORECASE)


def is_target_model(title: str) -> bool:
  """商品名が iPhone 16e または 17e かどうかを判定"""
  return bool(TARGET_PATTERN.search(title))


def get_current_stock():
  res = requests.get(URL, headers=HEADERS, timeout=15)
  res.raise_for_status()
  soup = BeautifulSoup(res.text, "html.parser")
  items = {}

  for a in soup.find_all("a", href=True):
    href = a["href"]
    if "/shop/product/" in href:
      text = a.get_text(strip=True)
      if "iPhone" in text and "[整備済製品]" in text:
        link = href if href.startswith("http") else "https://www.apple.com" + href
        items[text] = link

  return items


def send_line(message):
  url = "https://api.line.me/v2/bot/message/push"
  headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
  }
  data = {"to": USER_ID, "messages": [{"type": "text", "text": message}]}
  res = requests.post(url, headers=headers, json=data, timeout=10)
  print(f"LINE API Response: {res.status_code}")


def main():
  current = get_current_stock()
  print(f"Total refurbished iPhones currently in store: {len(current)}")

  # キャッシュ（前回の在庫一覧）の読み込み
  if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
      previous = json.load(f)
  else:
    previous = {}

  # 前回の状態と比較して新規・再入荷した商品のみを抽出
  new_items = {k: v for k, v in current.items() if k not in previous}

  # そのうち「iPhone 16e または 17e」のみに絞り込み
  matched_items = {k: v for k, v in new_items.items() if is_target_model(k)}

  if matched_items:
    print(f"Target items detected: {len(matched_items)}")
    text = "【入荷速報】iPhone 16e / 17e 整備済製品！\n"
    for title, link in list(matched_items.items())[:5]:  # 送信数制限
      text += f"\n・{title}\n{link}\n"
    send_line(text)
  else:
    print("No new target items (16e/17e) detected.")

  # 次回判定用に最新在庫をキャッシュへ保存
  with open(CACHE_FILE, "w", encoding="utf-8") as f:
    json.dump(current, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
  main()

