from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os

app = Flask(__name__)

# --- 初始化參數 ---
openai.api_key = os.getenv('OPENAI_API_KEY')
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler1 = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# 1. 初始化計數器 (全域變數)
msg_counter = 0

@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler1.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler1.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global msg_counter # 宣告使用全域變數
    text1 = event.message.text
    
    # 2. 每次收到訊息，計數器加 1
    msg_counter += 1

    try:
        # 3. 修改個性：在 messages 中加入 system role
        response = openai.ChatCompletion.create(
            model="gpt-5-nano"", # 註：目前官方尚未開放 gpt-5，建議先用 3.5 或 4
            messages=[
                {"role": "system", "content": "你是一位專業的占星師，說話優雅且富有禪意，回答時會加入一些星座相關的詞彙。"},
                {"role": "user", "content": text1}
            ],
            temperature=1,
        )
        
        ai_ret = response['choices'][0]['message']['content'].strip()
        
        # 4. 將計數器資訊放入回覆訊息中
        ret = f"【第 {msg_counter} 則對話】\n{ai_ret}"
        
    except Exception as e:
        print(f"Error: {e}")
        ret = '發生錯誤，請稍後再試！'

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ret))

if __name__ == '__main__':
    app.run()
