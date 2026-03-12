# 海外テックニュース RSS フィード

HN・VentureBeat AI・Reddit（r/artificial, r/LocalLLaMA, r/ChatGPT, r/gadgets, r/webdev）から
海外テックニュースを収集し、Claude APIで日本語翻訳してRSSフィードを生成します。

毎朝7時（JST）に GitHub Actions で自動実行。

## セットアップ手順

### 1. リポジトリ作成

```bash
# GitHubで新規リポジトリを作成（例: tech-feed）
git clone https://github.com/yourname/tech-feed.git
cd tech-feed

# このリポジトリのファイルをすべてコピー
```

### 2. APIキーをSecretsに登録

GitHubリポジトリの Settings → Secrets and variables → Actions から：

- `ANTHROPIC_API_KEY` : AnthropicのAPIキー

### 3. GitHub Pages を有効化

リポジトリの Settings → Pages から：
- Source: **GitHub Actions** を選択（または `docs/` フォルダを指定）

### 4. ワークフローを有効化

Actions タブから `generate-feed` を選択 → `Run workflow` で手動実行して動作確認。

### 5. Inoreaderに登録

GitHub PagesのURL（例: `https://yourname.github.io/tech-feed/feed.xml`）をInoreaderに追加。

## ファイル構成

```
tech-feed/
  ├── generate_feed.py          # メインスクリプト
  ├── .github/
  │     └── workflows/
  │           └── generate-feed.yml  # GitHub Actionsワークフロー
  └── docs/
        ├── index.html          # GitHub Pages トップ
        └── feed.xml            # 生成されるRSSフィード（自動更新）
```

## コスト目安

- GitHub Actions: 無料（月2000分、1回あたり約2分）
- Claude API（翻訳）: 約$0.01/日以下（Haiku使用、50記事翻訳）
- GitHub Pages: 無料

## カスタマイズ

`generate_feed.py` の先頭の設定値を変更：

```python
MAX_ITEMS_PER_SOURCE = 10  # ソースごとの取得件数
TRANSLATE_BATCH_SIZE = 20  # 翻訳バッチサイズ
INTEREST_KEYWORDS = [...]  # 興味キーワード（フィルタリング用）
```
