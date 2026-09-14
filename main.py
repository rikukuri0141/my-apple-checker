import json
import os
import re
import requests
from bs4 import BeautifulSoup

LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
USER_ID = os.environ.get("LINE_USER_ID")
CACHE_FILE = "stock_cache.json"

# Apple認定整備済製品（iPhoneカテゴリ）のURL
URL = "https://www.apple.com/jp/shop/refurbished/iphone"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# 監視したい機種の正規表現パターン（16e または 17e に一致）
TARGET_PATTERN = re.compile(r"iphone\s*(16e|17e)", re.IGNORECASE)


def is_target_model(title: str) -> bool:
  """商品名が iPhone 16e または 17e かどうかを判定"""
  return bool(TARGET_PATTERN.search(title))


def get_current_stock():
  res = requests.get(URL, headers=HEADERS, timeout=15)
  res.raise_for_status()
  soup = BeautifulSoup(res.text, "html.parser")
  items = {}
  for a in soup.select("h3 a"):
    title = a.get_text(strip=True)
    link = "https://www.apple.com" + a.get("href", "")
    items[title] = link
  return items


def send_line(message):
  if not LINE_ACCESS_TOKEN or not USER_ID:
    print("LINE credentials not set.")
    return
  url = "https://api.line.me/v2/bot/message/push"
  headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
  }
  data = {"to": USER_ID, "messages": [{"type": "text", "text": message}]}
  requests.post(url, headers=headers, json=data, timeout=10)


def main():
  current = get_current_stock()

  # 前回取得したキャッシュ
  if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
      previous = json.load(f)
  else:
    previous = {}

  # 全体の中から新しく追加・再入荷された商品を抽出
  new_items = {k: v for k, v in current.items() if k not in previous}

  # そのうち「iPhone 16e または 17e」のみを抽出
  matched_items = {k: v for k, v in new_items.items() if is_target_model(k)}

  if matched_items:
    print(f"Target items found: {len(matched_items)}")
    text = "【入荷速報】iPhone 16e / 17e 整備済製品！\n"
    for title, link in matched_items.items():
      text += f"\n・{title}\n{link}\n"
    send_line(text)
  else:
    print("No target items found (or no changes).")

  # 次回判定用に現在のiPhone全在庫をキャッシュへ保存
  with open(CACHE_FILE, "w", encoding="utf-8") as f:
    json.dump(current, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
  main()
