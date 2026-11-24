"""葬祭ビジネス定点の記事を公開前に点検する。公開対象にエラーがあると終了コード1。

使い方（site フォルダで実行）:
  python check.py         公開対象の記事だけ点検（CI でも実行）
  python check.py --all   下書きも含めて点検
"""
import re
import sys

import build

LINE_MAX, BUBBLE_MAX = 16, 9   # アイキャッチの1行あたりの目安（全角）
MIN_CHARS, MAX_CHARS = 3000, 8000   # 本文の文字数（タグと空白を除く）。SEO 記事の目安


def body_chars(html_text):
    text = re.sub(r"<[^>]+>", "", html_text)
    return len(re.sub(r"\s", "", text))


def width(s):
    """全角を1、半角を0.5として数える。"""
    return sum(0.5 if ord(c) < 0x1100 else 1 for c in s)


def check_post(p):
    errors, warns = [], []
    m, info = p["meta"], p["info"]
    for key in ("title", "date", "description", "big", "lines"):
        if not m.get(key):
            errors.append(f"メタ情報 {key} がない")
    lines, bubble = build.split_slash(m.get("lines", "")), build.split_slash(m.get("bubble", ""))
    if len(lines) > 2 or any(width(s) > LINE_MAX for s in lines):
        errors.append(f"lines は2行まで・1行{LINE_MAX}字程度まで: {lines}")
    if len(bubble) > 2 or any(width(s) > BUBBLE_MAX for s in bubble):
        errors.append(f"bubble は2行まで・1行{BUBBLE_MAX}字程度まで: {bubble}")
    if build.PLACEHOLDER.search(p["html"]):
        errors.append("【要確認】が残っている（見解などを書いて目印を消す）")
    chars = body_chars(p["html"])
    if chars < MIN_CHARS:
        errors.append(f"本文が短い（{chars}字。{MIN_CHARS}字以上）")
    elif chars > MAX_CHARS:
        warns.append(f"本文が長い（{chars}字。目安は{MAX_CHARS}字まで）")
    if not info["lead"]:
        errors.append("リード（最初の段落）がない")
    if len(info["facts"]) < 3:
        errors.append(f":::facts が3個未満（{len(info['facts'])}個）")
    for fact, src in info["facts"]:
        if not src:
            errors.append(f"出典のないファクト: {fact[:20]}…")
    if not info.get("opinion"):
        errors.append(":::opinion（見解）がない")
    if not info.get("next"):
        warns.append(":::next（次に注目する点）がない")
    if "！" in p["html"] or "!" in "".join(info.get("opinion", [])):
        warns.append("感嘆符がある")
    w = build.x_weight(build.x_post(p))
    if w > 280:
        errors.append(f"X 投稿文が長い（{w}/280）")
    return errors, warns


def main():
    include = "--all" in sys.argv
    posts, skipped = build.collect(include_drafts=include)
    failed = False
    if "example.github.io" in build.SITE_URL:
        print("警告: build.py の SITE_URL が仮のままです")
    for p in posts:
        errors, warns = check_post(p)
        mark = "NG" if errors else "OK"
        print(f"[{mark}] {p['path'].name}{'（下書き）' if p['draft'] else ''}")
        for e in errors:
            print(f"    エラー: {e}")
        for w in warns:
            print(f"    注意: {w}")
        if errors and not p["draft"]:
            failed = True
    for name, reason in skipped:
        print(f"[--] {name}（{reason}。--all で点検）")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
