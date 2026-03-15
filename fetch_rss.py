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

        # 日付を datetime に変換（なければ現在時刻）
        if published_parsed:
            published_dt = datetime.fromtimestamp(mktime(published_parsed))
        else:
            published_dt = datetime.now()

        # 公式ブログなどは日本語に翻訳
        if src.get("translate", False):
            try:
                title_ja = translator.translate(title, dest="ja").text
                if summary:
                    summary_ja = translator.translate(summary, dest="ja").text
                else:
                    summary_ja = ""
                title = title_ja
                summary = summary_ja
            except Exception:
                # 翻訳に失敗したら元のまま
                pass

        items.append({
            "title": title,
            "link": link,
            "summary": summary,
            "published": published,
            "published_dt": published_dt,
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

# 重要度順にソート（priority → 日付）
filtered.sort(key=lambda x: (x["priority"], x["published_dt"]), reverse=True)

# TOP10 と 残りに分割
top_items = filtered[:10]
other_items = filtered[10:]

# HTML生成（Yahoo!ニュースっぽいレイアウト）
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

.header span.logo {{
  color: #ffcc00;
}}

.container {{
  max-width: 960px;
  margin: 16px auto;
  background-color: #ffffff;
  padding: 16px;
  box-shadow: 0 0 4px rgba(0,0,0,0.1);
}}

.updated {{
  font-size: 12px;
  color: #666;
  margin-bottom: 12px;
}}

.main-title {{
  font-size: 18px;
  font-weight: bold;
  border-left: 4px solid #2f6fbd;
  padding-left: 8px;
  margin-bottom: 12px;
}}

.main-news-item {{
  border-bottom: 1px solid #e5e5e5;
  padding: 10px 0;
}}

.main-news-item:last-child {{
  border-bottom: none;
}}

.main-news-item a {{
  text-decoration: none;
  color: #1a0dab;
  font-size: 16px;
  font-weight: bold;
}}

.main-news-item a:hover {{
  text-decoration: underline;
}}

.main-meta {{
  font-size: 12px;
  color: #777;
  margin-top: 4px;
}}

.main-summary {{
  font-size: 13px;
  color: #333;
  margin-top: 4px;
}}

.sub-title {{
  font-size: 16px;
  font-weight: bold;
  margin-top: 20px;
  margin-bottom: 8px;
  border-left: 4px solid #999;
  padding-left: 8px;
}}

.sub-list {{
  list-style: none;
  padding-left: 0;
  margin: 0;
}}

.sub-list li {{
  font-size: 13px;
  padding: 4px 0;
  border-bottom: 1px dotted #ddd;
}}

.sub-list li a {{
  text-decoration: none;
  color: #1a0dab;
}}

.sub-list li a:hover {{
  text-decoration: underline;
}}

.sub-meta {{
  font-size: 11px;
  color: #777;
  margin-left: 4px;
}}
</style>
</head>
<body>
<div class="header">
  <span class="logo">IT</span> News Daily
</div>
<div class="container">
  <div class="updated">最終更新: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>

  <div class="main-title">重要ニュース TOP10</div>
"""

# TOP10（大きく表示）
for item in top_items:
    html += f"""
  <div class="main-news-item">
    <a href="{item['link']}" target="_blank" rel="noopener noreferrer">{item['title']}</a>
    <div class="main-meta">{item['source']} / {item['published']}</div>
"""
    if item["summary"]:
        html += f"""    <div class="main-summary">{item['summary']}</div>
"""
    html += "  </div>\n"

# 残り（概要メモ風）
html += """
  <div class="sub-title">その他のニュース</div>
  <ul class="sub-list">
"""

for item in other_items:
    html += f"""
    <li>
      <a href="{item['link']}" target="_blank" rel="noopener noreferrer">{item['title']}</a>
      <span class="sub-meta">{item['source']}</span>
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
