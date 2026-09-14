import os
import requests

LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
USER_ID = os.environ.get("LINE_USER_ID")


def send_line(message):
  if not LINE_ACCESS_TOKEN:
    print("Error: LINE_ACCESS_TOKEN is not set.")
    return
  if not USER_ID:
    print("Error: LINE_USER_ID is not set.")
    return

  url = "https://api.line.me/v2/bot/message/push"
  headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
  }
  data = {"to": USER_ID, "messages": [{"type": "text", "text": message}]}

  res = requests.post(url, headers=headers, json=data, timeout=10)
  print(f"LINE API Response Code: {res.status_code}")
  print(f"LINE API Response Body: {res.text}")


if __name__ == "__main__":
  print("Sending test message to LINE...")
  send_line("【接続テスト】GitHub Actionsからの通知テストです！")

