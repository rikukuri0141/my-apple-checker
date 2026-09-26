import os
import re
import requests

LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
# 変更前: API_URL = "https://www.apple.com/jp/shop/refurbished/iphone/tiles"
# 変更後: ストアの標準商品一覧APIを使用
API_URL = "https://www.apple.com/jp/shop/refurbished/iphone"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "ja-JP,ja;q=0.9",
}

# 判定パターン
PATTERN_15_16_128GB = re.compile(r"iphone\s*(15|16)\s+128gb", re.IGNORECASE)
PATTERN_E_SERIES = re.compile(r"iphone\s*(16e|17e)", re.IGNORECASE)


def is_target_model(title: str) -> bool:
  # Pro, Pro Max, Plus などの除外
  if re.search(r"\b(pro|plus|max)\b", title, re.IGNORECASE):
    return False

  # iPhone 15/16 (128GB)
  if PATTERN_15_16_128GB.search(title):
    return True

  # iPhone 16e/17e
  if PATTERN_E_SERIES.search(title):
    return True

  return False


# ==========================================
# テスト1: 判定ロジックの単体テスト
# ==========================================
def test_filter_logic():
  print("--- [テスト1] 商品名判定ロジックの検証 ---")
  test_cases = [
      ("iPhone 15 128GB - ブルー [整備済製品]", True),
      ("iPhone 15 256GB - ブラック [整備済製品]", False),  # 容量違い
      ("iPhone 15 Pro 128GB - ナチュラルチタニウム [整備済製品]", False),  # Pro
      ("iPhone 15 Plus 128GB - ピンク [整備済製品]", False),  # Plus
      ("iPhone 16 128GB - ホワイト [整備済製品]", True),
      ("iPhone 16 Pro Max 256GB - デザートチタニウム [整備済製品]", False),  # Pro Max
      ("iPhone 16e 128GB - ブラック [整備済製品]", True),
      ("iPhone 16e 256GB - ホワイト [整備済製品]", True),  # eシリーズは容量不問
      ("iPhone 17e 128GB - ブルー [整備済製品]", True),
      ("iPhone 14 128GB - スターライト [整備済製品]", False),  # 対象外世代
  ]

  all_passed = True
  for title, expected in test_cases:
    result = is_target_model(title)
    status = "OK" if result == expected else "NG"
    if status == "NG":
      all_passed = False
    print(f"[{status}] 判定結果: {result:<5} | 想定: {expected:<5} | {title}")

  if all_passed:
    print(">> テスト1完了: すべての判定が意図通りに動作しました！\n")
  else:
    print(">> テスト1失敗: 一部の判定に食い違いがあります。\n")


# ==========================================
# テスト2: 実際のApple APIからのデータ取得テスト
# ==========================================
def test_fetch_apple_api():
  print("--- [テスト2] Apple公式APIへの接続検証 ---")
  try:
    # ブラウザと同じ要求ヘッダーを付与
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "ja-JP,ja;q=0.9",
    }
    res = requests.get(API_URL, headers=headers, timeout=15)
    print(f"HTTP ステータスコード: {res.status_code}")
    res.raise_for_status()

    # ページ内の埋め込みJSONデータ (__NEXT_DATA__ または RefurbishedData) を抽出
    import json
    import re
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(res.text, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")

    products = []
    if script and script.string:
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
          products.append((title, full_url))
    else:
      # フォールバック: 通常のHTMLリンクから抽出
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
            products.append((title, full_url))

    # 重複除去
    unique_products = list({p[0]: p for p in products}.values())
    print(f"取得できた整備済iPhoneの総数: {len(unique_products)}件")

    matched = []
    for title, link in unique_products:
      if is_target_model(title):
        matched.append((title, link))

    if matched:
      print(f">> 現在、条件に合致する在庫があります ({len(matched)}件):")
      for t, l in matched:
        print(f"  ・{t}\n    {l}")
    else:
      print(">> 現在、指定条件（15/16 128GB, 16e, 17e）に合う在庫はありません。")

    print(">> テスト2完了: 正常にストア情報を解析できました！\n")

  except Exception as e:
    print(f">> テスト2失敗: {e}\n")


# ==========================================
# テスト3: LINE通知の送信テスト (任意)
# ==========================================
def test_send_line():
  print("--- [テスト3] LINE送信テスト ---")
  if not LINE_ACCESS_TOKEN:
    print("LINE_ACCESS_TOKEN が環境変数に設定されていません。スキップします。\n")
    return

  confirm = input("実際にLINE通知を1通テスト送信しますか？ (y/n): ")
  if confirm.lower() != "y":
    print("LINE送信テストをスキップしました。\n")
    return

  url = "https://api.line.me/v2/bot/message/broadcast"
  headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
  }
  data = {
      "messages": [
          {
              "type": "text",
              "text": (
                  "【テスト通知】\n整備済iPhone監視システムの疎通テストです。\n正常に通知が届いています。"
              ),
          }
      ]
  }

  res = requests.post(url, headers=headers, json=data, timeout=10)
  print(f"LINE API レスポンス: {res.status_code}")
  if res.status_code == 200:
    print(">> テスト3完了: LINEにテストメッセージが届いているか確認してください。\n")
  else:
    print(f">> テスト3失敗: {res.text}\n")


if __name__ == "__main__":
  test_filter_logic()
  test_fetch_apple_api()
  test_send_line()
