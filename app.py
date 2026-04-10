from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage # 新增 ImageSendMessage
import openai
import os

app = Flask(__name__)

# --- 初始化參數 ---
openai.api_key = os.getenv('OPENAI_API_KEY')
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler1 = WebhookHandler(os.getenv('CHANNEL_SECRET'))

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
    global msg_counter
    user_text = event.message.text
    msg_counter += 1

    try:
        # --- 判斷：如果使用者說「畫圖」，就執行 DALL-E ---
        if user_text.startswith("畫圖"):
            # 取得「畫圖」後面的文字當作提示詞
            prompt_text = user_text.replace("畫圖", "").strip()
            if not prompt_text:
                prompt_text = "一張神秘的星空圖" # 預設提示詞

            response = openai.Image.create(
                prompt=prompt_text,
                n=1,
                size="1024x1024"
            )
            image_url = response['data'][0]['url']
            
            # 回傳圖片訊息
            line_bot_api.reply_message(
                event.reply_token,
                ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
            )

        # --- 否則：執行一般的占星師對話 ---
        else:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一位專業的占星師，說話優雅且富有禪意，回答時會加入一些星座相關的詞彙。"},
                    {"role": "user", "content": user_text}
                ],
                temperature=1,
            )
            ai_ret = response['choices'][0]['message']['content'].strip()
            ret = f"【第 {msg_counter} 則對話】\n{ai_ret}"
            
            line_bot_api.reply_message(
                event.reply_token, 
                TextSendMessage(text=ret)
            )
            
    except Exception as e:
        print(f"Error: {e}")
        line_bot_api.reply_message(
            event.reply_token, 
            TextSendMessage(text=f"發生錯誤：{str(e)}")
        )

if __name__ == '__main__':
    app.run()
