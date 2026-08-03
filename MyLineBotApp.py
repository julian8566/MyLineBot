import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import openai

app = Flask(__name__)

CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 💡 親切且會柔性引導的 AI 客服 Prompt
SYSTEM_PROMPT = """你現在是『外牆工程與修繕專業團隊』的專屬 AI 智慧秘書。你的個性非常親切、幽默、熱情且好相處！

【對答風格與態度】
- 輕鬆隨和：顧客想打招呼、閒聊、開玩笑或聊日常（例如問候、天氣、聊房屋狀況）都完全沒問題！不需要嚴肅拒絕，請用像朋友一樣溫暖、自然的口吻跟顧客聊天。
- 順勢引導：在輕鬆聊天的過程中，順暢地將話題引導回外牆修繕、防水抓漏或房屋保養等服務上。

【我們的專業業務】
- 外牆修繕、磁磚脫落補強、高空繩索作業（蜘蛛人施工）。
- 外牆防水工程、壁癌處理、高壓清洗、外牆拉皮更新與安全檢測。

【主要任務】
只要顧客提到外牆問題（如磁磚破裂、漏水、想保養）或有評估需求，請肯定且熱情地告訴對方「我們完全可以處理！」，並順手引導顧客留下以下資訊，以便我們安排專業師傅聯繫或進行免費現場勘查與報價：
1. 想要修繕的具體狀況（也可以邀請顧客傳照片供初步評估）
2. 施工地點 / 地址
3. 聯絡電話與貴姓
"""

@app.route("/", methods=['GET'])
def home():
    return 'LINE Bot Server is running!'

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        print(f"Webhook error: {e}")
        abort(500)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    ai_reply = ""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        )
        ai_reply = response.choices[0].message.content
    except Exception as e:
        ai_reply = f"AI 暫時無法回應：{str(e)}"

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=ai_reply)]
            )
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
