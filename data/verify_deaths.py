"""死亡数のデータ（CSV）を検算する。記事を書く前に必ず実行する。

使い方（プロジェクトのルートで実行）:
  python -X utf8 data/verify_deaths.py

検算の内容:
  [共通] 毎年の月について、「過去1年間の合計の増減 ＝ 月別死亡数の前年同月差」が成り立つ
  [共通] 男＋女 ＝ 総数
  [共通] ある年の12か月分の合計 ＝ その年12月時点の過去1年間の合計（その年が12か月そろっているとき）
  [基準値] 月報（概数）令和8年6月分の中の値（第1表の累計 766,746人・823,343人、6月 113,355人・114,709人）
          1〜6月がそろっている間だけ照らす。食い違うときは数字が改訂された可能性があるので、人が確かめる
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
        print(("OK  " if ok else "NG  ") + f"{label}: {got:,}" + ("" if ok else f"（期待する値 {want:,}）"))
        if not ok:
            ng.append(label)

    # 基準値
    if all((2026, m) in monthly and (2025, m) in monthly for m in range(1, 7)):
        check("【基準】2026年1〜6月の累計", sum(monthly[(2026, m)] for m in range(1, 7)), 766746)
        check("【基準】2025年1〜6月の累計", sum(monthly[(2025, m)] for m in range(1, 7)), 823343)
        check("【基準】2026年6月", monthly[(2026, 6)], 113355)
        check("【基準】2025年6月", monthly[(2025, 6)], 114709)

    years = sorted({y for y, _ in monthly})
    for y in years:
        if all((y, m) in monthly for m in range(1, 13)) and (y, 12) in roll:
            check(f"{y}年の年間（月別の合計）＝{y}年12月時点の過去1年間", sum(monthly[(y, m)] for m in range(1, 13)), int(roll[(y, 12)]["total"]))
    for y in years:
        if not all((y - 1, m) in monthly for m in range(1, 13)):
            continue
        for m in range(1, 13):
            prev = (y, m - 1) if m > 1 else (y - 1, 12)
            if (y, m) in monthly and (y, m) in roll and prev in roll:
                now = int(roll[(y, m)]["total"]) - int(roll[prev]["total"])
                check(f"{y}年{m}月の過去1年間の合計の増減 ＝ 前年同月差", now, monthly[(y, m)] - monthly[(y - 1, m)])
    bad = [k for k, r in roll.items() if int(r["male"]) + int(r["female"]) != int(r["total"])]
    for k in bad:
        print("NG  男+女≠総数", k)
        ng.append(f"{k} 男+女≠総数")
    print("男女の合計が総数と一致:", "すべて OK" if not bad else "不一致あり")
    if ng:
        print("検算に失敗しました。記事を書かないでください")
        return 1
    print("検算はすべて通りました")
    return 0


if __name__ == "__main__":
    sys.exit(main())
