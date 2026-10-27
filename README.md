# IT・AI ニュース ダッシュボード

仕事中に iPad mini でさっと IT / AI ニュースを確認するための、**1 画面完結型**のダッシュボードです。

| 縦向き (2×2) | 横向き (4 列) |
| --- | --- |
| AI / 国内 IT / 海外テック / エンジニアトレンド を 2×2 で表示 | AI 列を少し広くして 4 列で表示 |

- ページ全体はスクロールせず、各パネルだけが個別にスクロールします
- 2 時間以内の記事に `NEW` バッジ、タップした記事は既読としてグレー表示（未読数をパネルに表示）
- AI 関連キーワード（生成AI, LLM, ChatGPT, Claude, Gemini など）を含む記事は、国内/海外フィードからでも「AI」パネルに集約
- ライト / ダーク / 自動（端末設定に追従）切り替え
- 10 分ごと・画面復帰時に自動で最新データを再読み込み
- ホーム画面に追加するとアプリのように全画面表示

## 仕組み

```
GitHub Actions (30 分ごと)
  └─ scripts/fetch_news.py が scripts/feeds.json の RSS を取得
       └─ site/news.json を生成
            └─ site/ を GitHub Pages にデプロイ
iPad mini の Safari → https://<ユーザー名>.github.io/my-first-up/
```

ブラウザから直接 RSS を読むと CORS で弾かれるサイトが多いため、サーバー側（Actions）でまとめて JSON にしています。
サーバー代は不要で、Python 標準ライブラリのみで動きます。

## セットアップ（最初に 1 回だけ）

1. このブランチを `main` にマージする（定期実行 `schedule` は main ブランチでのみ動きます）
2. GitHub のリポジトリ画面 → **Settings → Pages → Build and deployment → Source** を **GitHub Actions** に変更
3. **Actions** タブ → 「Update news dashboard」→ **Run workflow** で初回実行
4. 完了後、`https://<ユーザー名>.github.io/my-first-up/` を iPad mini の Safari で開く
5. 共有ボタン → **ホーム画面に追加** でアプリのように使えます

> 注: GitHub Pages はリポジトリが Public であれば無料プランで使えます（Private の場合は有料プランが必要）。

## ニュースソースの追加・変更

`scripts/feeds.json` を編集するだけです。`category` は次の 4 つから選びます。

| category | 表示パネル |
| --- | --- |
| `ai` | AI |
| `jp` | 国内 IT |
| `global` | 海外テック |
| `trend` | エンジニア トレンド |

例: Publickey の代わりに「窓の杜」を追加する場合

```json
{ "name": "窓の杜", "url": "https://forest.watch.impress.co.jp/data/rss/1.0/wf/feed.rdf", "category": "jp" }
```

| 項目 | 意味 |
| --- | --- |
| `country` | 発信元の国コード（`US` `GB` `DE` `CN` など）。`JP` 以外は記事に国旗を表示 |
| `translate` | `true` にすると見出しを日本語に翻訳し、原文を小さく併記 |

例: 韓国のテックメディアを海外テックに追加する場合（URL はそのサイトの RSS に置き換え）

```json
{ "name": "（サイト名）", "url": "https://example.com/feed.xml", "category": "global", "country": "KR", "translate": true }
```

翻訳には Google 翻訳の公開エンドポイント（API キー不要）を使っています。
非公式の仕組みのため、まれに失敗することがあり、その場合は原文の英語のまま表示されます。

RSS 2.0 / Atom / RSS 1.0 (RDF) のいずれにも対応しています。取得に失敗したフィードは画面右上に「取得失敗: ○○」と表示されます。

## ローカルで試す

```bash
python3 scripts/fetch_news.py      # site/news.json を生成
cd site && python3 -m http.server 8000
# → http://localhost:8000 を開く
```

## ニュースが更新されないとき

- 画面右上の「○○:○○ 取得」が、サーバー側でニュースを集めた時刻です。90 分以上前だと赤字で警告が出ます。
- ↻ ボタンは「サーバーにある最新データを読み直す」ボタンです。サーバー側の取得（15 分ごと）が動いていないと、押しても内容は変わりません。
- GitHub の定期実行は混雑時に遅れたり、スキップされたりすることがあります。すぐ最新にしたいときは、
  GitHub の **Actions** タブ → 「Update news dashboard」→ **Run workflow** で手動実行できます（スマホの GitHub アプリからも可能）。
