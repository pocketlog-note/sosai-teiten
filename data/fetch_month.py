"""次の月の月報（概数）が公表されているかを確かめ、許可があれば Excel を1つ取得して取り込む。標準ライブラリだけで動く。

使い方（プロジェクトのルートで実行）:
  python -X utf8 data/fetch_month.py                     公表されているかと、Excel の名前・URL を確かめるだけ（保存しない）
  python -X utf8 data/fetch_month.py --allow-download    公表されていれば Excel（約24KB）を data/raw/ に保存し、取り込む
  python -X utf8 data/fetch_month.py --month 2026-06     確かめる月を指定する（動作確認用）

終了コード: 0 成功（取り込み済み・新しい月あり）／3 まだ公表されていない／4 取得にユーザーの許可が要る／5 想定外（ページの構成が変わった等）

ダウンロードについて（plan/operations.md に許可の状態を記録している）:
  - 取得するのは「当月分を含む過去1年間の動向」の Excel 1つだけ（約24KB）。厚生労働省のサイトだけ。
  - ユーザーの許可がある間だけ、定期タスクが --allow-download を付けて実行する。許可がなければ付けない。
  - 厚生労働省のページは通常のスクリプトで読める。User-Agent は正直に名乗る。続けて何度も取りに行かない（1回の実行で1ページ＋1ファイル）。
"""
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
BASE = "https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/"
UA = "sosai-teiten-collector/0.1"
MAX_BYTES = 300_000


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=60).read()


def plain(html):
    return unicodedata.normalize("NFKC", re.sub(r"<[^>]+>", " ", html))


def next_month():
    import import_month
    last = max(import_month.read_monthly())
    return (last[0], last[1] + 1) if last[1] < 12 else (last[0] + 1, 1)


def main(argv):
    allow = "--allow-download" in argv
    if "--month" in argv:
        y, m = (int(x) for x in argv[argv.index("--month") + 1].split("-"))
    else:
        y, m = next_month()
    page = f"{BASE}m{y}/{m:02d}.html"
    try:
        body = get(page)
        try:
            html = body.decode("utf-8")
        except UnicodeDecodeError:
            html = body.decode("cp932", "replace")   # 厚生労働省のこのページは Shift_JIS
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"{y}年{m}月分の月報はまだ公表されていません（{page} が404）")
            return 3
        print(f"ページを取得できませんでした: {e}")
        return 5
    except Exception as e:  # noqa: BLE001
        print(f"ページを取得できませんでした: {e}")
        return 5

    text = re.sub(r"\s+", "", plain(html))
    pub = re.search(r"令和(\d+)年(\d+)月(\d+)日", text)
    if not pub:
        print("公表日を読み取れませんでした。ページの構成が変わった可能性があります")
        return 5
    pub_iso = f"{int(pub.group(1)) + 2018}-{int(pub.group(2)):02d}-{int(pub.group(3)):02d}"

    link = None
    for href, inner in re.findall(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
        if "過去1年間の動向" in re.sub(r"\s+", "", plain(inner)):
            link = urllib.parse.urljoin(page, href)
            break
    if not link or not link.lower().endswith(".xlsx"):
        print("「当月分を含む過去1年間の動向」のExcelのリンクを見つけられませんでした")
        return 5

    print(f"対象: {y}年{m}月分")
    print(f"ページ: {page}")
    print(f"PUB_DATE={pub_iso}")
    print(f"Excel: {link}")
    if not allow:
        print("ダウンロードにはユーザーの許可が要ります（--allow-download が付いていないため、保存しません）")
        return 4

    raw = HERE / "raw"
    raw.mkdir(exist_ok=True)
    dst = raw / f"{y}-{m:02d}-18.xlsx"
    body = get(link)
    if len(body) > MAX_BYTES or not body.startswith(b"PK"):
        print(f"想定と違うファイルです（{len(body)}バイト）。保存せずに止まります")
        return 5
    dst.write_bytes(body)
    print(f"保存: {dst.name}（{len(body):,}バイト）")

    sys.path.insert(0, str(HERE))
    import import_month
    rc = import_month.main(dst)
    return 0 if rc == 0 else 5


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    sys.exit(main(sys.argv[1:]))
