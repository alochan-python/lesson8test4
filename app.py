import os
from flask import Flask, Response, redirect, render_template, request, url_for
from sqlalchemy import create_engine, text

app = Flask(__name__)

# ============================================
# Render 本番:
#   Environment Variables の DATABASE_URL を使う
#
# ローカル確認:
#   必要ならここに External Database URL を貼る
# ============================================
MANUAL_DATABASE_URL = ""

raw_database_url = (MANUAL_DATABASE_URL or os.environ.get("DATABASE_URL", "")).strip()

if raw_database_url.startswith("postgres://"):
    raw_database_url = raw_database_url.replace(
        "postgres://", "postgresql+psycopg2://", 1
    )

DATABASE_URL = raw_database_url

engine = None
startup_error_message = ""

try:
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL が設定されていません。app.py の MANUAL_DATABASE_URL か、Render の環境変数を確認してください。"
        )

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
except Exception as e:
    startup_error_message = f"DB接続の初期化に失敗しました: {e}"


def get_form_data():
    return {
        "id": request.form.get("id", "").strip(),
        "title": request.form.get("title", "").strip(),
        "minutes": request.form.get("minutes", "").strip(),
        "description": request.form.get("description", "").strip(),
    }


def validate_recipe_form(form_data):
    title = form_data["title"]
    minutes_text = form_data["minutes"]

    if not title:
        return "タイトルは必須です。"

    if len(title) > 200:
        return "タイトルは200文字以内で入力してください。"

    if not minutes_text:
        return "所要分数は必須です。"

    try:
        minutes = int(minutes_text)
    except ValueError:
        return "所要分数は整数で入力してください。"

    if minutes < 1:
        return "所要分数は1以上で入力してください。"

    return ""


@app.route("/", methods=["GET", "POST"])
def index():
    error_message = ""
    success_message = ""
    form_data = {"id": "", "title": "", "minutes": "", "description": ""}
    recipes = []
    edit_id = request.args.get("edit", "").strip()

    if engine is None:
        return Response(
            render_template(
                "index.html",
                recipes=[],
                error_message="",
                success_message="",
                form_data=form_data,
                startup_error_message=startup_error_message,
                is_edit=False,
            ),
            content_type="text/html; charset=utf-8",
        )

    if request.method == "POST":
        action = request.form.get("action", "create").strip()
        form_data = get_form_data()

        if action == "delete":
            recipe_id = request.form.get("id", "").strip()
            try:
                delete_sql = text("DELETE FROM recipes WHERE id = :id")
                with engine.begin() as conn:
                    conn.execute(delete_sql, {"id": int(recipe_id)})
                return redirect(url_for("index", deleted="1"))
            except Exception as e:
                error_message = f"削除中にエラーが発生しました: {e}"

        else:
            error_message = validate_recipe_form(form_data)

            if not error_message:
                try:
                    with engine.begin() as conn:
                        if action == "update" and form_data["id"]:
                            update_sql = text("""
                                UPDATE recipes
                                SET title = :title,
                                    minutes = :minutes,
                                    description = :description
                                WHERE id = :id
                            """)
                            conn.execute(
                                update_sql,
                                {
                                    "id": int(form_data["id"]),
                                    "title": form_data["title"],
                                    "minutes": int(form_data["minutes"]),
                                    "description": form_data["description"] or None,
                                },
                            )
                            return redirect(url_for("index", updated="1"))
                        else:
                            insert_sql = text("""
                                INSERT INTO recipes (title, minutes, description)
                                VALUES (:title, :minutes, :description)
                            """)
                            conn.execute(
                                insert_sql,
                                {
                                    "title": form_data["title"],
                                    "minutes": int(form_data["minutes"]),
                                    "description": form_data["description"] or None,
                                },
                            )
                            return redirect(url_for("index", created="1"))
                except Exception as e:
                    error_message = f"保存中にエラーが発生しました: {e}"

    if request.args.get("created") == "1":
        success_message = "レシピを登録しました。"
    elif request.args.get("updated") == "1":
        success_message = "レシピを更新しました。"
    elif request.args.get("deleted") == "1":
        success_message = "レシピを削除しました。"

    try:
        select_sql = text("""
            SELECT id, title, minutes, description,
                   to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS') AS created_at
            FROM recipes
            ORDER BY created_at DESC, id DESC
        """)
        with engine.begin() as conn:
            rows = conn.execute(select_sql).mappings().all()
            recipes = [dict(row) for row in rows]
    except Exception as e:
        error_message = f"一覧の取得中にエラーが発生しました: {e}"

    if edit_id:
        for recipe in recipes:
            if str(recipe["id"]) == edit_id:
                form_data = {
                    "id": str(recipe["id"]),
                    "title": recipe["title"],
                    "minutes": str(recipe["minutes"]),
                    "description": recipe["description"] or "",
                }
                break

    is_edit = bool(form_data["id"])

    return Response(
        render_template(
            "index.html",
            recipes=recipes,
            error_message=error_message,
            success_message=success_message,
            form_data=form_data,
            startup_error_message=startup_error_message,
            is_edit=is_edit,
        ),
        content_type="text/html; charset=utf-8",
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    print(f"Starting app on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)