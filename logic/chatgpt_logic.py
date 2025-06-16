import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from logic.db_utils import getMemoriesByCategory, getRecentDialogues

# .env読み込み
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CATEGORY_CONFIG = {
    "感情": "心・精神",
    "健康": "健康",
    "趣味": "家庭・プライベート",
    "仕事": "社会・仕事",
    "お金": "経済・お金",
    "教養": "教養・知識",
    "導入": "導入",
    "サポート": "サポート"
}
CATEGORY_LABELS = list(CATEGORY_CONFIG.keys())

def loadMissionPolicyJson():
    file_path = os.getenv("MISSION_FILE_PATH")
    if not file_path or not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# カテゴリ分類
def getCategoryByGpt(message):
    categories = "」「".join(CATEGORY_LABELS)
    prompt = (
        f"以下の発言を最も適切なカテゴリで分類してください。\n"
        f"候補カテゴリ：{categories}\n"
        f"出力は1単語のカテゴリ名のみ。説明は禁止。\n"
        f"発言：「{message}」"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "カテゴリ分類のみを行ってください"},
                {"role": "user", "content": prompt}
            ]
        )
        category = response.choices[0].message.content.strip()
        return CATEGORY_CONFIG.get(category, "uncategorized")
    except Exception as e:
        print("[分類エラー]", e)
        return "uncategorized"

# プロンプト生成（履歴込み）
def buildPrompt(memories, user_message, mission_data, category, history):
    memory_section = "\n".join(f"- {m}" for m in memories)
    history_section = "\n".join(f"- {h}" for h in history)
    service_name = mission_data.get("service_name", "接客AI")
    tone = mission_data.get("tone", "丁寧な接客対応")
    values = "\n".join(f"- {v}" for v in mission_data.get("core_values", []))
    prohibitions = "\n".join(f"- {p}" for p in mission_data.get("prohibited_responses", []))
    category_policy = "\n".join(
        f"- {p}" for p in mission_data.get("categories", {}).get(category, [])
    )

    prompt = f"""
あなたは「{service_name}」という商用接客AIです。

【話し方】
- 一貫して「{tone}」で対応してください。

【接客方針】
{values}

【禁止事項】
{prohibitions}

【このカテゴリで特に重視すべき方針】
{category_policy}

【最近の対話履歴】
{history_section}

【これまでの関連情報】
{memory_section}

【ユーザーの質問】
「{user_message}」

上記に対して、内容が正確で誤解のない丁寧な文章を生成してください。
語尾は「です・ます調」とし、文脈に応じた自然な応答を生成してください。
特に、最近の対話履歴や関連記憶に触れることで、相手に寄り添った応答を意識してください。
応答は80文字以内に抑えてください。短く、簡潔にまとめてください。
"""
    return prompt.strip()

def callChatGptWithPrompt(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "あなたは商用接客Botです。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=100
    )
    return response.choices[0].message.content.strip()

# 応答生成メイン関数
def getChatGptReplyForReplying(user_message, target_user_id):
    category = getCategoryByGpt(user_message)
    print(f"[分類カテゴリ]: {category}")

    # 関連記憶の取得
    memory_items = getMemoriesByCategory(category, target_user_id)
    memory_ids = [m[0] for m in memory_items]
    memory_texts = [m[1] for m in memory_items]

    print(f"🧠 使用記憶ID: {memory_ids}")
    print(f"🧠 記憶数: {len(memory_texts)}件")
    print(f"🧠 カテゴリ: {category}")

    # ミッション情報の取得
    mission_data = loadMissionPolicyJson()

    # 対話履歴の取得（時系列順）
    dialogue_history = getRecentDialogues(target_user_id)

    # プロンプト構築
    prompt = buildPrompt(memory_texts, user_message, mission_data, category, dialogue_history)
    print(f"[履歴確認] 対話履歴: {dialogue_history}") 

    # GPT呼び出し
    reply_text = callChatGptWithPrompt(prompt)

    return {
        "reply_text": reply_text,
        "used_memory_ids": memory_ids,
        "category": category
    }
