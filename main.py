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

  # 【テスト用】差分判定を一旦スキップし、現在ストアにある全商品から対象を抽出
  # （本番に戻すときは new_items.items() に戻します）
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

