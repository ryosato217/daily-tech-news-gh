"""
海外テックニュース収集 → 日本語翻訳（DeepL API Free）→ RSS生成
ソース: Hacker News, VentureBeat AI, Reddit (AI/テック系)
"""

import os
import re
import json
import time
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import formatdate, parsedate_to_datetime
import urllib.request
import urllib.parse
import xml.dom.minidom

# --- 設定 ---
DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY", "")
OUTPUT_FILE = "docs/feed.xml"
MAX_ITEMS_PER_SOURCE = 10   # ソースごとの最大取得件数
SUMMARY_MAX_CHARS = 200     # 概要の最大文字数（英語）

INTEREST_KEYWORDS = [
    "AI", "LLM", "GPT", "Claude", "Gemini", "agent", "model",
    "open source", "tool", "framework", "web", "gadget", "device",
    "startup", "SaaS", "API", "plugin", "automation", "workflow"
]

# --- ユーティリティ ---

def fetch_url(url, headers=None):
    """URLの内容を取得"""
    req = urllib.request.Request(url, headers=headers or {
        "User-Agent": "tech-feed/1.0"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [WARN] fetch失敗: {url} → {e}")
        return ""

def strip_html(text):
    """簡易HTMLタグ除去"""
    return re.sub(r"<[^>]+>", "", text).strip()

def deepl_translate(texts):
    """
    DeepL API Free でテキストのリストをまとめて日本語翻訳。
    無料版エンドポイント: api-free.deepl.com
    1リクエストで複数テキストを送信可能（text パラメータを繰り返す）。
    """
    if not DEEPL_API_KEY:
        return texts

    params = [("target_lang", "JA"), ("source_lang", "EN")]
    for t in texts:
        params.append(("text", t if t.strip() else " "))

    payload = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(
        "https://api-free.deepl.com/v2/translate",
        data=payload,
        headers={
            "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            data = json.loads(res.read())
            return [t["text"] for t in data["translations"]]
    except Exception as e:
        print(f"  [WARN] DeepL翻訳失敗: {e}")
        return texts

def translate_items(items):
    """
    タイトルと概要をDeepLでまとめて翻訳。
    タイトルと概要を1つのリストにまとめて1リクエストで送信（文字数節約）。
    DeepL Freeは1リクエスト最大50テキストのため50件ずつバッチ処理。
    """
    print("▶ DeepL で翻訳中...")

    # タイトルと概要を交互に並べる
    # ["title1", "summary1", "title2", "summary2", ...]
    combined = []
    for item in items:
        combined.append(item["title"])
        summary = item.get("description", "")[:SUMMARY_MAX_CHARS]
        combined.append(summary if summary.strip() else " ")

    translated = []
    batch_size = 50  # DeepLの1リクエスト上限
    for i in range(0, len(combined), batch_size):
        batch = combined[i:i + batch_size]
        print(f"  バッチ {i // batch_size + 1}: {len(batch)} テキスト送信")
        result = deepl_translate(batch)
        translated.extend(result)
        time.sleep(0.5)

    # タイトルと概要に分離してアイテムに付与
    for idx, item in enumerate(items):
        item["title_ja"] = translated[idx * 2] if idx * 2 < len(translated) else item["title"]
        raw_desc = translated[idx * 2 + 1] if idx * 2 + 1 < len(translated) else ""
        item["description_ja"] = raw_desc.strip() if raw_desc.strip() != " " else ""

    print(f"  → {len(items)} 件翻訳完了")
    return items

def is_interesting(title):
    """興味キーワードにマッチするか簡易判定"""
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in INTEREST_KEYWORDS)

# --- ソース別収集 ---

def fetch_hackernews():
    """Hacker News トップ記事を取得（公式Firebase API使用）"""
    print("▶ Hacker News 取得中...")
    items = []
    try:
        top_ids_raw = fetch_url("https://hacker-news.firebaseio.com/v0/topstories.json")
        top_ids = json.loads(top_ids_raw)[:30]
        for item_id in top_ids:
            if len(items) >= MAX_ITEMS_PER_SOURCE:
                break
            raw = fetch_url(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json")
            if not raw:
                continue
            item = json.loads(raw)
            if item.get("type") != "story" or not item.get("title"):
                continue
            items.append({
                "title": item["title"],
                "url": f"https://news.ycombinator.com/item?id={item_id}",
                "description": "",
                "score": item.get("score", 0),
                "source": "Hacker News",
                "published": datetime.fromtimestamp(item.get("time", 0), tz=timezone.utc)
            })
            time.sleep(0.1)
    except Exception as e:
        print(f"  [ERROR] HN: {e}")
    print(f"  → {len(items)} 件取得")
    return items

def fetch_venturebeat_ai():
    """VentureBeat AI の RSS フィードを取得"""
    print("▶ VentureBeat AI 取得中...")
    items = []
    try:
        raw = fetch_url("https://venturebeat.com/category/ai/feed/")
        root = ET.fromstring(raw)
        channel = root.find("channel")
        for entry in channel.findall("item")[:MAX_ITEMS_PER_SOURCE]:
            title = entry.findtext("title", "").strip()
            url = entry.findtext("link", "").strip()
            desc = strip_html(entry.findtext("description", ""))[:SUMMARY_MAX_CHARS]
            pub_str = entry.findtext("pubDate", "")
            try:
                pub = parsedate_to_datetime(pub_str)
            except Exception:
                pub = datetime.now(tz=timezone.utc)
            if title and url:
                items.append({
                    "title": title,
                    "url": url,
                    "description": desc,
                    "score": 0,
                    "source": "VentureBeat AI",
                    "published": pub
                })
    except Exception as e:
        print(f"  [ERROR] VentureBeat: {e}")
    print(f"  → {len(items)} 件取得")
    return items

def fetch_reddit(subreddit):
    """Reddit サブレッドの hot 記事を curl で取得（WebFetchはブロックされるため）"""
    items = []
    try:
        result = subprocess.run(
            ["curl", "-s", "-H", "User-Agent: tech-feed/1.0",
             f"https://old.reddit.com/r/{subreddit}/hot.json?t=day&limit={MAX_ITEMS_PER_SOURCE}"],
            capture_output=True, text=True, timeout=15
        )
        data = json.loads(result.stdout)
        for child in data["data"]["children"]:
            d = child["data"]
            if d.get("stickied"):
                continue
            selftext = strip_html(d.get("selftext", ""))[:SUMMARY_MAX_CHARS]
            items.append({
                "title": d["title"],
                "url": f"https://www.reddit.com{d['permalink']}",
                "description": selftext,
                "score": d.get("ups", 0),
                "source": f"r/{subreddit}",
                "published": datetime.fromtimestamp(d.get("created_utc", 0), tz=timezone.utc)
            })
    except Exception as e:
        print(f"  [WARN] r/{subreddit}: {e}")
    return items

def fetch_all_reddit():
    """AI・テック系サブレッドをまとめて取得"""
    print("▶ Reddit 取得中...")
    subreddits = ["artificial", "LocalLLaMA", "ChatGPT", "gadgets", "webdev"]
    all_items = []
    for sub in subreddits:
        items = fetch_reddit(sub)
        all_items.extend(items)
        time.sleep(1)
    all_items.sort(key=lambda x: x.get("score", 0), reverse=True)
    result = all_items[:MAX_ITEMS_PER_SOURCE * 2]
    print(f"  → {len(result)} 件取得")
    return result

# --- RSS生成 ---

def generate_rss(items):
    """RSS 2.0 フィードを生成"""
    now_rfc = formatdate(usegmt=True)
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "海外テックニュース（日本語）"
    ET.SubElement(channel, "link").text = "https://github.com"
    ET.SubElement(channel, "description").text = (
        f"HN・VentureBeat・Reddit から収集した海外テックニュース日本語訳 | {today}"
    )
    ET.SubElement(channel, "language").text = "ja"
    ET.SubElement(channel, "lastBuildDate").text = now_rfc

    for item in items:
        entry = ET.SubElement(channel, "item")
        title_ja = item.get("title_ja", item["title"])
        source = item.get("source", "")
        score = item.get("score", 0)
        score_str = f" ({score}pt)" if score else ""

        ET.SubElement(entry, "title").text = f"[{source}]{score_str} {title_ja}"
        ET.SubElement(entry, "link").text = item["url"]

        # Inoreaderで読みやすいdescription
        desc_ja = item.get("description_ja", "").strip()
        desc_parts = [f"<p><strong>{title_ja}</strong></p>"]
        if desc_ja:
            desc_parts.append(f"<p>{desc_ja}</p>")
        desc_parts.append(
            f"<p><small>原題: {item['title']}<br>ソース: {source}</small></p>"
        )
        ET.SubElement(entry, "description").text = "\n".join(desc_parts)
        ET.SubElement(entry, "guid", isPermaLink="true").text = item["url"]

        pub = item.get("published", datetime.now(tz=timezone.utc))
        ET.SubElement(entry, "pubDate").text = formatdate(pub.timestamp(), usegmt=True)

    raw_xml = ET.tostring(rss, encoding="unicode")
    dom = xml.dom.minidom.parseString(raw_xml)
    return dom.toprettyxml(indent="  ", encoding=None)

# --- メイン ---

def main():
    print("=" * 50)
    print("海外テックニュース RSS生成（DeepL翻訳）")
    print("=" * 50)

    # 収集
    items = []
    items.extend(fetch_hackernews())
    items.extend(fetch_venturebeat_ai())
    items.extend(fetch_all_reddit())
    print(f"\n合計 {len(items)} 件収集")

    # 興味フィルタリング（キーワードマッチ）
    filtered = [i for i in items if is_interesting(i["title"])]
    if len(filtered) < 10:
        filtered = items  # フィルタが厳しすぎる場合は全件使用
    print(f"フィルタ後: {len(filtered)} 件")

    # スコア順にソートして上位50件に絞る
    filtered.sort(key=lambda x: x.get("score", 0), reverse=True)
    filtered = filtered[:50]

    # 翻訳
    if DEEPL_API_KEY:
        filtered = translate_items(filtered)
    else:
        print("  [INFO] DEEPL_API_KEY 未設定のため翻訳スキップ（英語のまま出力）")
        for item in filtered:
            item["title_ja"] = item["title"]
            item["description_ja"] = item.get("description", "")

    # RSS生成・保存
    print("▶ RSS生成中...")
    os.makedirs("docs", exist_ok=True)
    xml_content = generate_rss(filtered)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(xml_content)

    print(f"\n✅ 完了: {OUTPUT_FILE} ({len(filtered)} 件)")

if __name__ == "__main__":
    main()
