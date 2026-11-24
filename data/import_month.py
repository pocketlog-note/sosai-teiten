"""新しい月報の Excel（過去1年間の動向）を取り込み、新しい月の死亡数を data/deaths_monthly.csv に足す。

使い方（プロジェクトのルートで実行）:
  python -X utf8 data/import_month.py data/raw/<年>-<月>-18.xlsx

仕組み: 過去1年間の合計は、その月で「前年同月の分が抜け、当月の分が入る」。
  当月の死亡数 ＝ 当月の過去1年間の合計 − 前月の過去1年間の合計 ＋ 前年同月の死亡数
2026年1〜6月の6か月分で、この計算が月報の第2表の値と完全に一致することを確かめてある。
前年同月の死亡数が CSV にない月は計算しない。

止まる条件（人が確かめる）:
  - すでに保存してある過去1年間の合計と、新しい Excel の値が食い違う（数字が改訂された可能性）
  - 取り込み後の検算（data/verify_deaths.py）が通らない
"""
import csv
import sys
from pathlib import Path

import import_rolling as ir

HERE = Path(__file__).parent
MONTHLY = HERE / "deaths_monthly.csv"


def read_monthly():
    with MONTHLY.open(encoding="utf-8") as f:
        return {(int(r["year"]), int(r["month"])): int(r["deaths"]) for r in csv.DictReader(f)}


def main(path):
    new = ir.parse_rolling(path)
    old = ir.read_rolling_csv()
    conflicts = [(k, old[k], new[k]) for k in new if k in old and old[k] != new[k]]
    if conflicts:
        for k, o, n in conflicts[:5]:
            print(f"食い違い: {k[0]}年{k[1]}月 保存済み {o} ／ 新しいExcel {n}")
        print("保存済みの値と食い違います。数字が改訂された可能性があるため、取り込まずに止まります")
        return 2
    merged = {**old, **new}
    ir.write_rolling(merged)

    monthly = read_monthly()
    year = max(y for y, _ in new)
    added = []
    for m in range(1, 13):
        k = (year, m)
        if k not in new or k in monthly:
            continue
        prev = (year, m - 1) if m > 1 else (year - 1, 12)
        same_last = (year - 1, m)
        if prev not in merged or same_last not in monthly:
            print(f"{year}年{m}月は、前月の過去1年間の合計か前年同月の死亡数がないため、計算しません")
            continue
        monthly[k] = merged[k]["total"] - merged[prev]["total"] + monthly[same_last]
        added.append(k)
    if added:
        with MONTHLY.open("a", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            for (y, m) in added:
                w.writerow([y, m, monthly[(y, m)], f"月報(概数)令和{y - 2018}年{m}月分「過去1年間の動向」から算出（過去1年間の合計の増減＋前年同月の死亡数）"])
                print(f"追加: {y}年{m}月の死亡数 {monthly[(y, m)]:,}人")
    else:
        print("追加する月はありません（すでに取り込み済みです）")

    import verify_deaths
    return verify_deaths.main()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
