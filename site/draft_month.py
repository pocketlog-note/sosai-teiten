"""月報（概数）の1か月分の記事の下書きを、検算済みCSVから作る。数字は手で打たず、すべてここで算出する。標準ライブラリだけで動く。

使い方（site フォルダで実行）:
  python -X utf8 draft_month.py 2026 7 --pub 2026-12-08
  python -X utf8 draft_month.py 2026 4 --pub 2026-09-08 --backfill --out ..\\_work\\sample.md   過去分として書く（日付を過去にし、その旨を記事に書く）

出力: content/<公表日>-deaths-<年>-<月2桁>.md（--out で変えられる）
  - 概要・表・グラフ・1日あたり・過去1年間の合計・注意書き・ファクト・集計方法は自動で埋まる
  - 次の2か所は【要確認】の目印だけ置く。書くか削除して目印を消すまで公開されない（check.py がエラーにする）
      「今月の火葬・葬祭の動き」の節（公的な資料で確かめた、出典つきの新しい動き。なければ節ごと削除）
      しずかの見解
  - 1月分は、累計が当月と同じになるため作らない（手で書く）
前提: data/verify_deaths.py が通っていること。
"""
import calendar
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(name):
    with (ROOT / "data" / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build(Y, K, pub, backfill=False):
    M = {(int(r["year"]), int(r["month"])): int(r["deaths"]) for r in read("deaths_monthly.csv")}
    R = {(int(r["year"]), int(r["month"])): {k: int(r[k]) for k in ("total", "male", "female")} for r in read("deaths_rolling12.csv")}
    if K < 2:
        raise SystemExit("1月分は累計が当月と同じになるため、この下書きでは作りません。手で書いてください")
    for m in range(1, K + 1):
        if (Y, m) not in M or (Y - 1, m) not in M:
            raise SystemExit(f"{Y}年{m}月か{Y - 1}年{m}月の死亡数が data/deaths_monthly.csv にありません")
    for key in ((Y - 2, K), (Y - 1, K), (Y, K)):
        if key not in R:
            raise SystemExit(f"{key[0]}年{key[1]}月の過去1年間の合計が data/deaths_rolling12.csv にありません")

    n = lambda x: f"{x:,}"
    pct = lambda a, b: round((a - b) * 100 / b, 1)
    day = lambda y, m: M[(y, m)] / calendar.monthrange(y, m)[1]
    N = Y - 2018                       # 令和の年
    pm = (Y, K - 1)                    # 前月
    c_prev = sum(M[(Y - 1, m)] for m in range(1, K + 1))
    c_now = sum(M[(Y, m)] for m in range(1, K + 1))
    cd, cp = c_prev - c_now, abs(pct(c_now, c_prev))
    v_prev, v_now = M[(Y - 1, K)], M[(Y, K)]
    vd, vp = abs(v_prev - v_now), abs(pct(v_now, v_prev))
    word = "少なく" if v_now < v_prev else "多く"
    sign = "−" if v_now < v_prev else "＋"
    cword = "少なく" if c_now < c_prev else "多く"
    r2, r1, r0 = R[(Y - 2, K)], R[(Y - 1, K)], R[(Y, K)]
    upto = {k: v for k, v in R.items() if k <= (Y, K)}
    first = min(upto)
    peak = max(upto, key=lambda k: upto[k]["total"])
    base = max(M[(Y - 1, m)] for m in range(1, K + 1))
    pub_y, pub_m, pub_d = (int(x) for x in pub.split("-"))
    pub_jp = f"{pub_m}月{pub_d}日"
    page_no = f"{K:02d}"
    url_k = f"https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/m{Y}/{page_no}.html"
    TOKYO = "https://www.hokeniryo.metro.tokyo.lg.jp/"

    def d_of(m):
        return M[(Y - 1, m)] - M[(Y, m)]

    def p_of(m):
        return abs(pct(M[(Y, m)], M[(Y - 1, m)]))

    def sg(m):
        return "−" if M[(Y, m)] < M[(Y - 1, m)] else "＋"

    rows = "".join(
        f"<tr><td>{m}月</td><td class=\"num\">{n(M[(Y - 1, m)])}</td><td class=\"num\">{n(M[(Y, m)])}</td>"
        f"<td class=\"num\">{sg(m)}{n(abs(d_of(m)))}</td><td class=\"num\">{sg(m)}{p_of(m)}%</td></tr>\n" for m in range(1, K + 1))
    rows += (f"<tr><th>1〜{K}月の累計</th><th class=\"num\">{n(c_prev)}</th><th class=\"num\">{n(c_now)}</th>"
             f"<th class=\"num\">{'−' if c_now < c_prev else '＋'}{n(abs(cd))}</th><th class=\"num\">{'−' if c_now < c_prev else '＋'}{cp}%</th></tr>\n")
    table1 = (f'<div class="tbl"><table>\n<tr><th>月</th><th class="num">{Y - 1}年（人）</th><th class="num">{Y}年（人）</th>'
              '<th class="num">増減（人）</th><th class="num">増減率</th></tr>\n' + rows + "</table></div>")
    bars = '<div class="bars">\n'
    for m in range(1, K + 1):
        for y, color in ((Y - 1, "#b9cdc4"), (Y, "#3e5c52")):
            bars += (f'<div class="row"><span>{y}年{m}月</span><div class="track"><div class="fill" '
                     f'style="width:{M[(y, m)] * 100 / base:.1f}%;background:{color}"></div></div><span>{n(M[(y, m)])}</span></div>\n')
    bars += "</div>"
    prows = "".join(f"<tr><td>{m}月</td><td class=\"num\">{day(Y - 1, m):,.0f}</td><td class=\"num\">{day(Y, m):,.0f}</td></tr>\n" for m in range(1, K + 1))
    table2 = (f'<div class="tbl"><table>\n<tr><th>月</th><th class="num">{Y - 1}年（人/日）</th><th class="num">{Y}年（人/日）</th></tr>\n'
              + prows + "</table></div>")
    rrows = "".join(
        f"<tr><td>{y}年{K}月</td><td class=\"num\">{n(r['total'])}</td><td class=\"num\">{n(r['male'])}</td><td class=\"num\">{n(r['female'])}</td></tr>\n"
        for y, r in ((Y - 2, r2), (Y - 1, r1), (Y, r0)))
    table3 = ('<div class="tbl"><table>\n<tr><th>時点</th><th class="num">総数（人）</th><th class="num">男（人）</th><th class="num">女（人）</th></tr>\n'
              + rrows + "</table></div>")
    kpi = (f'<div class="kpis"><div class="kpi"><div class="n">{n(v_now)}人</div><div class="l">{Y}年{K}月の死亡数</div></div>'
           f'<div class="kpi warn"><div class="n">{sign}{vp}%</div><div class="l">前年同月（{n(v_prev)}人）との比較</div></div>'
           f'<div class="kpi"><div class="n">{n(c_now)}人</div><div class="l">1〜{K}月の累計（前年同期比 {"−" if c_now < c_prev else "＋"}{cp}%）</div></div></div>')

    pd = M[pm]
    diff_pm = v_now - pd
    mag = abs(diff_pm)
    bub_n = f"{mag / 10000:.1f}万人" if mag >= 10000 else f"{n(mag)}人"
    bubble = f"{K - 1}月より / {bub_n}{'多め' if diff_pm > 0 else '少なめ'}"
    jan = M[(Y, 1)]
    start_roll = f"{Y - 1}年{K + 1}月" if K < 12 else f"{Y}年1月"

    src = (f"厚生労働省「人口動態統計月報（概数）（令和{N}（{Y}）年{K}月分）」（[ページ]({url_k})、{pub_y}年{pub_jp}公表）"
           "の「当月分を含む過去1年間の動向」を加工して作成")
    if backfill:
        note = (f"この記事は、令和{N}年{K}月分の月報が公表されたことを受けて、本誌が過去分としてまとめたものです。")
        lead_pre = f"同省が公表している月別の値では、"
    else:
        note = f"この記事は、令和{N}年{K}月分の月報（概数）が公表されたことを受けて書いています。"
        lead_pre = "同月報の資料から算出した月別の値では、"

    title = f"{Y}年{K}月の死亡数は{n(v_now)}人　前年同月比{vp}%{'減' if v_now < v_prev else '増'}、1〜{K}月の累計は{n(c_now)}人"
    md = f"""---
title: {title}
date: {pub}
description: 厚生労働省の人口動態統計月報（概数）をもとに、{Y}年{K}月の死亡数を整理しました。{K}月は{n(v_now)}人で前年同月より{vp}%{'少なく' if v_now < v_prev else '多く'}、1〜{K}月の累計は前年同期比{cp}%{'減' if c_now < c_prev else '増'}です。
category: 数字を読む｜死亡数（{K}月分）
big: {v_now / 10000:.1f}万人
big_color: #3e5c52
lines: {Y}年{K}月の死亡数 / 前年同月比 {vp}%{'減' if v_now < v_prev else '増'}
bubble: {bubble}
x_text: 【今日の数字】{Y}年{K}月の死亡数は{n(v_now)}人。前年同月より{vp}%{'少なく' if v_now < v_prev else '多く'}なりました。1〜{K}月の累計は{n(c_now)}人で、前年同期比{cp}%{'減' if c_now < c_prev else '増'}です。（厚生労働省 人口動態統計）
---

厚生労働省が{pub_y}年{pub_jp}に、人口動態統計月報（概数）の令和{N}年{K}月分を公表しました。{lead_pre}{Y}年{K}月の死亡数は{n(v_now)}人で、{Y - 1}年{K}月（{n(v_prev)}人）より{n(vd)}人、{vp}%{word}なっています。1月から{K}月までの累計は{n(c_now)}人で、前年同期（{n(c_prev)}人）より{n(abs(cd))}人、{cp}%{cword}なりました。

{kpi}

{note}月別の死亡数は、同じ月報の「当月分を含む過去1年間の動向」にある過去1年間の合計の増減に、前年同月の死亡数を足して算出しています。前年以前の月別の値は、令和8年6月分の月報（第2表）などから取っています。

## {Y}年{K}月の死亡数は{n(v_now)}人　前年同月より{vp}%{word}なった

死亡数は、葬儀や火葬の需要を考えるときの手がかりの一つです。ただし、葬儀や火葬の件数そのものを数えた統計ではない点には注意が必要です。

{Y}年{K}月の死亡数は{n(v_now)}人で、前年同月の{n(v_prev)}人より{n(vd)}人、{vp}%の{'減少' if v_now < v_prev else '増加'}でした。1月（{n(jan)}人）と比べると{n(abs(jan - v_now))}人{'少なく' if v_now < jan else '多く'}、{K - 1}月（{n(pd)}人）と比べると{n(mag)}人{'多く' if diff_pm > 0 else '少なく'}なっています。

## 1〜{K}月の月別の死亡数　{Y - 1}年と{Y}年を比べる

1月から{K}月までの月ごとに{Y - 1}年と{Y}年を比べます。

{table1}

次のグラフは月別の死亡数を、{Y - 1}年1〜{K}月で最も多い月（{n(base)}人）を100とした長さで並べたものです。薄い色が{Y - 1}年、濃い色が{Y}年です。

{bars}

## 1日あたりの死亡数で見る季節の差

月の合計はその月の日数にも左右されます。そこで、月の死亡数をその月の日数で割った「1日あたりの死亡数」も計算しました（本誌算出）。

{table2}

{Y}年は1月の1日あたり{day(Y, 1):,.0f}人に対して、{K}月は{day(Y, K):,.0f}人でした。差は{abs(round(day(Y, 1)) - round(day(Y, K))):,}人です。{Y - 1}年は1月の{day(Y - 1, 1):,.0f}人から{K}月の{day(Y - 1, K):,.0f}人でした。

## 過去1年間の合計で見ると　{n(r0['total'])}人

月ごとの増減は季節の影響を受けやすいため、傾向を見るときは「当月を含む過去1年間」の合計も参考になります。たとえば{Y}年{K}月なら、{start_roll}から{Y}年{K}月までの12か月分を足した数字です。

{table3}

{Y}年{K}月までの過去1年間の死亡数は{n(r0['total'])}人で、男性が{n(r0['male'])}人、女性が{n(r0['female'])}人でした。1年前の{Y - 1}年{K}月の{n(r1['total'])}人と比べると、{n(abs(r1['total'] - r0['total']))}人（{abs(pct(r0['total'], r1['total']))}%）{'少なく' if r0['total'] < r1['total'] else '多く'}なっています。月報が示している{first[0]}年{first[1]}月から{Y}年{K}月までの範囲で、過去1年間の合計が最も大きかったのは{peak[0]}年{peak[1]}月の{n(upto[peak]['total'])}人です。{Y - 2}年{K}月の{n(r2['total'])}人と比べると、{Y}年{K}月は{n(abs(r2['total'] - r0['total']))}人（{abs(pct(r0['total'], r2['total']))}%）{'少ない' if r0['total'] < r2['total'] else '多い'}水準です。

## 【要確認】今月の火葬・葬祭の動き

【要確認】公的な資料（自治体や国の公表資料）で確かめた、今月の火葬・葬祭の動きを、出典つきで2〜3段落書く。東京都の資料は表やグラフを複写せず、数字を自分の言葉で書き、リンクはトップページだけにする。新しい動きが確かめられないときは、この節とファクト欄の対応する項目ごと削除する。

## 数字を読むときの注意

数字を使うときは、次の点に気をつけてください。

- 本稿の死亡数は「月報（概数）」の値です。概数に若干の修正を加えたものが、年報（確定数）として公表されます。{Y - 1}年の数値も概数で、のちに修正される場合があります。
- 人口動態統計は日本において発生した日本人に関する事象を集計したものです。日本人以外の人（外国人など）は含まれません。
- 月別の死亡数は、過去1年間の合計の増減と前年同月の死亡数から算出した本誌の値です。「1日あたり」の数字も、月の死亡数をその月の日数で割った本誌の算出値で、厚生労働省が公表した数字ではありません。
- 死亡数は葬儀や火葬の件数と同じではありません。

:::facts
- {Y}年{K}月の死亡数は{n(v_now)}人で、{Y - 1}年{K}月（{n(v_prev)}人）より{n(vd)}人（{vp}%）{word}なった｜{src}（月別の値は本誌が算出）
- 1〜{K}月の累計は{n(c_now)}人で、{Y - 1}年1〜{K}月（{n(c_prev)}人）より{n(abs(cd))}人（{cp}%）{cword}なった｜同（本誌が算出）
- 当月を含む過去1年間の死亡数は、{Y}年{K}月が{n(r0['total'])}人（男{n(r0['male'])}人、女{n(r0['female'])}人）、{Y - 1}年{K}月が{n(r1['total'])}人｜同
- 人口動態統計月報（概数）の令和{N}年{K}月分は{pub_y}年{pub_jp}に公表された｜厚生労働省「人口動態統計月報（概数）（令和{N}（{Y}）年{K}月分）」（[ページ]({url_k})）
- 【要確認】今月の火葬・葬祭の動きについての事実｜【要確認】出典
:::

:::opinion 【要確認】見解の見出し
【要確認】しずかの見解を2段落で書く。ファクトにない数字は書かない。静かで丁寧な文体。感嘆符・不安をあおる表現・冗談は使わない。
:::

:::next
- {Y}年{K + 1 if K < 12 else 1}月以降の死亡数が、前年の同じ月と比べてどう動くか
- 月報（概数）の次回公表分で、1〜{K + 1 if K < 12 else 1}月の累計の前年同期比がどう変わるか
:::

:::method
月別の死亡数は、厚生労働省「人口動態統計月報（概数）（令和{N}（{Y}）年{K}月分）」の「当月分を含む過去1年間の動向」にある過去1年間の合計の増減に、前年同月の死亡数を足して算出しました（過去の月で、この計算が月報の第2表の値と一致することを確かめています）。前年以前の月別の値は、令和8年6月分の月報（第2表）などの値です。月別の比較、増減率、累計、1日あたりの死亡数は本誌が算出しており、「人口動態統計月報（概数）」を加工して作成したものです。国が作成したものではありません。令和{N}年{K}月分の月報は{pub_y}年{pub_jp}に公表されています（[ページ]({url_k})）。【要確認】今月の火葬・葬祭の動きに使った資料の名称・更新日・閲覧日を書く（東京都の資料は[東京都保健医療局]({TOKYO})のトップページだけにリンクする）。
:::
"""
    return md


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = sys.argv[1:]
    if len(args) < 2 or "--pub" not in opts:
        print(__doc__)
        raise SystemExit(1)
    Y, K = int(args[0]), int(args[1])
    pub = opts[opts.index("--pub") + 1]
    backfill = "--backfill" in opts
    out = Path(opts[opts.index("--out") + 1]) if "--out" in opts else ROOT / "site" / "content" / f"{pub}-deaths-{Y}-{K:02d}.md"
    if out.exists() and "--force" not in opts:
        raise SystemExit(f"{out.name} はすでにあります（作り直すときは --force）")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(Y, K, pub, backfill), encoding="utf-8")
    print(f"下書きを作りました: {out}（【要確認】が残っている間は公開されません）")
