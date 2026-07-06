import sqlite3
import requests
import logging

# ⚙️ ログの設定 (画面とファイルの両方に同時に出力)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("pokemon_and_ability_fetch.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

# 🌐 設定値
GRAPHQL_URL = "https://graphql.pokeapi.co/v1beta2"
DB_NAME = "pokemon_champions.db"

# 📜 ポケモンの基本ステータスと、制限なし(複数)の特性IDを同時に取得するGraphQLクエリ
GRAPHQL_QUERY = """
query samplePokeAPIquery {
  pokemon(where: {pokemonmoves: {version_group_id: {_eq: 32}}}) {
    id
    name
    pokemonabilities {
      ability_id
      is_hidden
    }
    pokemontypes {
      type_id
    }
    pokemonstats {
      base_stat
    }
  }
}
"""


def fetch_and_build_tables():
    logging.info(
        "=== 🌐 PokeAPI GraphQL からポケモン＆複数特性データの同時取得を開始 ==="
    )

    # 1. API通信
    try:
        response = requests.post(GRAPHQL_URL, json={"query": GRAPHQL_QUERY})
        response.raise_for_status()
        json_data = response.json()
        logging.info("✨ データのダウンロードに成功しました！解析を開始します。")
    except Exception as e:
        logging.critical(f"🚨 API通信中にエラーが発生しました: {e}")
        return

    # 2. DB準備
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("Drop table if exists pokemon")
    # ① ポケモン基本情報テーブル (ability_idは含めず、ステータスとタイプIDのみ)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pokemon (
            id INTEGER PRIMARY KEY,
            name TEXT,
            type_id1 INTEGER,
            type_id2 INTEGER,
            hp INTEGER,
            attack INTEGER,
            defense INTEGER,
            special_attack INTEGER,
            special_defense INTEGER,
            speed INTEGER
        )
    """)

    # ② 特性紐づけ専用テーブル (技と同じく、IDの数字ペアと夢特性フラグのみを保存)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pokemon_ability (
            pokemon_id INTEGER,
            ability_id INTEGER,
            is_hidden INTEGER,
            PRIMARY KEY (pokemon_id, ability_id)
        )
    """)
    conn.commit()

    # 3. 解析と流し込み
    try:
        pokemon_list = json_data.get("data", {}).get("pokemon", [])
        logging.info(
            f"対象ポケモン: {len(pokemon_list)} 匹を2つのテーブルに振り分けて書き込みます..."
        )

        total_pokemon = 0
        total_abilities = 0

        for p_data in pokemon_list:
            p_id = p_data.get("id")
            p_name = p_data.get("name")

            if not p_id:
                continue

            # --- 1. タイプ(ID)の解析 ---
            types_list = p_data.get("pokemontypes", [])
            type_id1 = types_list[0].get("type_id") if len(types_list) > 0 else None
            type_id2 = types_list[1].get("type_id") if len(types_list) > 1 else None

            # --- 2. ステータスの解析 ---
            stats_list = p_data.get("pokemonstats", [])
            hp = stats_list[0].get("base_stat", 0) if len(stats_list) > 0 else 0
            attack = stats_list[1].get("base_stat", 0) if len(stats_list) > 1 else 0
            defense = stats_list[2].get("base_stat", 0) if len(stats_list) > 2 else 0
            sp_attack = stats_list[3].get("base_stat", 0) if len(stats_list) > 3 else 0
            sp_defense = stats_list[4].get("base_stat", 0) if len(stats_list) > 4 else 0
            speed = stats_list[5].get("base_stat", 0) if len(stats_list) > 5 else 0

            # ➔ pokemon テーブルへ保存
            cursor.execute(
                """
                INSERT OR REPLACE INTO pokemon 
                (id, name, type_id1, type_id2, hp, attack, defense, special_attack, special_defense, speed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    p_id,
                    p_name,
                    type_id1,
                    type_id2,
                    hp,
                    attack,
                    defense,
                    sp_attack,
                    sp_defense,
                    speed,
                ),
            )
            total_pokemon += 1

            # --- 3. 複数特性の解析と保存 ---
            for a_data in p_data.get("pokemonabilities", []):
                ability_id = a_data.get("ability_id")
                is_hidden = 1 if a_data.get("is_hidden") else 0

                if ability_id:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO pokemon_ability (pokemon_id, ability_id, is_hidden)
                        VALUES (?, ?, ?)
                    """,
                        (p_id, ability_id, is_hidden),
                    )
                    total_abilities += 1

            # 50匹ごとに進捗をログに出力
            if total_pokemon % 50 == 0 or total_pokemon == len(pokemon_list):
                logging.info(
                    f"  ➔ 進捗: {total_pokemon} / {len(pokemon_list)} 匹を処理完了 (現在の特性総数: {total_abilities}つ)"
                )

        conn.commit()
        logging.info(
            "=== 🏁 pokemon および pokemon_ability テーブルの構築が完了しました！ ==="
        )
        logging.info(f"対象DB: {DB_NAME}")
        logging.info(f"・pokemon テーブル登録数          : {total_pokemon} 枠")
        logging.info(f"・pokemon_ability (特性ペア) 登録数 : {total_abilities} 件")

    except Exception as e:
        logging.critical(f"🚨 データ解析・DB書き込み中にエラーが発生しました: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    fetch_and_build_tables()
