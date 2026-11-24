"""記事の Markdown から、文章だけ（メタ情報・HTML の表やグラフを除く）を取り出す。yomiyasu の検査に渡すため。

使い方（プロジェクトのルートで実行）:
  python -X utf8 tools/export_text.py site/content/<記事>.md _text/<名前>-final.md
"""
import re
import sys
from pathlib import Path


def export(text):
    text = text.replace("\r\n", "\n")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    title = ""
    if m:
        for line in m.group(1).splitlines():
            if line.startswith("title:"):
                title = line.split(":", 1)[1].strip()
        text = m.group(2)
    out = [f"# {title}", ""] if title else []
    for line in text.splitlines():
        s = line.rstrip()
        if s.lstrip().startswith("<"):
            continue                      # 表・グラフの HTML
        if re.match(r":::opinion\s+(.*)", s):
            out.append("## 見解：" + re.match(r":::opinion\s+(.*)", s).group(1))
            continue
        if re.match(r":::(facts|next|method)", s):
            out.append({"facts": "## この記事のファクト", "next": "## 次に注目する点", "method": "## 集計方法"}[s.strip()[3:]])
            continue
        if s.strip() == ":::":
            continue
        s = re.sub(r"\[([^\]]+)\]\(https?://[^)]+\)", r"\1", s)
        out.append(s)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"


if __name__ == "__main__":
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(export(src.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"書きました: {dst}（{len(dst.read_text(encoding='utf-8'))}字）")
