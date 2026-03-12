# 海外テックニュース RSS フィード

HN・VentureBeat AI・Reddit（r/artificial, r/LocalLLaMA, r/ChatGPT, r/gadgets, r/webdev）から
海外テックニュースを収集し、DeepL API Freeで日本語翻訳してRSSフィードを生成します。

毎朝7時（JST）に GitHub Actions で自動実行。

## フィードURL

```
https://ryosato217.github.io/daily-tech-news-gh/feed.xml
```

## セットアップ手順

### 1. DeepL API Free のキー取得

https://www.deepl.com/pro-api から Free 登録（クレジットカード不要）

### 2. APIキーをSecretsに登録

GitHubリポジトリの Settings → Secrets and variables → Actions から：

- `DEEPL_API_KEY` : DeepL API Free のキー

### 3. GitHub Pages を有効化

リポジトリの Settings → Pages から：
- Source: Deploy from a branch
- Branch: `main` / `docs` フォルダを選択

### 4. 動作確認（手動実行）

Actions タブから `海外テックニュース RSS生成` を選択 → `Run workflow` で手動実行。

### 5. Inoreaderに登録

上記フィードURLをInoreaderの「フィードを追加」に入力。

## ファイル構成

```
daily-tech-news-gh/
  ├── generate_feed.py              # メインスクリプト（収集・翻訳・RSS生成）
  ├── .github/
  │     └── workflows/
  │           └── generate-feed.yml # GitHub Actionsワークフロー（毎朝JST 7:00）
  └── docs/
        ├── index.html              # GitHub Pages トップ
        └── feed.xml                # 生成されるRSSフィード（自動更新）
```

## コスト

| サービス | 費用 |
|---------|------|
| GitHub Actions | 無料（月2,000分、1回約2分） |
| GitHub Pages | 無料 |
| DeepL API Free | 無料（月50万文字、本用途は月約37万文字） |
| **合計** | **¥0/月** |

## カスタマイズ

`generate_feed.py` の先頭の設定値を変更：

```python
MAX_ITEMS_PER_SOURCE = 10   # ソースごとの取得件数
SUMMARY_MAX_CHARS = 200     # 概要の最大文字数
INTEREST_KEYWORDS = [...]   # 興味キーワード（フィルタリング用）
```
