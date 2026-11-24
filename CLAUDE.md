# sosai-teiten（葬祭ビジネス定点）

## 目的
葬儀社・斎場・関連事業者向けに、公的な一次データを集計して伝えるニュースサイト。記事は「ファクト（出典つき）＋キャラクター（しずか）の見解」の形にする。企画の全体は `play\niche-news-sites`（5案の比較・共通の形式）にある。

## 公開
- GitHub: 匿名アカウント `pocketlog-note` の公開リポジトリ `sosai-teiten`（ユーザー判断で入札ウォッチ・ポケットログと同じアカウント）。公開URL: https://pocketlog-note.github.io/sosai-teiten/
- Pages の公開元は「GitHub Actions」（設定済み）。`main` へ push すると `.github/workflows/pages.yml` が点検→ビルド→公開する（毎朝6時にも実行され、`date` が今日になった記事が公開される）。
- コミットの作者は `pocketlog-note` と noreply アドレス（ローカル設定済み）。個人のメールアドレスを出さない。
- GitHub の操作（リポジトリ作成・Pages設定）は、ユーザーが Chrome でサインイン済みのため Claude in Chrome で行った（ユーザー許可 2026-11-24）。パスワードは扱わない。

## 記事の基準
- **本文は3,000〜8,000文字（SEOブログ記事の目安。ユーザー指示 2026-11-24）。** `site/check.py` が3,000字未満をエラー、8,000字超を注意にする。水増しはしない。ファクトを増やして長くする。
- 記事は「ファクト（出典つき）」と「しずかの見解」を分ける。意見は見解欄だけ。
- しずかの文体: です・ます調で静かに丁寧に。冗談・感嘆符・不安をあおる表現は使わない。死を軽く扱わない。見解欄は「わたし」を使ってよい。
- 数字は必ず `data/` の検算済みCSVから `data/figures.py` で算出して写す（手で打たない）。記事を書く前に `python -X utf8 data/verify_deaths.py` を通す。
- 書いたら yomiyasu で推敲・検査する。`python -X utf8 tools/export_text.py site/content/<記事>.md _text/<名前>-final.md` で文章だけ取り出し、資料（`_text/<名前>-material.md`）と一緒に `yomiyasu_check.py run --material ... --final ... --doc-type article --stance 説明 --fact-gaps` → `verify`。

## データ源と利用条件
- **厚生労働省「人口動態統計月報（概数）」**（死亡数）。最新は令和8年6月分（2026-11-04公表）。ページ: https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/m2026/06.html
  - 利用条件: 「公共データ利用規約（第1.0版）」（https://www.mhlw.go.jp/chosakuken/index.html）。出典を記載する。加工した場合は加工した旨を書く。国が作成したかのように見せない。記事の末尾・about・フッターに記載済み。
  - 一覧フォルダ（`.../s2026/`、`.../m2026/`）は 403。個別ページは通常のブラウザで開ける。PDF・Excel の URL はダウンロードになる。**ファイルのダウンロードはユーザーの許可が要る。**2026-11-24 に `xlsx/6-18.xlsx`（24KB）と `dl/toukeihyo_06.pdf`（5.9MB）の2つだけ許可を得て取得した（`data/raw/`、git管理外）。
  - 月別の死亡数は PDF 第2表から `data/deaths_monthly.csv` に写した（検算済み）。過去1年間の合計は xlsx から `data/import_rolling.py` で `data/deaths_rolling12.csv` にした。
- **東京都保健医療局「東京の火葬場について」**（2026-06-19更新）。サイトポリシー（https://www.hokeniryo.metro.tokyo.lg.jp/policy）: 掲載資料は個人的・非営利の使用に限り複製・使用でき、転載・変更・配布等は事前の許可が必要。リンクはトップページのみ自由（個別ページへのリンクは事前許諾）。→ 記事では数字を自分の言葉で書いて出典を文章で示し、表やグラフの複写はしない。リンクはトップページだけ。**広告などで収益化する場合は、事前に東京都へ問い合わせて許可を得る。**
- 斎場の空き枠を全国まとめて取れる公開データはない（さいたま市・西宮市・札幌市などが自治体ごとに予約画面を公開しているだけ）。`mockup\04-sosai.html` の「斎場32か所を4週間記録」は**架空**で、公開してはいけない。

## よく使うコマンド（プロジェクトのルートで。`python -X utf8` を付けると文字化けしない）
- 検算: `python -X utf8 data/verify_deaths.py`／数値の算出: `python -X utf8 data/figures.py`
- 点検・ビルド（site フォルダで）: `python -X utf8 check.py`（`--all` で下書きも）、`python -X utf8 build.py`、`$env:INCLUDE_DRAFTS=1; python -X utf8 build.py`
- X 投稿文の下書きは `site/x-drafts/`（投稿は人が行う）。

## ファイル構成
- `site/` サイト生成（build.py・check.py・style.css・content/*.md・pages/*.md）。入札ウォッチ（`play\niche-news-sites\site`）から複製して葬祭向けに直したもの。
- `data/` 死亡数のCSV、取り込み・検算・算出のスクリプト。`tools/` アイキャッチ生成・文章の取り出し。`_text/` yomiyasu の資料と最終稿。`mockup/` 最初のモックアップ（数字は架空）。

## メモ・決定事項
- 2026-11-24 プロジェクト作成。最初の記事「2026年上半期の死亡数は766,746人」（5,177字）を公開。
- 未解決: 次の月のデータ取得（新しい月報のPDF/Excelはダウンロードになるため、毎回ユーザーの許可が要る。許可を得て定期化するか、e-Stat 等の別の取得方法を調べる）。
- 未解決: 東京都の資料を使うことへの許可（収益化する場合）。ポリシー上、個人的・非営利の範囲では複製・使用できるが、転載等は許可が要る。
- 2026-11-25 定期タスク `sosai-teiten-monthly`（毎月10日・25日の13時ごろ。Auto モード）を登録（ユーザー指示「定期的に自動的に更新するために登録」）。手順は `plan/operations.md`、履歴は `plan/log.md`。ファイルのダウンロードはしない方針のため、月報の数字が HTML で読めない月は、許可が要るファイルを記録して止まる。完全に自動にするには、ダウンロードの許可の扱いか、別の取得方法（e-Stat API など。利用登録が要る）を決める必要がある。
