from flask import Flask, jsonify, render_template

from POKEMON import get_pokemon_list

app = Flask(__name__)
app.config["WTF_CSRF_ENABLED"] = False  # 開発中だけセキュリティをオフにする


# 画面を表示するためのルート
@app.route("/")
def index():
    return render_template("index.html")


# 💡 JavaScriptから呼ばれる「データ提供専用」のルート
@app.route("/api/get-options")
def get_options():
    # 本来はここでデータベースから取得したりしますが、まずはシンプルな配列で
    # ※前にお話しした「id」と「name（表示名）」のセットにしておくと超扱いやすいです！
    pokedata = get_pokemon_list()

    # 配列をそのままJavaScriptが読める形（JSONフォーマット）に変換して返します
    return jsonify(pokedata)


if __name__ == "__main__":
    app.run(debug=True, port=8000)
