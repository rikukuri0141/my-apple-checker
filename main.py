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

# 【テスト用】15、16、16e、17e を対象
TARGET_PATTERN = re.compile(r"iphone\s*(15|16|17)", re.IGNORECASE)


def is_target_model(title: str) -> bool:
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

  # 取得した全商品名を出力して確認
  for title in current.keys():
    print(f"Found: {title}")

  # キャッシュ（前回の在庫一覧）の読み込み
  if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
      previous = json.load(f)
  else:
    previous = {}

  # 【テスト用】差分判定をスキップし、現在ストアにある全商品から対象を抽出
  matched_items = {k: v for k, v in current.items() if is_target_model(k)}

  if matched_items:
    print(f"Target items detected: {len(matched_items)}")
    text = "【入荷速報テスト】iPhone 整備済製品！\n"
    for title, link in list(matched_items.items())[:5]:  # 最大5件送信
      text += f"\n・{title}\n{link}\n"
    send_line(text)
  else:
    print("No target items matched pattern.")

  # 最新在庫をキャッシュへ保存
  with open(CACHE_FILE, "w", encoding="utf-8") as f:
    json.dump(current, f, ensure_ascii=False, indent=2)


# ★これが抜けていたため実行されていませんでした
if __name__ == "__main__":
  main()
