import sqlite3
import os
import json

DB_NAME = "memory.db"

# 初期化：必要テーブル（memories / dialogues）を作成
def initDatabase():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    try:
        # テーブル存在チェック
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memories'")
        if not c.fetchone():
            # 記憶テーブル
            c.execute("""
                CREATE TABLE memories (
                    memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    category TEXT DEFAULT 'uncategorized',
                    weight INTEGER DEFAULT 1,
                    target_user_id TEXT NOT NULL,
                    is_forgotten INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 応答ログテーブル
            c.execute("""
                CREATE TABLE dialogues (
                    dialogue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_user_id TEXT NOT NULL,
                    sender_user_id TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    is_ai_generated BOOLEAN NOT NULL,
                    text TEXT NOT NULL,
                    memory_refs TEXT,
                    prompt_version TEXT,
                    temperature REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            print("✅ memory.db initialized (Reply専用)")
        else:
            print("✅ memory.db already initialized")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# 記憶と対話ログを登録（1トランザクション）
def registerMemoryAndDialogue(
    user_id,
    message,
    content,
    category, 
    memory_refs=None,
    is_ai_generated=False,
    sender_user_id="self",
    message_type="input"
):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        # 記憶登録
        c.execute("""
            INSERT INTO memories (content, category, weight, target_user_id)
            VALUES (?, ?, ?, ?)
        """, (content, category, 1, user_id))
        memory_id = c.lastrowid

        # 応答ログ登録
        c.execute("""
            INSERT INTO dialogues (
                target_user_id, sender_user_id, message_type,
                is_ai_generated, text, memory_refs,
                prompt_version, temperature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            sender_user_id,
            message_type,
            is_ai_generated,
            message,
            json.dumps(memory_refs) if memory_refs else None,
            None,
            None
        ))

        conn.commit()
        print(f"✅ Memory + Dialogue recorded: memory_id={memory_id}")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# 指定カテゴリとユーザーIDで記憶を取得（GPT応答時に使用）
def getMemoriesByCategory(category, target_user_id, limit=10):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT memory_id, content
        FROM memories
        WHERE is_forgotten = 0
          AND category = ?
          AND target_user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (category, target_user_id, limit))
    result = c.fetchall()
    conn.close()
    return result

# 管理者確認用：全記憶の一覧を取得（任意使用）
def getAllMemories():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT memory_id, content, category, weight FROM memories WHERE is_forgotten = 0")
    results = c.fetchall()
    conn.close()
    return results

# 対象ユーザーの直近の対話ログを取得する関数（デフォルトで直近3件）
def getRecentDialogues(target_user_id, limit=3):
    # データベースへ接続
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 最新の対話ログを取得（降順で取得）
    cursor.execute("""
        SELECT text FROM dialogues
        WHERE target_user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (target_user_id, limit))

    # 結果をすべて取得
    rows = cursor.fetchall()
    conn.close()

    # 時系列順（古い→新しい）に並べ直して返す
    return [row[0] for row in reversed(rows)]

