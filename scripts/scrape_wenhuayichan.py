# -*- coding: utf-8 -*-
"""
爬取《人民日报》"文化遗产"版 10 篇报道，合并保存为 JSON。
数据源：
  2025-04-02 第20版 文化遗产（6篇）
  2025-05-07 第20版 文化遗产（4篇）
运行：python scrape_wenhuayichan.py
输出：D:/DSDH/corpus/wenhuayichan_10.json
"""
import json
import re
import time
import urllib.request
from pathlib import Path

OUT_DIR = Path(r"D:/DSDH/corpus")
OUT_FILE = OUT_DIR / "wenhuayichan_10.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# (日期, 文章ID)  —— 均为"文化遗产"版文章
ARTICLES = [
    ("20250402", 30065474), ("20250402", 30065475), ("20250402", 30065476),
    ("20250402", 30065477), ("20250402", 30065478), ("20250402", 30065479),
    ("20250507", 30071715), ("20250507", 30071716), ("20250507", 30071717),
    ("20250507", 30071718),
]


def dpath(d: str) -> str:  # 20250402 -> 202504/02
    return f"{d[:6]}/{d[6:]}"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"[\s\u3000]+", " ", s).strip()


def parse(html: str, d: str, aid: int) -> dict:
    # 元数据在 <!--enpproperty <date>..</date>...--> 注释块里
    prop = re.search(r"<!--enpproperty (.*?)-->.*?/enpproperty-->", html, re.S)
    prop = prop.group(1) if prop else ""

    def meta(tag: str) -> str:
        m = re.search(rf"<{tag}>(.*?)</{tag}>", prop, re.S)
        return strip_tags(m.group(1)) if m else ""

    # 正文在 <!--enpcontent--> ... <!--/enpcontent--> 注释块里，<p> 分段
    body = re.search(r"<!--enpcontent-->(.*?)<!--/enpcontent-->", html, re.S)
    paras = []
    if body:
        for p in re.findall(r"<p[^>]*>(.*?)</p>", body.group(1), re.S):
            t = re.sub(r"[\s\u3000]+", "", re.sub(r"<[^>]+>", "", p))
            t = t.replace("&nbsp;", "").strip()
            if t and not t.startswith("——"):
                paras.append(t)

    return {
        "id": aid,
        "title": meta("title"),
        "subtitle": meta("subtitle"),
        "author": meta("author"),
        "date": meta("date")[:10],
        "url": meta("url") or f"http://paper.people.com.cn/rmrb/pc/content/{dpath(d)}/content_{aid}.html",
        "paragraphs": paras,
        "full_text": "\n".join(paras),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    articles = []
    for d, aid in ARTICLES:
        url = f"https://paper.people.com.cn/rmrb/pc/content/{dpath(d)}/content_{aid}.html"
        try:
            html = fetch(url)
            art = parse(html, d, aid)
            articles.append(art)
            print(f"[ok] {art['date']} {art['title']}（{len(art['full_text'])}字）")
        except Exception as e:
            print(f"[fail] {d} {aid}: {e}")
        time.sleep(1.5)  # 控制抓取频率

    OUT_FILE.write_text(
        json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n共 {len(articles)} 篇，已保存至 {OUT_FILE}")


if __name__ == "__main__":
    main()
