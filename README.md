# SixTONES ニュース監視 → Slack通知

sixtones.jp/news を10分ごとにチェックし、新着記事が出たらSlackに投稿します。
「日程」「東京ドーム」「ナゴヤドーム」「バンテリン」「チケット」などを含む記事は @channel 付きで通知。

## セットアップ（10分くらい）
1. GitHubで新しいリポジトリ（Privateで可）を作り、このフォルダの中身をすべてアップロード
   （`.github/workflows/watch.yml` も忘れずに）
2. Slackで Incoming Webhook を作成し、通知したいチャンネルのWebhook URLを取得
   （Slack App管理画面 → Create App → Incoming Webhooks → Add New Webhook）
3. リポジトリの Settings → Secrets and variables → Actions → New repository secret
   名前 `SLACK_WEBHOOK_URL`、値に上のURL
4. Actionsタブ → 「SixTONES news watch」→ Run workflow で手動実行して動作確認

## 動作テスト
手元で `python watch.py --test 479` を実行すると、既存の479番の記事で通知文を確認できます
（環境変数 SLACK_WEBHOOK_URL を入れておけば実際にSlackへ届きます）。

## 調整
- キーワード：`watch.py` の `KEYWORDS`
- 頻度：`watch.yml` の cron（`*/5` で5分ごと）
- 監視開始番号：`state.json` の `last_id`

## 注意
- 公式サイトの作りが変わると検知できなくなる可能性があります。
- 60日間リポジトリに更新がないとGitHubが定期実行を止めますが、新着のたびにstate.jsonが更新されるので通常は問題なし。
