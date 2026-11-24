"""アイキャッチ画像(1200x630 SVG)を、JSONの指定から作る。

使い方:
    python tools/make_eyecatch.py eyecatch/01-nyusatsu.json
    python tools/make_eyecatch.py eyecatch/*.json   (PowerShell では1件ずつ)

JSON の項目:
    out        出力先 (例: images/eyecatch-01.svg)
    site       サイト名 (左上に表示)
    label      今日のコーナー名 (例: 今日の数字)
    color      サイトの基調色 (外枠・サイト名)
    big        大きく見せる数字や短い語 (例: 62%)
    big_color  big の色
    lines      big の下に出す説明 (1〜2行。1行あたり全角16字程度まで)
    bubble     キャラクターのひとこと (1〜2行。1行あたり全角9字程度まで)
    bubble_bg  吹き出しの背景色
    char       キャラクターのSVGファイル (viewBox 0 0 200 200)
    date       日付
    note       右下の注記 (例: 数値は架空のサンプル)。省略可
    tone       "calm" にすると吹き出しを小さく、文字色を抑える (葬祭など)
外部ライブラリは使わない (Python 標準ライブラリのみ)。
"""
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

FONT = "Yu Gothic UI, Hiragino Sans, Meiryo, sans-serif"


def inner_svg(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"<svg[^>]*>(.*)</svg>", text, re.S)
    if not m:
        raise ValueError(f"SVG として読めません: {path}")
    return m.group(1).strip()


def build(spec: dict, base: Path) -> str:
    color = spec["color"]
    calm = spec.get("tone") == "calm"
    char = inner_svg(base / spec["char"])
    ink = "#444" if calm else "#1c2430"
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">',
        f'<rect width="1200" height="630" fill="{color}"/>',
        '<rect x="36" y="36" width="1128" height="558" rx="28" fill="#fff"/>',
        f'<text x="86" y="120" font-family="{FONT}" font-size="34" font-weight="700" fill="{color}">'
        f'{escape(spec["site"])}<tspan fill="#888" font-weight="400">　｜　{escape(spec["label"])}</tspan></text>',
        f'<text x="80" y="{300 if not calm else 280}" font-family="{FONT}" font-size="{170 if not calm else 130}" '
        f'font-weight="800" fill="{spec["big_color"]}">{escape(spec["big"])}</text>',
    ]
    y = 385 if not calm else 365
    for line in spec["lines"][:2]:
        parts.append(f'<text x="86" y="{y}" font-family="{FONT}" font-size="48" font-weight="700" fill="{ink}">{escape(line)}</text>')
        y += 62
    foot = escape(spec["date"]) + ("　／　" + escape(spec["note"]) if spec.get("note") else "")
    parts.append(f'<text x="86" y="556" font-family="{FONT}" font-size="26" fill="#888">{foot}</text>')
    # 吹き出し
    bub = spec.get("bubble") or []
    if bub:
        bg = spec.get("bubble_bg", "#f2f2f2")
        h = 60 + 46 * len(bub[:2])
        parts.append(f'<rect x="760" y="78" width="360" height="{h}" rx="22" fill="{bg}"/>')
        parts.append(f'<path d="M930 {78 + h} L962 {78 + h + 36} L980 {78 + h} Z" fill="{bg}"/>')
        ty = 78 + 70
        for line in bub[:2]:
            parts.append(f'<text x="940" y="{ty}" text-anchor="middle" font-family="{FONT}" '
                         f'font-size="{34 if not calm else 30}" font-weight="700" fill="{ink}">{escape(line)}</text>')
            ty += 46
    # キャラクター (200x200 → 約300px)
    parts.append(f'<g transform="translate(830,262) scale(1.5)">{char}</g>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    for arg in argv:
        spec_path = Path(arg)
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        base = Path.cwd()
        out = base / spec["out"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build(spec, base), encoding="utf-8")
        print(f"作成: {spec['out']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
