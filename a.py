import csv # csvはよく使うから何のことかわかりやすくするためにcsv.⚪︎⚪︎の形で使う
from urllib.parse import urljoin, urlparse # 大きな道具箱から取り出している
import time                                # 道具＝ライブラリ
import requests
from bs4 import BeautifulSoup

# 定義　＜よく出てくるやつ＞
base_url = "https://www.musashino-u.ac.jp"
domain = urlparse(base_url).netloc  # urlpaseは分解処理　.netlocはドメインのこと

# データを格納する変数
site_map = {}  # 「辞書型」の空っぽの箱を用意
visited_urls = set()  # 無限ループ阻止　set()は「集合型」＝「同じ値を重複してはいけない」処理
urls_to_visit = [
    base_url
]  # これからアクセスするURLのリスト =[]これは「リスト型」

# 数上限（200個）
MAX_PAGES = 200
crawled_count = 0

print("クローリングを開始します...")

# 探索するURLが残っていて、かつ最大ページ数に達していない間ループ
while urls_to_visit and crawled_count < MAX_PAGES: #　whileは条件を繰り返す
    # リストの先頭からURLを1つ取り出す
    current_url = urls_to_visit.pop(0)

    # 既に訪問済みの場合はスキップ
    if current_url in visited_urls:
        continue

    print(f"[{crawled_count + 1}] アクセス中: {current_url}")

    try:
        # 1. サイトにアクセス
        res = requests.get(current_url, timeout=10)
        visited_urls.add(current_url)  # 訪問済みに記録

        # ★【重要】サーバーへの負荷軽減のためのスリープ
        time.sleep(1)

        # ステータスコードが200以外の場合はスキップ
        if res.status_code != 200:
            continue

        # PDFや画像ではなく、HTMLペーの場合のみ処理
        if "text/html" not in res.headers.get("Content-Type", ""):
            continue

        # 2. BeautifulSoupで解析
        res.encoding = res.apparent_encoding  # 文字化け対策
        soup = BeautifulSoup(res.text, "html.parser")

        # 3. タイトルを取得して辞書に　格納＝保存するってこと！
        title_tag = soup.find("title")
        title = title_tag.text.strip() if title_tag else "No Title"
        site_map[current_url] = title # ここ！で{url：タイトル}がセットで保存の設定
        crawled_count += 1

        # 4. ページ内のすべてのリンク(aタグ)を抽出
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()

            # javascript: や mailto: 等の特殊リンクを除外
            if href.startswith(("javascript:", "mailto:", "tel:")):
                continue

            # 相対パス（/about/等）を絶対URL（https://.../about/）に変換
            full_url = urljoin(current_url, href)

            # URL内の「#」以降（ページ内リンク）を削除（同一ページへの重複アクセス防止）
            full_url = full_url.split("#")[0]

            # 抽出したURLが同一ドメインかチェック
            parsed_url = urlparse(full_url)
            if parsed_url.netloc == domain:
                # まだ訪問しておらず、次に訪問するリストにも入っていないURLだけを追加
                if (
                    full_url not in visited_urls
                    and full_url not in urls_to_visit
                ):
                    # PDFなどのファイルのリンクは除外（HTMLのみ辿る）
                    if not full_url.lower().endswith(
                        (
                            ".pdf",
                            ".jpg",
                            ".jpeg",
                            ".png",
                            ".gif",
                            ".zip",
                            ".docx",
                            ".xlsx",
                        )
                    ):
                        urls_to_visit.append(full_url)

    except requests.exceptions.RequestException as e:
        print(f"  通信エラー発生（スキップします）: {e}")
        visited_urls.add(current_url)

print(f"\n合計 {crawled_count} ページの情報を取得しました。")

# 5. 辞書型変数をCSVファイルに保存
csv_filename = "sitemap.csv"

# 'utf-8-sig' で保存するとExcelで開いても日本語が文字化けしません
with open(csv_filename, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)
    # 1行目のヘッダー
    writer.writerow(["URL", "Title"])

    # 辞書(site_map)からURLとタイトルを取り出して1行ずつ書き込む
    for url, title in site_map.items():
        writer.writerow([url, title])

print(f"CSVファイル '{csv_filename}' への保存が完了しました！")

