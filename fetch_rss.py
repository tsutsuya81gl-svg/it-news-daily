import feedparser
import json
import hashlib
from difflib import SequenceMatcher
from datetime import datetime

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

        items.append({
            "title": title,
            "link": link,
            "summary": summary,
            "published": published,
            "source": src["name"],
            "priority": src["priority"]
        })

# 重複排除（タイトル類似度）
filtered = []
for item in items:
    is_duplicate = False
    for f in filtered:
        if similar(item["title"], f["title"]) > 0.7:
            # priority が高い方を残す
            if item["priority"] > f["priority"]:
                filtered.remove(f)
                filtered.append(item)
            is_duplicate = True
            break
    if not is_duplicate:
        filtered.append(item)

# 日付順にソート
filtered.sort(key=lambda x: x["published"], reverse=True)

# HTML生成
html = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>IT News Daily</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { font-family: sans-serif; padding: 20px; line-height: 1.6; }
.news-item { margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #ddd; }
.title { font-size: 18px; font-weight: bold; }
.source { color: #555; font-size: 14px; }
</style>
</head>
<body>
<h1>IT News Daily</h1>
<p>最終更新: """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """</p>
"""

for item in filtered:
    html += f"""
<div class="news-item">
  <div class="title"><a href="{item['link']}" target="_blank">{item['title']}</a></div>
  <div class="source">{item['source']} / {item['published']}</div>
</div>
"""

html += """
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
