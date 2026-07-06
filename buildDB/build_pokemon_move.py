import sqlite3
import requests
import logging

# ⚙️ ログの設定 (ログファイルとターミナルに同時出力)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("graphql_fetch.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

# 🌐 設定項目
GRAPHQL_URL = "https://graphql.pokeapi.co/v1beta2"
DB_NAME = "pokemon_champions.db"

# 📜 送信するGraphQLクエリ
# championsの技を持っているポケモンと、その技IDをすべて一発で取得します
GRAPHQL_QUERY = """
query samplePokeAPIquery {
  pokemon(where: {pokemonmoves: {versiongroup: {name: {_eq: "champions"}}}}) {
    id
    pokemonmoves(where: {versiongroup: {name: {_eq: "champions"}}}) {
      move_id
    }
  }
}
"""


def fetch_and_build_db():
    logging.info("=== 🌐 PokeAPI GraphQL からのデータ取得を開始します ===")
    logging.info(f"URL: {GRAPHQL_URL}")

    # 1. APIにリクエストを送信
    try:
        response = requests.post(GRAPHQL_URL, json={"query": GRAPHQL_QUERY})
        response.raise_for_status()  # エラーがあればここで例外を発生させる
        json_data = response.json()
        logging.info("✨ PokeAPIからのデータダウンロードに成功しました！")
    except Exception as e:
        logging.critical(f"🚨 APIからのデータ取得中に通信エラーが発生しました: {e}")
        return

    # 2. データベースの準備
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 重複をガードするID紐づけテーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS selectionmove (
            pokemon_id INTEGER,
            move_id INTEGER,
            PRIMARY KEY (pokemon_id, move_id)
        )
    """)
    conn.commit()

    # 3. データの解析と流し込み
    try:
        pokemon_list = json_data.get("data", {}).get("pokemon", [])
        logging.info(
            f"取得データ内から {len(pokemon_list)} 種類のポケモンを検出しました。DBに書き込みます。"
        )

        total_inserted = 0

        for p_data in pokemon_list:
            pokemon_id = p_data.get("id")
            moves = p_data.get("pokemonmoves", [])

            if not pokemon_id:
                continue

            pokemon_inserted_count = 0
            for m_data in moves:
                move_id = m_data.get("move_id")

                if move_id:
                    try:
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO selectionmove (pokemon_id, move_id)
                            VALUES (?, ?)
                        """,
                            (pokemon_id, move_id),
                        )

                        if cursor.rowcount > 0:
                            pokemon_inserted_count += 1
                            total_inserted += 1
                    except Exception as e:
                        logging.error(
                            f"  ❌ ポケモンID: {pokemon_id}, 技ID: {move_id} の保存エラー: {e}"
                        )

            # 各ポケモンの進捗をサラッとログに残す
            if pokemon_inserted_count > 0:
                logging.info(
                    f"  ➔ ポケモンID: {pokemon_id} に {pokemon_inserted_count} 件の技を新規紐づけ"
                )

        # 4. 保存の確定
        conn.commit()
        logging.info("=== 🏁 全データの移行が完了しました！ ===")
        logging.info(f"データベースファイル: {DB_NAME}")
        logging.info(f"今回新規に登録されたIDペア: 累計 {total_inserted} 件")

    except Exception as e:
        logging.critical(f"🚨 JSONデータの解析・DB保存中にエラーが発生しました: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    fetch_and_build_db()
