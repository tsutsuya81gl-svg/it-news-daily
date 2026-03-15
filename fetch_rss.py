import feedparser
import json
from difflib import SequenceMatcher
from datetime import datetime
from time import mktime
from googletrans import Translator

translator = Translator()

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

# RSS一覧読み込み
with open("rss_list.json", "r", encoding="utf-8") as f:
    rss_sources = json.load(f)["sources"]

items = []

# RSS取得
for src in rss_sources:
    feed = feedparser.parse(src["url"])
    for entry in feed.entries:
        title = entry.title
        link = entry.link
        summary = getattr(entry, "summary", "")
        published = getattr(entry, "published", "")
        published_parsed = getattr(entry, "published_parsed", None)

        # 日付変換
        if published_parsed:
            published_dt = datetime.fromtimestamp(mktime(published_parsed))
        else:
            published_dt = datetime.now()

        # 翻訳（公式ブログのみ）
        if src.get("translate", False):
            try:
                title = translator.translate(title, dest="ja").text
                if summary:
                    summary = translator.translate(summary, dest="ja").text
            except Exception:
                pass

        # 概要を短めに整形（1〜2行）
        if summary:
            summary = summary.replace("\n", " ")
            if len(summary) > 120:
                summary = summary[:120] + "…"

        items.append({
            "title": title,
            "link": link,
            "summary": summary,
            "published": published,
            "published_dt": published_dt,
            "source": src["name"],
            "priority": src["priority"],
            "kind": src["type"]  # news / official
        })

# 重複排除
filtered = []
for item in items:
    is_duplicate = False
    for f in filtered:
        if similar(item["title"], f["title"]) > 0.7:
            if item["priority"] > f["priority"]:
                filtered.remove(f)
                filtered.append(item)
            is_duplicate = True
            break
    if not is_duplicate:
        filtered.append(item)

# ソート
filtered.sort(key=lambda x: (x["priority"], x["published_dt"]), reverse=True)

# カテゴリ分割
news_items = [i for i in filtered if i["kind"] == "news"]
official_items = [i for i in filtered if i["kind"] == "official"]

# TOP10
top_news = news_items[:10]
top_official = official_items[:10]

# その他20件
top_keys = {(i["title"], i["link"]) for i in top_news + top_official}
other_items = [i for i in filtered if (i["title"], i["link"]) not in top_keys][:20]

# HTML生成
html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>IT News Daily</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Segoe UI", sans-serif;
  background-color: #f5f5f5;
}}

.header {{
  background-color: #2f6fbd;
  color: #fff;
  padding: 12px 16px;
  font-size: 20px;
  font-weight: bold;
}}

.container {{
  max-width: 960px;
  margin: 16px auto;
  padding: 16px;
}}

.section-title {{
  font-size: 18px;
  font-weight: bold;
  margin: 16px 0 8px;
  border-left: 4px solid #2f6fbd;
  padding-left: 8px;
}}

.card {{
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}}

.card-official {{
  border: 1px solid #2f6fbd;
}}

.card ul {{
  margin: 0;
  padding-left: 18px;
}}

.card li {{
  margin-bottom: 4px;
  font-size: 14px;
}}

.card a {{
  text-decoration: none;
  color: #1a0dab;
  font-weight: bold;

  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}}

.card a:hover {{
  text-decoration: underline;
}}

.meta {{
  font-size: 12px;
  color: #777;
}}

.sub-list {{
  list-style: none;
  padding-left: 0;
}}

.sub-list li {{
  padding: 6px 0;
  border-bottom: 1px dotted #ccc;
  font-size: 14px;
}}

.sub-list a {{
  text-decoration: none;
  color: #1a0dab;

  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}}

.sub-meta {{
  font-size: 11px;
  color: #777;
}}
</style>
</head>
<body>

<div class="header">IT News Daily</div>

<div class="container">

<div class="section-title">ニュース TOP10</div>
"""

# ニュース TOP10
for item in top_news:
    html += f"""
<div class="card">
  <ul>
    <li><a href="{item['link']}" target="_blank">{item['title']}</a></li>
    <li>{item['summary']}</li>
    <li class="meta">{item['source']} / {item['published']}</li>
  </ul>
</div>
"""

# 公式 TOP10
html += """
<div class="section-title">公式ドキュメント・ブログ TOP10</div>
"""

for item in top_official:
    html += f"""
<div class="card card-official">
  <ul>
    <li><a href="{item['link']}" target="_blank">{item['title']}</a></li>
    <li>{item['summary']}</li>
    <li class="meta">{item['source']} / {item['published']}</li>
  </ul>
</div>
"""

# その他20件
html += """
<div class="section-title">その他のニュース（20件）</div>
<ul class="sub-list">
"""

for item in other_items:
    html += f"""
  <li>
    <a href="{item['link']}" target="_blank">{item['title']}</a>
    <span class="sub-meta"> / {item['source']}</span>
  </li>
"""

html += """
</ul>
</div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
