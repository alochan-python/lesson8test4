# レシピ投稿ミニアプリ

Render の PostgreSQL と Flask + SQLAlchemy を使った最小構成のレシピ投稿アプリです。  
トップページ 1 画面で、一覧表示と新規追加ができます。

## ファイル構成

- `app.py` : Webアプリ本体
- `db_init.py` : DB テーブル初期化
- `requirements.txt`
- `README.md`

---

## できること

- レシピ一覧表示（新しい順）
- 新規追加
  - タイトル（必須）
  - 所要分数（必須・整数・1以上）
  - 説明（任意）

削除や編集は本課題の範囲外です。

---

## ローカル実行手順

### 1. 仮想環境を作成して有効化

macOS / Linux:

```bash
python -m venv env && source env/bin/activate