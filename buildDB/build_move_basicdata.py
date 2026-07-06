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


def rebuild_move_basicdata():
    logging.info("=== 🌐 データベース(pokemon_move)から必要な技IDを抽出 ===")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ==========================================
    # 1. 必要な技IDの抽出
    # ==========================================
    try:
        cursor.execute("SELECT DISTINCT move_id FROM pokemon_move")
        target_move_ids = [row[0] for row in cursor.fetchall()]
        logging.info(f"✨ {len(target_move_ids)}件のユニークな技IDを抽出しました。")
    except sqlite3.OperationalError as e:
        logging.critical(f"🚨 pokemon_moveテーブルが見つからないかエラーです: {e}")
        conn.close()
        return

    if not target_move_ids:
        logging.warning("⚠️ 取得する技IDがありませんでした。")
        conn.close()
        return

    # ==========================================
    # 2. GraphQLクエリ (必要な技IDのみを要求)
    # ==========================================
    graphql_query = """
    query GetMoveBasicData($moveIds: [Int!]) {
      move(where: {id: {_in: $moveIds}}) {
        id
        name
        type_id
        power
        accuracy
        pp
        priority
        move_damage_class_id
        move_target_id
      }
    }
    """

    logging.info("=== 🌐 PokeAPI GraphQL から基本データの取得開始 ===")

    try:
        response = requests.post(
            GRAPHQL_URL,
            json={"query": graphql_query, "variables": {"moveIds": target_move_ids}},
        )
        response.raise_for_status()
        json_data = response.json()
        logging.info("✨ データのダウンロードに成功しました！DBの再構築を開始します。")
    except Exception as e:
        logging.critical(f"🚨 API通信中にエラーが発生しました: {e}")
        conn.close()
        return

    # ==========================================
    # 🧹 3. 古いテーブルの削除と、新しいテーブルの作成
    # ==========================================
    logging.info("🧹 既存の move_basicdata テーブルを削除して初期化します...")
    cursor.execute("DROP TABLE IF EXISTS move_basicdata")

    cursor.execute("""
        CREATE TABLE move_basicdata (
            id INTEGER PRIMARY KEY,
            name TEXT,
            type_id INTEGER,
            power INTEGER,
            accuracy INTEGER,
            pp INTEGER,
            priority INTEGER,
            damage_class_id INTEGER,
            target_id INTEGER
        )
    """)
    conn.commit()

    # ==========================================
    # 4. データの厳密なチェックと流し込み
    # ==========================================
    try:
        target_ids_set = set(target_move_ids)
        move_list = json_data.get("data", {}).get("move", [])

        insert_count = 0

        for m_data in move_list:
            m_id = m_data.get("id")

            # ▼ ここが最重要：抽出したIDリストに無い技は強制的にスルー！
            if not m_id or m_id not in target_ids_set:
                continue

            cursor.execute(
                """
                INSERT INTO move_basicdata 
                (id, name, type_id, power, accuracy, pp, priority, damage_class_id, target_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    m_id,
                    m_data.get("name"),
                    m_data.get("type_id"),
                    m_data.get("power"),
                    m_data.get("accuracy"),
                    m_data.get("pp"),
                    m_data.get("priority"),
                    m_data.get("move_damage_class_id"),
                    m_data.get("move_target_id"),
                ),
            )
            insert_count += 1

        conn.commit()
        logging.info("=== 🏁 基本データの再構築が完了しました！ ===")
        logging.info(f"対象DB: {DB_NAME}")
        logging.info(
            f"・move_basicdata 登録数: {insert_count}件 (必要最小限にダイエット成功)"
        )

    except Exception as e:
        logging.critical(f"🚨 データ解析・DB書き込み中にエラーが発生しました: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    rebuild_move_basicdata()
