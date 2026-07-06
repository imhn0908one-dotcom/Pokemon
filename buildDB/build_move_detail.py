import sqlite3
import requests
import logging

# ⚙️ ログの設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("move_meta_fetch.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

GRAPHQL_URL = "https://graphql.pokeapi.co/v1beta2"
DB_NAME = "pokemon_champions.db"


def fetch_and_build_move_details():
    logging.info("=== 🌐 データベース(pokemon_move)から必要な技IDを抽出 ===")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. 必要な技IDの抽出
    try:
        cursor.execute("SELECT DISTINCT move_id FROM pokemon_move")
        rows = cursor.fetchall()
        target_move_ids = [row[0] for row in rows]
        logging.info(f"✨ {len(target_move_ids)}件のユニークな技IDを抽出しました。")
    except sqlite3.OperationalError as e:
        logging.critical(f"🚨 pokemon_moveテーブルが見つからないかエラーです: {e}")
        conn.close()
        return

    if not target_move_ids:
        logging.warning("⚠️ 取得する技IDがありませんでした。")
        conn.close()
        return

    # 2. GraphQLクエリ (stat_chance を追加)
    graphql_query = """
    query GetMoveDetails($moveIds: [Int!]) {
      move(where: {id: {_in: $moveIds}}) {
        id
        movemeta {
          move_meta_ailment_id
          ailment_chance
          flinch_chance
          stat_chance
          crit_rate
          min_hits
          max_hits
          min_turns
          max_turns
          drain
          healing
          move_meta_category_id
        }
      }
      
      movemetastatchange(where: {move_id: {_in: $moveIds}}) {
        move_id
        stat_id
        change
      }
    }
    """

    logging.info("=== 🌐 PokeAPI GraphQL から詳細データの取得開始 ===")

    try:
        response = requests.post(
            GRAPHQL_URL,
            json={"query": graphql_query, "variables": {"moveIds": target_move_ids}},
        )
        response.raise_for_status()
        json_data = response.json()

        if "errors" in json_data:
            logging.critical(f"🚨 GraphQLクエリエラー: {json_data['errors']}")
            return

        logging.info(
            "✨ データのダウンロードに成功しました！DBの初期化と解析を開始します。"
        )
    except Exception as e:
        logging.critical(f"🚨 API通信中にエラーが発生しました: {e}")
        return

    # ==========================================
    # 🧹 3. 既存のテーブルをすべて削除（完全リセット）
    # ==========================================
    logging.info(
        "🧹 既存の move_meta, move_stat_change テーブルを削除して初期化します..."
    )
    cursor.execute("DROP TABLE IF EXISTS move_meta")
    cursor.execute("DROP TABLE IF EXISTS move_stat_change")

    # ==========================================
    # 🏗️ 4. 新しいテーブルの作成 (stat_chance を追加)
    # ==========================================
    cursor.execute("""
        CREATE TABLE move_meta (
            move_id INTEGER PRIMARY KEY,
            ailment_id INTEGER,
            ailment_chance INTEGER,
            flinch_chance INTEGER,
            stat_chance INTEGER,
            crit_rate INTEGER,
            min_hits INTEGER,
            max_hits INTEGER,
            min_turns INTEGER,
            max_turns INTEGER,
            drain INTEGER,
            healing INTEGER,
            category_id INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE move_stat_change (
            move_id INTEGER,
            stat_id INTEGER,
            change_stage INTEGER,
            PRIMARY KEY (move_id, stat_id)
        )
    """)
    conn.commit()

    # 5. データの解析と流し込み
    try:
        target_ids_set = set(target_move_ids)

        # --- ① move_meta への保存処理 ---
        move_list = json_data.get("data", {}).get("move", [])
        meta_count = 0

        for m_data in move_list:
            m_id = m_data.get("id")

            if not m_id or m_id not in target_ids_set:
                continue

            meta_data_list = m_data.get("movemeta") or []

            if len(meta_data_list) > 0:
                meta_data = meta_data_list[0]

                # ▼ 無意味な0埋めデータを判定
                is_empty_meta = (
                    meta_data.get("ailment_chance") == 0
                    and meta_data.get("flinch_chance") == 0
                    and meta_data.get("stat_chance") == 0
                    and meta_data.get("crit_rate") == 0
                    and meta_data.get("drain") == 0
                    and meta_data.get("healing") == 0
                    and meta_data.get("min_hits") is None
                    and meta_data.get("min_turns") is None
                    and (meta_data.get("move_meta_ailment_id") or 0) == 0
                )

                if is_empty_meta:
                    continue

                cursor.execute(
                    """
                    INSERT INTO move_meta 
                    (move_id, ailment_id, ailment_chance, flinch_chance, stat_chance, crit_rate, 
                     min_hits, max_hits, min_turns, max_turns, drain, healing, category_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        m_id,
                        meta_data.get("move_meta_ailment_id"),
                        meta_data.get("ailment_chance"),
                        meta_data.get("flinch_chance"),
                        meta_data.get("stat_chance"),
                        meta_data.get("crit_rate"),
                        meta_data.get("min_hits"),
                        meta_data.get("max_hits"),
                        meta_data.get("min_turns"),
                        meta_data.get("max_turns"),
                        meta_data.get("drain"),
                        meta_data.get("healing"),
                        meta_data.get("move_meta_category_id"),
                    ),
                )
                meta_count += 1

        # --- ② move_stat_change への保存処理 ---
        stat_changes = json_data.get("data", {}).get("movemetastatchange", [])
        stat_change_count = 0

        for stat in stat_changes:
            m_id = stat.get("move_id")

            if not m_id or m_id not in target_ids_set:
                continue

            cursor.execute(
                """
                INSERT INTO move_stat_change (move_id, stat_id, change_stage)
                VALUES (?, ?, ?)
            """,
                (m_id, stat.get("stat_id"), stat.get("change")),
            )
            stat_change_count += 1

        conn.commit()
        logging.info("=== 🏁 初期化とデータ構築が完了しました！ ===")
        logging.info(f"対象DB: {DB_NAME}")
        logging.info(f"・move_meta 登録数: {meta_count}件 (意味のあるデータのみ)")
        logging.info(f"・move_stat_change 登録数: {stat_change_count}件")

    except Exception as e:
        logging.critical(f"🚨 データ解析・DB書き込み中にエラーが発生しました: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    fetch_and_build_move_details()
