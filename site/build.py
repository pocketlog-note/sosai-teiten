"""葬祭ビジネス定点: content/*.md（記事）と pages/*.md（固定ページ）から静的サイト docs/ を作る。
標準ライブラリだけで動く。ポケットログ（play/pocket-log）の build.py と同じ考え方。

使い方（site フォルダで実行）:
  python build.py                          本番ビルド（下書き・未来日付・【要確認】入りは除外）
  $env:INCLUDE_DRAFTS=1; python build.py   下書きも含めて確認用にビルド

出力:
  docs/                 公開するサイト
  x-drafts/<slug>.txt   X に投稿する文の下書き（公開はしない）

記事の先頭のメタ情報:
---
title: 見出し（数字を入れる）
date: 2026-11-23            未来の日付はその日まで公開されない（予約公開）
description: 一行説明（検索結果・SNS）
category: ニュース｜データ
big: 76.7万人                  アイキャッチの大きな数字
big_color: #3e5c52           省略可
lines: 2026年上半期の死亡数 / 前年同期比（人口動態統計）   アイキャッチの説明（/ で改行、2行まで）
bubble: 冬が最も / 多い月です                         しずかのひとこと（/ で改行、2行まで）
x_text: X 投稿文（省略すると自動で作る。URL は自動で末尾に付く）
draft: true
---

本文の書き方:
  最初の段落          リード（ファクトだけ）
  ## 見出し           本文の節
  < で始まる行        HTML をそのまま出す（グラフ・表）
  :::facts            この記事のファクト。各行「- 事実｜出典」
  :::opinion 見出し   しずかの見解。段落で書く
  :::next             次に注目する点。各行「- 項目」
  :::method           集計方法
  :::                 ブロックの終わり
"""
import html
import os
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT.parent / "tools"))
import make_eyecatch  # noqa: E402

POSTS_SRC = ROOT / "content"
PAGES_SRC = ROOT / "pages"
OUT = ROOT / "docs"
XOUT = ROOT / "x-drafts"

SITE_URL = "https://pocketlog-note.github.io/sosai-teiten"  # 独自ドメインにしたらここを変える
SITE_NAME = "葬祭ビジネス定点"
SITE_TAGLINE = "葬儀・火葬の現場を、公的データで読む"
SITE_DESC = "葬儀社・斎場・関連事業者に向けて、人口動態統計や自治体の公表資料をもとに、葬祭まわりの数字を静かに伝えるサイトです。"
# 厚生労働省のコンテンツは「公共データ利用規約（第1.0版）」で、出典の記載と、加工した旨の記載が求められる
API_CREDIT_HTML = ('統計は<a href="https://www.mhlw.go.jp/" target="_blank" rel="noopener">厚生労働省</a>「人口動態統計」'
                   'を加工して作成しています（国が作成したものではありません）。')
COLOR = "#3e5c52"
CHAR_NAME = "しずか"
CHAR_BIO = "葬祭業界の定点観測係の黒猫。公的な数字を静かに読んで、見解はそのあとに添えます。"
OPINION_NOTE = "※見解はファクトをもとにした本誌キャラクターの意見です。特定の事業者・施設の評価ではありません。"
HASHTAGS = "#葬祭 #火葬 #多死社会"
BUBBLE_BG = "#e6ece9"
PLACEHOLDER = re.compile(r"【要確認")
JST = timezone(timedelta(hours=9))
INCLUDE_DRAFTS = bool(os.environ.get("INCLUDE_DRAFTS"))


# ---------- 読み込み ----------
def parse(path):
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    meta, body = {}, text
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = m.group(2)
    return meta, body


def is_true(v):
    return str(v).lower() == "true"


def split_slash(v):
    return [s.strip() for s in v.split("/") if s.strip()] if v else []


def publish_status(meta, body, include_drafts=None):
    """公開してよければ None、ダメなら理由を返す。"""
    if INCLUDE_DRAFTS if include_drafts is None else include_drafts:
        return None
    if is_true(meta.get("draft")):
        return "下書き"
    try:
        d = datetime.strptime(meta.get("date", ""), "%Y-%m-%d").date()
    except ValueError:
        return "date の形式が不正"
    if d > datetime.now(JST).date():
        return f"予約（{d} 公開）"
    if PLACEHOLDER.search(body):
        return "【要確認】が残っている"
    return None


# ---------- 本文 ----------
def esc(s):
    return html.escape(s, quote=True)


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[(.+?)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s


def paragraphs(lines):
    out, buf = [], []
    for ln in lines + [""]:
        if ln.strip():
            buf.append(ln.strip())
        elif buf:
            out.append("".join(buf))
            buf = []
    return out


def render_block(name, arg, lines):
    """:::name arg ... ::: のブロックを HTML にする。中身は (dict) でも返す。"""
    items = [ln.strip()[2:] for ln in lines if ln.strip().startswith("- ")]
    if name == "facts":
        lis = []
        for it in items:
            fact, _, src = it.partition("｜")
            lis.append(f'<li>{inline(fact.strip())}<span class="src">出典：{inline(src.strip())}</span></li>')
        return ('<section class="facts"><h2>この記事のファクト</h2><ol>' + "".join(lis) + "</ol></section>",
                {"facts": [(i.partition("｜")[0].strip(), i.partition("｜")[2].strip()) for i in items]})
    if name == "opinion":
        ps = "".join(f"<p>{inline(p)}</p>" for p in paragraphs(lines))
        return (f'<section class="opinion"><img src="{{prefix}}images/char.svg" alt="{CHAR_NAME}"><div>'
                f'<div class="who">{CHAR_NAME}の見解</div><h2>{inline(arg)}</h2>{ps}'
                f'<p class="disc">{OPINION_NOTE}</p></div></section>',
                {"opinion_title": arg, "opinion": paragraphs(lines)})
    if name == "next":
        return ('<div class="next"><b>次に注目する点</b><ul>' + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul></div>",
                {"next": items})
    if name == "method":
        return (f'<div class="method"><b>集計方法</b>　{"".join(inline(p) for p in paragraphs(lines))}</div>', {"method": True})
    raise ValueError(f"知らないブロック :::{name}")


def md_to_html(body):
    """本文を HTML にする。(html, 情報dict) を返す。"""
    out, info = [], {"lead": "", "facts": [], "opinion": [], "next": []}
    para, items = [], []
    block = None  # (name, arg, lines)

    def flush():
        nonlocal para, items
        if para:
            text = "".join(para)
            if not info["lead"] and not any(o.startswith("<h2") for o in out):
                info["lead"] = text
                out.append(f'<p class="lead">{inline(text)}</p>')
            else:
                out.append(f"<p>{inline(text)}</p>")
            para = []
        if items:
            out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
            items = []

    for raw in body.splitlines():
        s = raw.rstrip()
        if block is not None:
            if s.strip() == ":::":
                h, data = render_block(*block)
                out.append(h)
                info.update(data)
                block = None
            else:
                block[2].append(s)
            continue
        m = re.match(r":::(\w+)\s*(.*)", s.strip())
        if m:
            flush()
            block = (m.group(1), m.group(2).strip(), [])
        elif not s.strip():
            flush()
        elif s.startswith("## "):
            flush()
            out.append(f"<h2>{inline(s[3:])}</h2>")
        elif s.lstrip().startswith("<"):
            flush()
            out.append(s)
        elif s.startswith("- "):
            if para:
                flush()
            items.append(s[2:])
        else:
            if items:
                flush()
            para.append(s.strip())
    if block is not None:
        raise ValueError(f":::{block[0]} が閉じられていません")
    flush()
    return "\n".join(out), info


# ---------- X 投稿文 ----------
def x_weight(text):
    """X の文字数の数え方（概算）。URL は23、半角は1、全角は2。上限は280。"""
    urls = re.findall(r"https?://\S+", text)
    rest = re.sub(r"https?://\S+", "", text)
    return 23 * len(urls) + sum(1 if ord(c) < 0x1100 else 2 for c in rest)


def x_post(p):
    head = (p["meta"].get("x_text") or "").replace("\\n", "\n") or f"【今日の数字】{p['meta'].get('big', '')}\n{p['title']}"
    return f"{head}\n{p['url']}\n{HASHTAGS}"


# ---------- HTML ----------
def layout(*, title, desc, inner, prefix, url, og_type="website", full_title=None):
    full = full_title or f"{title}｜{SITE_NAME}"
    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(url)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{esc(url)}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta name="twitter:card" content="summary">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{prefix}feed.xml">
<link rel="stylesheet" href="{prefix}style.css"></head>
<body>
<header><div class="bar">
<a class="logo" href="{prefix}index.html">{SITE_NAME}<small>{SITE_TAGLINE}</small></a>
<nav><a href="{prefix}index.html">ニュース</a><a href="{prefix}about.html">このサイトについて</a></nav>
</div></header>
{inner}
<footer><div class="bar"><span>© {datetime.now(JST).year} {SITE_NAME}　{API_CREDIT_HTML}</span>
<nav><a href="{prefix}about.html">このサイトについて</a><a href="{prefix}feed.xml">RSS</a></nav></div></footer>
</body></html>"""


def aside(prefix):
    return (f'<aside><div class="box char"><img src="{prefix}images/char.svg" alt=""><h3>{CHAR_NAME}</h3>{CHAR_BIO}</div>'
            f'<div class="box"><h3>このサイトについて</h3>記事は公開データの集計をもとに、AIキャラクターが下書きし、編集部が確認して公開しています。'
            f' <a href="{prefix}about.html">くわしく</a></div></aside>')


def card(p, prefix):
    return (f'<a class="card" href="{prefix}posts/{p["slug"]}.html">'
            f'<img src="{prefix}images/eyecatch/{p["slug"]}.svg" alt="">'
            f'<span class="t">{esc(p["title"])}</span><span class="d">{p["date"]}・{esc(p["category"])}</span></a>')


def build_post(p):
    draft = '<p class="draftnote">下書きプレビュー（公開されていません）</p>' if p["draft"] else ""
    body = p["html"].replace("{prefix}", "../")
    inner = f"""<div class="wrap"><article>{draft}
<img class="eyecatch" src="../images/eyecatch/{p['slug']}.svg" alt="{esc(p['meta'].get('big', ''))}">
<span class="cat">{esc(p['category'])}</span>
<h1>{esc(p['title'])}</h1>
<div class="byline"><img src="../images/char.svg" alt="">文：{CHAR_NAME}（AIキャラクター）／確認：{SITE_NAME}編集部　｜　{p['date']}</div>
{body}
</article>{aside('../')}</div>"""
    return layout(title=p["title"], desc=p["desc"], inner=inner, prefix="../", url=p["url"], og_type="article")


def collect(include_drafts=None):
    """公開対象の記事を集める。check.py からも使う。"""
    posts, skipped = [], []
    for path in sorted(POSTS_SRC.glob("*.md")):
        meta, body = parse(path)
        reason = publish_status(meta, body, include_drafts)
        if reason:
            skipped.append((path.name, reason))
            continue
        content_html, info = md_to_html(body)
        slug = path.stem
        posts.append({
            "slug": slug, "path": path, "meta": meta, "info": info,
            "title": meta.get("title", slug), "date": meta.get("date", ""),
            "desc": meta.get("description", ""), "category": meta.get("category", "ニュース"),
            "draft": is_true(meta.get("draft")), "html": content_html,
            "url": f"{SITE_URL}/posts/{slug}.html",
        })
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts, skipped


def eyecatch_spec(p):
    return {
        "site": SITE_NAME, "label": "今日の数字", "color": COLOR,
        "big": p["meta"].get("big", ""), "big_color": p["meta"].get("big_color", "#c0392b"),
        "lines": split_slash(p["meta"].get("lines", "")), "bubble": split_slash(p["meta"].get("bubble", "")),
        "bubble_bg": BUBBLE_BG, "tone": "calm", "char": "images/char.svg", "date": p["date"].replace("-", "."),
        "note": p["meta"].get("eyecatch_note", ""),
    }


def main():
    posts, skipped = collect()
    for name, reason in skipped:
        print(f"  非公開: {name}（{reason}）")
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "posts").mkdir(parents=True)
    (OUT / "images" / "eyecatch").mkdir(parents=True)
    shutil.copy(ROOT / "style.css", OUT / "style.css")
    shutil.copy(ROOT / "images" / "char.svg", OUT / "images" / "char.svg")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    XOUT.mkdir(exist_ok=True)

    for p in posts:
        (OUT / "posts" / f"{p['slug']}.html").write_text(build_post(p), encoding="utf-8")
        svg = make_eyecatch.build(eyecatch_spec(p), ROOT)
        (OUT / "images" / "eyecatch" / f"{p['slug']}.svg").write_text(svg, encoding="utf-8")
        (XOUT / f"{p['slug']}.txt").write_text(x_post(p) + "\n", encoding="utf-8")

    cards = "".join(card(p, "") for p in posts) or '<p class="empty">最初の記事を準備中です。</p>'
    inner = f"""<div class="wrap"><main><section class="hero"><h1>{SITE_TAGLINE}</h1><p>{SITE_DESC}</p></section>
<h2 class="section">新着のニュース</h2><div class="cards">{cards}</div></main>{aside('')}</div>"""
    (OUT / "index.html").write_text(layout(title=SITE_NAME, desc=SITE_DESC, inner=inner, prefix="", url=f"{SITE_URL}/",
                                           full_title=f"{SITE_NAME}｜{SITE_TAGLINE}"), encoding="utf-8")

    pages = []
    for path in sorted(PAGES_SRC.glob("*.md")):
        meta, body = parse(path)
        ps = "".join(f"<h2>{inline(b[3:])}</h2>" if b.startswith("## ") else f"<p>{inline(b)}</p>"
                     for b in paragraphs(body.splitlines()))
        title = meta.get("title", path.stem)
        inner = f'<div class="wrap"><article><h1>{esc(title)}</h1>{ps}</article>{aside("")}</div>'
        (OUT / f"{path.stem}.html").write_text(layout(title=title, desc=meta.get("description", SITE_DESC), inner=inner,
                                                      prefix="", url=f"{SITE_URL}/{path.stem}.html"), encoding="utf-8")
        pages.append(path.stem)

    urls = [f"{SITE_URL}/"] + [p["url"] for p in posts] + [f"{SITE_URL}/{s}.html" for s in pages]
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"<url><loc>{esc(u)}</loc></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    items = ""
    for p in posts[:20]:
        d = datetime.strptime(p["date"], "%Y-%m-%d").replace(hour=6, tzinfo=JST)
        items += (f"<item><title>{esc(p['title'])}</title><link>{p['url']}</link><guid>{p['url']}</guid>"
                  f"<pubDate>{format_datetime(d)}</pubDate><description>{esc(p['desc'])}</description></item>\n")
    (OUT / "feed.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{SITE_NAME}</title>'
        f"<link>{SITE_URL}/</link><description>{esc(SITE_DESC)}</description><language>ja</language>\n{items}</channel></rss>\n",
        encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")

    print(f"記事 {len(posts)} 本・固定ページ {len(pages)} 枚を docs/ に、X 投稿文を x-drafts/ に出力しました"
          + ("（下書き込みプレビュー）" if INCLUDE_DRAFTS else ""))


if __name__ == "__main__":
    main()
