"""厚生労働省「人口動態統計月報（概数）」の『当月分を含む過去1年間の動向』(xlsx) から、
死亡数（総数・男・女）の「過去1年間の合計」を CSV にする。標準ライブラリだけで動く。

使い方（プロジェクトのルートで実行）:
  python -X utf8 data/import_rolling.py data/raw/6-18.xlsx

出力: data/deaths_rolling12.csv（year, month, total, male, female）
注意: この表の値は「その月までの1年間（例: 2026年6月なら2025年7月〜2026年6月）の合計」で、月ごとの死亡数ではない。
"""
import csv
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
Q = "{%s}" % NS["m"]


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


def main(path):
    rows = read_rows(path)
    # 死亡数ブロック: 総数13-15行、男16-18行、女19-21行（各ブロックは 令和8・7・6 の順）。見出しを確かめてから読む
    assert rows[13].get("A", "").startswith("死亡数"), "死亡数の行の位置が変わっています。xlsx の構成を確かめてください"
    assert rows[16].get("B", "").startswith("男") and rows[19].get("B", "").startswith("女")
    cols = "EFGHIJKLMNOP"   # 1月〜12月
    out = {}
    for label, first in (("total", 13), ("male", 16), ("female", 19)):
        for offset, year in ((0, 2026), (1, 2025), (2, 2024)):
            r = rows[first + offset]
            assert str(year - 1988 if year < 2019 else 0) is not None
            for i, col in enumerate(cols, 1):
                if col in r:
                    out.setdefault((year, i), {})[label] = int(r[col])
    dst = Path(__file__).parent / "deaths_rolling12.csv"
    with dst.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "month", "total", "male", "female"])
        for (y, m) in sorted(out):
            v = out[(y, m)]
            w.writerow([y, m, v["total"], v["male"], v["female"]])
    print(f"{len(out)}か月分を {dst.name} に書きました")


if __name__ == "__main__":
    main(sys.argv[1])
