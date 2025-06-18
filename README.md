---

# 🤖 Reply – 対話専用のパーソナライズ応答AI

<div align="center">
<img src="https://github.com/bepro-engineer/ai_reply/blob/main/images/reply_screen_top.png" width="700">
</div>

---

## 💬 Replyとは？

「その返事、覚えてるよ」
Replyは、ユーザーとの対話を記録し、それを元に返答する**記憶ベースの応答AI**です。

Echoとは異なり、人格モードやPhase機能は持たず、常に**同じモードで接客を続けます**。
LINE Botなどに組み込むことで、まるで“中の人がずっと対応しているかのような”ユーザー体験を実現します。

---

## 🧠 Replyの特徴

* ユーザーごとの**会話履歴・記憶を個別に保持**
* 会話カテゴリを自動判定（固定辞書型）
* 過去の記憶（memories）を抽出し、文脈生成に活用
* AI応答と人間発話の**時系列ログを保存**
* 常に**同じ人格での応答**（モード分岐なし）

---

## 🏗️ システム構成

| モジュール                 | 説明                    |
| --------------------- | --------------------- |
| `app.py`              | Webhook受信用のFlaskアプリ本体 |
| `chatgpt_logic.py`    | OpenAIへの問い合わせロジック     |
| `db_utils.py`         | SQLite操作（記憶・対話ログ管理）   |
| `mission_policy.json` | システムの応答制約・方針定義ファイル    |

---
## 📚 ブログ解説（導入背景・技術・思想）

このプロジェクトの詳しい背景・構造・実装意図については、以下の記事で完全解説しています。

👉 [過人格を持ったLINE接客AI「Reply」](https://www.pmi-sfbac.org/category/product/ai-reply-system/)

---

## 💻 Echoの動作画面

以下は、実際にReplyをLINE上で実行した画面イメージです：

<div align="center">
<img src="https://raw.githubusercontent.com/bepro-engineer/ai-reply/main/images/reply_screen.png" width="r300">
</div>

## 🛠️ セットアップ手順

1. 仮想環境を作成し、依存ライブラリをインストール：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. `.env`ファイルを作成（OpenAIキーを設定）：

```
OPENAI_API_KEY=sk-xxxxxx
```

3. データベース初期化（SQLite）：

```bash
python
>>> from db_utils import initDatabase
>>> initDatabase()
```

4. アプリ起動：

```bash
python app.py
```

---

## 🧾 使用テーブル構造

### 🔹 memories（記憶）

| カラム名             | 型       | 説明            |
| ---------------- | ------- | ------------- |
| memory\_id       | INTEGER | 主キー           |
| content          | TEXT    | 記憶した内容        |
| category         | TEXT    | 固定カテゴリ（辞書ベース） |
| weight           | INTEGER | 重み（現状未使用）     |
| target\_user\_id | TEXT    | 対象ユーザーID      |
| is\_forgotten    | INTEGER | 忘却フラグ（0 or 1） |
| created\_at      | TEXT    | 登録日時          |

---

### 🔹 dialogues（対話ログ）

| カラム名              | 型       | 説明                  |
| ----------------- | ------- | ------------------- |
| dialogue\_id      | INTEGER | 主キー                 |
| target\_user\_id  | TEXT    | 対象ユーザーID            |
| sender\_user\_id  | TEXT    | 発信者ID               |
| message\_type     | TEXT    | 'input' or 'output' |
| is\_ai\_generated | INTEGER | 1=AI, 0=人間発話        |
| text              | TEXT    | メッセージ本文             |
| memory\_refs      | TEXT    | 使用した記憶（JSON）        |
| prompt\_version   | TEXT    | 使用したプロンプトのバージョン識別   |
| temperature       | REAL    | 出力温度                |
| created\_at       | TEXT    | タイムスタンプ             |

---

## 📝 応答構造と記憶の流れ

```
User → app.py → chatgpt_logic.py
           ↓         ↓
        db_utils ← OpenAI API
```

* 会話を受け取り、カテゴリ分類（固定辞書）
* 過去の記憶を最大10件まで抽出（同カテゴリ・同ユーザーID）
* 会話コンテキスト（直近3往復）と共にChatGPTへ送信
* 応答と記憶参照内容をdialoguesに保存

---

## 🚫 Phase機能について

> Echoに存在する「人格モード（Phase0/1/2）」は、Replyには存在しません。
> Replyは常に**同一モードで記憶・応答**を続ける仕組みです。

---

## 📂 ディレクトリ構成（初期）

```
├── app.py
├── logic/
│   ├── chatgpt_logic.py   # ChatGPT呼び出し・プロンプト生成・記憶抽出
│   ├── db_utils.py        # SQLite操作（記憶・対話ログ保存）
│   └── __init__.py
├── mission_policy.json
├── memory.db
├── .env
├── requirements.txt
```

---

