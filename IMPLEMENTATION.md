# 海外テックニュース RSS自動生成 — 実装まとめ

## 概要

海外のテックニュース（Hacker News・VentureBeat AI・Reddit）を毎日自動収集し、
DeepL APIでタイトル＋概要を日本語翻訳してRSSフィードを生成する。
GitHub Actionsで毎朝7時（JST）に自動実行し、GitHub Pagesで公開する。
Inoreaderなどのフィードリーダーで購読できる。

---

## 全体構成

```
GitHubリポジトリ（例: tech-feed）
├── generate_feed.py              # メインスクリプト（収集・翻訳・RSS生成）
├── .github/
│   └── workflows/
│       └── generate-feed.yml    # GitHub Actions定義（毎朝7時自動実行）
└── docs/
    ├── index.html               # GitHub Pages トップ（フィードURLを表示）
    └── feed.xml                 # 生成されるRSSフィード（自動更新）
```

---

## データフロー

```
GitHub Actions（毎朝UTC 22:00 = JST 7:00）
  ↓
generate_feed.py 実行
  ├── Hacker News API からトップ記事取得（最大10件）
  ├── VentureBeat AI RSS から最新記事取得（最大10件）
  └── Reddit（r/artificial, r/LocalLLaMA, r/ChatGPT, r/gadgets, r/webdev）
        ↓ curlで取得（GitHub ActionsはReddit直アクセス可能）
  ↓
興味キーワードでフィルタリング → スコア順にソート → 上位50件
  ↓
DeepL API Free でタイトル＋概要200文字を日本語翻訳
  （タイトルと概要を1リクエストにまとめて送信、月約37万文字で無料枠内）
  ↓
docs/feed.xml を生成（RSS 2.0形式）
  ↓
git commit & push → GitHub Pages に自動反映
  ↓
Inoreader が https://yourname.github.io/tech-feed/feed.xml を購読
```

---

## ファイル説明

### generate_feed.py

メインスクリプト。外部ライブラリ不要（標準ライブラリのみ）。

**主な関数:**

| 関数 | 役割 |
|------|------|
| `fetch_hackernews()` | HN Firebase APIからトップ記事取得 |
| `fetch_venturebeat_ai()` | VentureBeat AI RSSをパース |
| `fetch_all_reddit()` | 5サブレッドをcurlで取得・統合 |
| `translate_items()` | DeepL APIで全件まとめて翻訳 |
| `generate_rss()` | RSS 2.0 XMLを生成 |
| `main()` | 収集→フィルタ→翻訳→RSS生成の一連の流れ |

**環境変数:**

| 変数名 | 内容 |
|--------|------|
| `DEEPL_API_KEY` | DeepL API Freeのキー（GitHub Secretsで管理） |

**設定値（スクリプト先頭で変更可能）:**

```python
MAX_ITEMS_PER_SOURCE = 10   # ソースごとの最大取得件数
SUMMARY_MAX_CHARS = 200     # 概要の最大文字数（英語）
INTEREST_KEYWORDS = [...]   # フィルタリング用キーワード
```

### .github/workflows/generate-feed.yml

- `cron: '0 22 * * *'` = 毎日UTC 22:00 = JST 7:00に実行
- `workflow_dispatch` で手動実行ボタンも有効
- 実行後に `docs/feed.xml` をコミット＆プッシュ

### docs/index.html

GitHub PagesのトップページURL。
フィードURLを動的に表示するだけのシンプルなHTML。

---

## セットアップ手順

### 1. GitHubリポジトリ作成

```bash
# GitHub上で新規リポジトリ作成（例: tech-feed）
git clone https://github.com/yourname/tech-feed.git
cd tech-feed

# ファイルを配置
# generate_feed.py → ルート
# .github/workflows/generate-feed.yml → 該当ディレクトリ
# docs/index.html → docs/フォルダ

git add .
git commit -m "init: tech-feed"
git push
```

### 2. DeepL API Freeのキー取得

1. https://www.deepl.com/pro-api にアクセス
2. 「Free登録」でアカウント作成（クレジットカード不要）
3. APIキーをコピー

### 3. GitHub Secretsにキーを登録

リポジトリの **Settings → Secrets and variables → Actions** から：

- Name: `DEEPL_API_KEY`
- Value: DeepLのAPIキー

### 4. GitHub Pagesを有効化

リポジトリの **Settings → Pages** から：

- Source: **Deploy from a branch**
- Branch: `main` / `docs` フォルダを選択

数分後に `https://yourname.github.io/tech-feed/` が公開される。

### 5. 動作確認（手動実行）

リポジトリの **Actions タブ** から：

1. `海外テックニュース RSS生成` を選択
2. `Run workflow` ボタンをクリック
3. ログを確認（緑チェックならOK）
4. `docs/feed.xml` が生成されていることを確認

### 6. Inoreaderに登録

```
https://yourname.github.io/tech-feed/feed.xml
```

上記URLをInoreaderの「フィードを追加」に入力。

---

## コスト

| サービス | 費用 |
|---------|------|
| GitHub Actions | 無料（月2,000分、1回約2分） |
| GitHub Pages | 無料 |
| DeepL API Free | 無料（月50万文字、本用途は月約37万文字） |
| **合計** | **¥0/月** |

---

## RSSフィードの見え方（Inoreader）

各記事のエントリーは以下の形式：

```
タイトル: [r/artificial](1234pt) AIエージェントが〇〇を実現
本文:
  AIエージェントが〇〇を実現（日本語概要）
  原題: AI Agent Achieves... | r/artificial
```

---

## カスタマイズポイント

### ニュースソースを追加したい

`generate_feed.py` に新しい取得関数を追加して `main()` から呼ぶだけ。
例: TechCrunch RSSを追加する場合：

```python
def fetch_techcrunch():
    raw = fetch_url("https://techcrunch.com/feed/")
    # RSSパース処理...
    return items

# main()内で追加
items.extend(fetch_techcrunch())
```

### フィルタリングキーワードを変更したい

```python
INTEREST_KEYWORDS = [
    "AI", "LLM", "GPT", "Claude", "Gemini",  # AI系
    "gadget", "device", "iPhone",              # ガジェット系
    "WordPress", "Next.js", "Dify",            # Web開発系
]
```

### 実行時刻を変えたい

`generate-feed.yml` の cron 式を変更：

```yaml
# JST = UTC+9 なので、希望時刻から9引く
- cron: '0 22 * * *'   # JST 7:00
- cron: '0 23 * * *'   # JST 8:00
- cron: '30 22 * * *'  # JST 7:30
```

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| feed.xmlが空 | キーワードフィルタが厳しすぎる | `INTEREST_KEYWORDS` を減らすか条件を緩和 |
| 翻訳されていない | `DEEPL_API_KEY` が未設定 | GitHub Secretsを確認 |
| Redditが0件 | User-Agent規制 | curlのUser-Agentを変更 |
| Actions失敗 | Pagesへのpush権限なし | ワークフローの `permissions: contents: write` を確認 |
