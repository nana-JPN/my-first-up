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

RSS 2.0 / Atom / RSS 1.0 (RDF) のいずれにも対応しています。取得に失敗したフィードは画面右上に「取得失敗: ○○」と表示されます。

## ローカルで試す

```bash
python3 scripts/fetch_news.py      # site/news.json を生成
cd site && python3 -m http.server 8000
# → http://localhost:8000 を開く
```
