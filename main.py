import os
import requests

LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")

def send_broadcast(message):
    if not LINE_ACCESS_TOKEN:
        print("Error: LINE_ACCESS_TOKEN is not set.")
        return

    # 一斉配信用エンドポイント (Broadcast API)
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    data = {
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    
    res = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"LINE Broadcast Response Code: {res.status_code}")
    print(f"Response Body: {res.text}")

if __name__ == "__main__":
    print("Sending broadcast test message to all followers...")
    send_broadcast("【全体配信テスト】この公式アカウントを友だち追加している全員に届いています！")

