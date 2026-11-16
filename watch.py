"""
SixTONES公式サイトの新着ニュースを監視し、Slackに通知する。
- sixtones.jp/news/<番号> を連番でチェック（前回の番号+1から）
- 新しい記事があればSlackへ投稿。日程・ドーム関連キーワードを含めば @channel 付きで強調
- 依存ライブラリなし（Python標準ライブラリのみ）

使い方:
  python watch.py            # 通常の監視（GitHub Actionsから定期実行）
  python watch.py --test 479 # 指定番号の記事でSlack通知をテスト（状態は更新しない）
"""
import html, json, os, re, sys, urllib.request, urllib.error

BASE = "https://sixtones.jp/news/"
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")
LOOKAHEAD = 5  # 番号が飛ぶ場合に備え、先の番号もいくつか確認する
KEYWORDS = ["日程", "公演", "東京ドーム", "ナゴヤドーム", "バンテリン", "ドーム",
            "AHEAD", "アマヘッド", "チケット", "先行", "会場"]
WEBHOOK = os.environ.get("SLACK_WEBHOOK_URL", "")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")


def fetch(news_id):
    """記事があれば {id,url,title,desc,text} を、なければ None を返す"""
    url = f"{BASE}{news_id}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ja"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            if r.status != 200 or not r.geturl().rstrip("/").endswith(f"/news/{news_id}"):
                return None  # トップ等へリダイレクト＝記事なし
            body = r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            return None
        raise

    def meta(prop):
        m = re.search(rf'<meta[^>]+(?:property|name)=["\']{prop}["\'][^>]+content=["\']([^"\']*)', body, re.I) \
            or re.search(rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']{prop}["\']', body, re.I)
        return html.unescape(m.group(1)).strip() if m else ""

    title = meta("og:title")
    if not title:
        m = re.search(r"<title>(.*?)</title>", body, re.I | re.S)
        title = html.unescape(m.group(1)).strip() if m else ""
    # 中身のないページ（サイト名だけのタイトル）は記事なしとみなす
    if not title or "|" not in title and "｜" not in title:
        return None
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", body, flags=re.S | re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    text = re.sub(r"\s+", " ", text)
    return {"id": news_id, "url": url, "title": title, "desc": meta("og:description"), "text": text}


def notify(article):
    hits = [k for k in KEYWORDS if k in article["title"] or k in article["text"]]
    head = "<!channel> :rotating_light: *SixTONES 日程・ドーム関連の可能性あり*" if hits else ":newspaper: SixTONES 新着ニュース"
    msg = f"{head}\n*{article['title']}*\n{article['desc']}\n{article['url']}"
    if hits:
        msg += f"\nヒットしたキーワード: {', '.join(hits)}\n→ 該当日の料金・在庫をすぐ確認してください"
    print(msg)
    if not WEBHOOK:
        print("（SLACK_WEBHOOK_URL未設定のため送信スキップ）")
        return
    data = json.dumps({"text": msg}).encode()
    req = urllib.request.Request(WEBHOOK, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=20).read()


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--test":
        a = fetch(int(sys.argv[2]))
        if a:
            notify(a)
        else:
            print("記事が見つかりません")
        return

    with open(STATE_FILE, encoding="utf-8") as f:
        state = json.load(f)
    last = state["last_id"]
    newest = last
    for nid in range(last + 1, last + 1 + LOOKAHEAD):
        a = fetch(nid)
        if a:
            notify(a)
            newest = nid
    if newest != last:
        state["last_id"] = newest
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        print(f"last_id: {last} -> {newest}")
    else:
        print(f"新着なし（last_id={last}）")


if __name__ == "__main__":
    main()
