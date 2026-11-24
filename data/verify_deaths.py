"""死亡数のデータ（CSV）を、出典の別の表の合計と照らして検算する。記事を書く前に必ず実行する。

使い方（プロジェクトのルートで実行）:
  python -X utf8 data/verify_deaths.py

照らす先（すべて厚生労働省「人口動態統計月報（概数）令和8（2026）年6月分」の中の値）:
  - 第1表の「累計1月〜6月」: 2026年 766,746人、2025年 823,343人
  - 第1表の6月: 2026年 113,355人、2025年 114,709人
  - xlsx「過去1年間の動向」: 2025年12月時点の過去1年間＝2025年の年間死亡数 1,589,489人
  - xlsx の過去1年間の合計の月ごとの増減 ＝ 月別死亡数の前年同月差（2026年1〜6月）
  - 男＋女 ＝ 総数
"""
import csv
import sys
from pathlib import Path

D = Path(__file__).parent


def read(name):
    with (D / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    monthly = {(int(r["year"]), int(r["month"])): int(r["deaths"]) for r in read("deaths_monthly.csv")}
    roll = {(int(r["year"]), int(r["month"])): r for r in read("deaths_rolling12.csv")}
    ng = []

    def check(label, got, want):
        ok = got == want
        print(("OK  " if ok else "NG  ") + f"{label}: {got:,}" + ("" if ok else f"（出典の値 {want:,}）"))
        if not ok:
            ng.append(label)

    check("2026年1〜6月の累計", sum(monthly[(2026, m)] for m in range(1, 7)), 766746)
    check("2025年1〜6月の累計", sum(monthly[(2025, m)] for m in range(1, 7)), 823343)
    check("2026年6月", monthly[(2026, 6)], 113355)
    check("2025年6月", monthly[(2025, 6)], 114709)
    check("2025年の年間（月別の合計）", sum(monthly[(2025, m)] for m in range(1, 13)), 1589489)
    check("2025年12月時点の過去1年間の合計（xlsx）", int(roll[(2025, 12)]["total"]), 1589489)
    prev = int(roll[(2025, 12)]["total"])
    for m in range(1, 7):
        now = int(roll[(2026, m)]["total"])
        check(f"2026年{m}月の過去1年間の合計の増減 ＝ 前年同月差", now - prev, monthly[(2026, m)] - monthly[(2025, m)])
        prev = now
    for k, r in roll.items():
        if int(r["male"]) + int(r["female"]) != int(r["total"]):
            ng.append(f"{k} 男+女≠総数")
            print("NG  男+女≠総数", k)
    print("男女の合計が総数と一致:", "すべて OK" if not any("男+女" in x for x in ng) else "不一致あり")
    if ng:
        print("検算に失敗しました。記事を書かないでください")
        return 1
    print("検算はすべて通りました")
    return 0


if __name__ == "__main__":
    sys.exit(main())
