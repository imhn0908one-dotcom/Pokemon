import sqlite3
import requests
import logging

# ⚙️ ログの設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

GRAPHQL_URL = "https://graphql.pokeapi.co/v1beta2"
DB_NAME = "pokemon_champions.db"


def rebuild_ability_basicdata():
    logging.info("=== 🌐 データベース(pokemon_ability)から必要な特性IDを抽出 ===")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ==========================================
    # 1. 必要な特性IDの抽出
    # ==========================================
    try:
        # すでに作成済みの pokemon_ability から重複なしで特性IDを取り出します
        cursor.execute("SELECT DISTINCT ability_id FROM pokemon_ability")
        target_ability_ids = [row[0] for row in cursor.fetchall()]
        logging.info(
            f"✨ {len(target_ability_ids)}件のユニークな特性IDを抽出しました。"
        )
    except sqlite3.OperationalError as e:
        logging.critical(f"🚨 pokemon_abilityテーブルが見つからないかエラーです: {e}")
        conn.close()
        return

    if not target_ability_ids:
        logging.warning("⚠️ 取得する特性IDがありませんでした。")
        conn.close()
        return

    # ==========================================
    # 2. GraphQLクエリ (必要な特性IDのみを要求)
    # ==========================================
    graphql_query = """
    query GetAbilityDetails($abilityIds: [Int!]) {
      ability(where: {id: {_in: $abilityIds}}) {
        id
        name
      }
    }
    """

    logging.info("=== 🌐 PokeAPI GraphQL から特性データの取得開始 ===")

    try:
        response = requests.post(
            GRAPHQL_URL,
            json={
                "query": graphql_query,
                "variables": {"abilityIds": target_ability_ids},
            },
        )
        response.raise_for_status()
        json_data = response.json()

        if "errors" in json_data:
            logging.critical(f"🚨 GraphQLクエリエラー: {json_data['errors']}")
            conn.close()
            return

        logging.info("✨ データのダウンロードに成功しました！DBの再構築を開始します。")
    except Exception as e:
        logging.critical(f"🚨 API通信中にエラーが発生しました: {e}")
        conn.close()
        return

    # ==========================================
    # 🧹 3. 古いテーブルの削除と、新しいテーブルの作成
    # ==========================================
    logging.info("🧹 既存の ability_basicdata テーブルを削除して初期化します...")
    cursor.execute("DROP TABLE IF EXISTS ability_basicdata")

    # 特性のIDと英語名を保存するシンプルなテーブル
    cursor.execute("""
        CREATE TABLE ability_basicdata (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    """)
    conn.commit()

    # ==========================================
    # 4. データの厳密なチェックと流し込み
    # ==========================================
    try:
        target_ids_set = set(target_ability_ids)
        ability_list = json_data.get("data", {}).get("ability", [])

        insert_count = 0

        for a_data in ability_list:
            a_id = a_data.get("id")

            # 抽出したIDリストに無い特性は強制的にスルー！
            if not a_id or a_id not in target_ids_set:
                continue

            cursor.execute(
                """
                INSERT INTO ability_basicdata (id, name)
                VALUES (?, ?)
            """,
                (a_id, a_data.get("name")),
            )
            insert_count += 1

        conn.commit()
        logging.info("=== 🏁 ability_basicdata テーブルの構築が完了しました！ ===")
        logging.info(f"対象DB: {DB_NAME}")
        logging.info(f"・ability_basicdata 登録数: {insert_count}件 (ダイエット成功)")

    except Exception as e:
        logging.critical(f"🚨 データ解析・DB書き込み中にエラーが発生しました: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    rebuild_ability_basicdata()
