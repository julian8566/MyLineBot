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

# -------------------------------------------------------------------
# 請填入你的 LINE 與 OpenAI 金鑰
# -------------------------------------------------------------------
CHANNEL_SECRET = 'b8bcfbf891b8e2252735533fcc615b6a'
CHANNEL_ACCESS_TOKEN = 'JAcYi/RkE+nRplV+a0DrvHG5qTfQa0+4jseXHpeJ4mnRikH38MvTDxcgDjj9KUsvaAIrM3XVnDse2v8IqqEzxJVs3+8FFDBOBSyWY71ilvT9VKTDn31E4s20GlMgJ00kC6/dnqAqFuAL4nB4y4+cRgdB04t89/1O/w1cDnyilFU='
OPENAI_API_KEY = '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'

# 初始化 LINE 與 OpenAI
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    ai_reply = ""

    # 讓 OpenAI GPT 來思考並回答使用者傳來的訊息
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 使用快速且聰明的輕量模型
            messages=[
                {"role": "system", "content": "你是一個貼心、幽默且專業的 LINE AI 助理。"},
                {"role": "user", "content": user_message}
            ]
        )
        ai_reply = response.choices[0].message.content
    except Exception as e:
        ai_reply = f"哎呀，我的 AI 大腦暫時連線失敗了：{str(e)}"

    # 將 AI 生成的回覆透過 LINE 傳回給使用者
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=ai_reply)]
            )
        )

if __name__ == "__main__":
    app.run(port=5000)