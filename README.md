---

# 🤖 Reply – 対話に特化したパーソナライズ応答AI

「あなたとの対話を記憶し、次の会話に活かすAI」

---

## 💡 Replyとは？

`Reply`は、ユーザーとの会話履歴を記憶し、次回以降の応答時にその履歴を活用するシンプルな対話型AIです。Phase分岐や人格モードは存在せず、常にリアルタイムの対話ログと記憶データに基づいて応答します。

## 🏗️ システム構成

* `app.py`：FlaskベースのWebhookエンドポイントを提供
* `chatgpt_logic.py`：OpenAI APIへの問い合わせロジック
* `db_utils.py`：記憶データと対話ログの保存／取得処理（SQLite）
* `mission_policy.json`：システムの初期方針や制約定義

## 📦 セットアップ手順

1. **仮想環境の作成と有効化**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **依存ライブラリのインストール**

   ```bash
   pip install -r requirements.txt
   ```

3. **環境変数の設定（`.env`ファイル）**

   ```
   OPENAI_API_KEY=sk-xxxx
   ```

4. **データベースの初期化**

   ```bash
   python
   >>> from db_utils import initDatabase
   >>> initDatabase()
   ```

5. **Flaskアプリの起動**

   ```bash
   python app.py
   ```

## 🧠 主な機能

| 機能       | 説明                                  |
| -------- | ----------------------------------- |
| 記憶登録     | ユーザー発言内容を `memories` テーブルに保存        |
| 応答ログ保存   | AI・ユーザー発言を `dialogues` テーブルに記録      |
| 応答時の記憶参照 | ユーザーID + カテゴリに基づき、過去の関連記憶を最大10件まで取得 |
| 対話文脈保持   | 直近の対話ログ3件を抽出し、OpenAIへのコンテキストに使用     |

## 🗃️ テーブル構成（SQLite）

### memories

| カラム名             | 説明        |
| ---------------- | --------- |
| memory\_id       | 主キー       |
| content          | 記憶したテキスト  |
| category         | カテゴリ      |
| weight           | 重み付け（未使用） |
| target\_user\_id | 記憶対象のユーザー |
| is\_forgotten    | 忘却フラグ     |
| created\_at      | 作成日時      |

### dialogues

| カラム名              | 説明                |
| ----------------- | ----------------- |
| dialogue\_id      | 主キー               |
| target\_user\_id  | 会話の相手ユーザー         |
| sender\_user\_id  | 発信者ID（self or AI） |
| message\_type     | input / output    |
| is\_ai\_generated | AI応答かどうか          |
| text              | メッセージ本文           |
| memory\_refs      | 参照した記憶（JSON形式）    |
| prompt\_version   | 使用したプロンプトのバージョン   |
| temperature       | モデル温度設定           |
| created\_at       | 作成日時              |

## ⚠️ 補足事項

* **Phaseモードは未実装です。** Echoとは異なり、人格切り替え機能は存在しません。
* LINE連携やWebhook接続には別途外部設定が必要です。

## 📁 ファイル構成

```
├── app.py
├── chatgpt_logic.py
├── logic/
│   ├── chatgpt_logic.py   # ChatGPT呼び出し・プロンプト生成・記憶抽出
│   ├── db_utils.py        # SQLite操作（記憶・対話ログ保存）
│   └── __init__.py
├── memory.db（実行後に作成）
├── .env
├── requirements.txt
```

---

