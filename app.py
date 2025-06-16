from flask import Flask, request, abort
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage


from dotenv import load_dotenv
import os
import json

# 自作モジュール
from logic.db_utils import initDatabase, registerMemoryAndDialogue
from logic.chatgpt_logic import getChatGptReplyForReplying

# ログ設定
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# 環境変数読み込み
load_dotenv()

# 環境変数取得
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")
memory_target_user_id = os.getenv("MEMORY_TARGET_USER_ID")
target_role = os.getenv("TARGET_ROLE")

# 検証
if not memory_target_user_id:
    raise ValueError("MEMORY_TARGET_USER_ID is not set.")
if not channel_secret or not access_token:
    raise ValueError("LINE設定が未定義です")

# FlaskとLINE初期化
app = Flask(__name__)
handler = WebhookHandler(channel_secret)
messaging_api = MessagingApi(ApiClient(Configuration(access_token=access_token)))

# DB初期化
initDatabase()

@app.route("/ai_reply_webhook", methods=["POST"])
def ai_reply_webhook():
    signature = request.headers["X-Line-Signature"]
    body_text = request.get_data(as_text=True)
    body_json = request.get_json(force=True)

    events = body_json.get("events", [])
    if not events:
        print("⚠️ Warning: No events in body.")
        return "NO EVENT", 200

    try:
        handler.handle(body_text, signature)
    except Exception as e:
        print(f"[REPLY] Webhook Error: {e}")
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handleMessage(event):
    try:
        user_id = event.source.user_id
        message = event.message.text

        NG_WORDS = ["セフレ", "エロ", "性欲", "キスして", "付き合って", "いやらしい"]
        if any(ng in message.lower() for ng in NG_WORDS):
            reply_text = "この話題には応答できません。"
            reply = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
            messaging_api.reply_message(reply)
            return

        print(f"[REPLY] Received message from user_id: {user_id}")
        print(f"[REPLY] MEMORY_TARGET_USER_ID: {memory_target_user_id}")

        # ChatGPT応答を生成（カテゴリ分類＋記憶＋mission込み）
        gpt_result = getChatGptReplyForReplying(message, memory_target_user_id)
        reply_text = gpt_result["reply_text"]
        memory_refs = json.dumps(gpt_result["used_memory_ids"])

        # 応答ログを記録（user_id＝応答人格、sender_user_id＝実際の発話者）
        registerMemoryAndDialogue(
            user_id=memory_target_user_id,
            message=message,
            content=reply_text,
            category=gpt_result["category"],  # 応答側の記録分類
            memory_refs=memory_refs,
            is_ai_generated=True,
            sender_user_id=user_id,
            message_type="reply"
        )

        # LINEへ返信
        reply = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply_text)]
        )
        messaging_api.reply_message(reply)
        print("[REPLY] 応答完了 & 記録済み")

    except Exception as e:
        print(f"[REPLY] Handler Error: {e}")

if __name__ == '__main__':
    print("✅ initDatabase() を実行開始")
    initDatabase()
    print("✅ initDatabase() を完了")
    print(f"🌐 DEBUG: running Reply (接客応答専用モード)")
    app.run(debug=False, host='0.0.0.0', port=5003)
