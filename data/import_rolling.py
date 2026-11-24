"""厚生労働省「人口動態統計月報（概数）」の『当月分を含む過去1年間の動向』(xlsx) を読む。標準ライブラリだけで動く。

使い方（プロジェクトのルートで実行）:
  python -X utf8 data/import_rolling.py data/raw/6-18.xlsx     deaths_rolling12.csv を作り直す（初回用）
通常は data/import_month.py が、この関数を使って新しい月を取り込む。

この表の値は「その月までの1年間（例: 2026年6月なら2025年7月〜2026年6月）の合計」で、月ごとの死亡数ではない。
死亡数（総数・男・女）の3つのブロックは、それぞれ最新年・前年・前々年の3行からなる。
年は D 列の「（2026）」から読む。行の位置や見出しが想定と違うときは、取り込まずに止まる。
"""
import csv
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
Q = "{%s}" % NS["m"]
COLS = "EFGHIJKLMNOP"   # 1月〜12月
HERE = Path(__file__).parent


def read_rows(path):
    z = zipfile.ZipFile(path)
    ss = [("".join(t.text or "" for t in si.iter(Q + "t"))) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS)]
    rows = {}
    for row in ET.fromstring(z.read("xl/worksheets/sheet1.xml")).iter(Q + "row"):
        cells = {}
        for c in row.findall("m:c", NS):
            v = c.find("m:v", NS)
            if v is None:
                continue
            cells[re.sub(r"\d", "", c.get("r"))] = ss[int(v.text)] if c.get("t") == "s" else v.text
        rows[int(row.get("r"))] = cells
    return rows


def parse_rolling(path):
    """{(年, 月): {"total":…, "male":…, "female":…}} を返す。"""
    rows = read_rows(path)
    if not rows.get(13, {}).get("A", "").startswith("死亡数") or not rows.get(16, {}).get("B", "").startswith("男") \
            or not rows.get(19, {}).get("B", "").startswith("女"):
        raise ValueError("死亡数の行の位置が変わっています。xlsx の構成を確かめてください")
    out = {}
    for label, first in (("total", 13), ("male", 16), ("female", 19)):
        for offset in range(3):
            r = rows[first + offset]
            m = re.search(r"(\d{4})", unicodedata.normalize("NFKC", r.get("D", "")))
            if not m:
                raise ValueError(f"年を読めません（{first + offset}行目 D列: {r.get('D')!r}）")
            year = int(m.group(1))
            for i, col in enumerate(COLS, 1):
                if col in r:
                    out.setdefault((year, i), {})[label] = int(r[col])
    return out


def write_rolling(data, dst=None):
    dst = dst or HERE / "deaths_rolling12.csv"
    with Path(dst).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "month", "total", "male", "female"])
        for (y, m) in sorted(data):
            v = data[(y, m)]
            w.writerow([y, m, v["total"], v["male"], v["female"]])


def read_rolling_csv(path=None):
    path = Path(path or HERE / "deaths_rolling12.csv")
    with path.open(encoding="utf-8") as f:
        return {(int(r["year"]), int(r["month"])): {k: int(r[k]) for k in ("total", "male", "female")} for r in csv.DictReader(f)}


if __name__ == "__main__":
    data = parse_rolling(sys.argv[1])
    write_rolling(data)
    print(f"{len(data)}か月分を deaths_rolling12.csv に書きました")
