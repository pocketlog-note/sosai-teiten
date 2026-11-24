"""記事で使う数値（増減・増減率・1日あたり・割合）を、検算済みの CSV から計算して表示する。
記事の数字は、手計算ではなくこの出力から写す。

使い方（プロジェクトのルートで実行）:
  python -X utf8 data/figures.py
"""
import calendar
import csv
from pathlib import Path

D = Path(__file__).parent


def read(name):
    with (D / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


monthly = {(int(r["year"]), int(r["month"])): int(r["deaths"]) for r in read("deaths_monthly.csv")}
roll = {(int(r["year"]), int(r["month"])): {k: int(r[k]) for k in ("total", "male", "female")} for r in read("deaths_rolling12.csv")}


def pct(a, b):
    return round((a - b) * 100 / b, 1)


print("== 月別（2025→2026）")
for m in range(1, 7):
    a, b = monthly[(2025, m)], monthly[(2026, m)]
    print(f"{m}月 {a:,} → {b:,}  差 {b - a:+,}  {pct(b, a):+}%")
h25, h26 = sum(monthly[(2025, m)] for m in range(1, 7)), sum(monthly[(2026, m)] for m in range(1, 7))
print(f"1〜6月累計 {h25:,} → {h26:,}  差 {h26 - h25:+,}  {pct(h26, h25):+}%")
y25 = sum(monthly[(2025, m)] for m in range(1, 13))
second = y25 - h25
print(f"2025年 年間 {y25:,}  上半期 {h25:,}（{h25 * 100 / y25:.1f}%） 下半期 {second:,}（{second * 100 / y25:.1f}%）")

print("== 1日あたり（月の死亡数÷日数）")
for y in (2025, 2026):
    for m in range(1, 13):
        if (y, m) in monthly:
            days = calendar.monthrange(y, m)[1]
            print(f"{y}年{m}月 {monthly[(y, m)]:,}人 ÷{days}日 = {monthly[(y, m)] / days:,.0f}人/日")

print("== 月別の最大・最小")
for y in (2025, 2026):
    ms = {m: v for (yy, m), v in monthly.items() if yy == y}
    mx, mn = max(ms, key=ms.get), min(ms, key=ms.get)
    print(f"{y}年 最多 {mx}月 {ms[mx]:,} / 最少 {mn}月 {ms[mn]:,} / 比 {ms[mx] / ms[mn]:.2f}")
print(f"2026年1月/6月 = {monthly[(2026, 1)] / monthly[(2026, 6)]:.2f}")

print("== 過去1年間の合計（総数・男・女）")
for key in ((2024, 6), (2025, 6), (2025, 12), (2026, 6)):
    r = roll[key]
    print(f"{key[0]}年{key[1]}月 総数 {r['total']:,} 男 {r['male']:,} 女 {r['female']:,}")
a, b = roll[(2025, 6)]["total"], roll[(2026, 6)]["total"]
print(f"過去1年間 2025年6月→2026年6月 {a:,} → {b:,}  差 {b - a:+,}  {pct(b, a):+}%")
a = roll[(2024, 6)]["total"]
print(f"過去1年間 2024年6月→2026年6月 {a:,} → {b:,}  差 {b - a:+,}  {pct(b, a):+}%")
print("過去1年間の合計が最大だった月:", max(roll, key=lambda k: roll[k]["total"]), max(v["total"] for v in roll.values()))
r = roll[(2026, 6)]
print(f"男 {r['male'] * 100 / r['total']:.1f}% 女 {r['female'] * 100 / r['total']:.1f}%")
