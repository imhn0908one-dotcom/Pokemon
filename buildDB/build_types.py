import sqlite3
import requests

# 正しいURL
GRAPHQL_URL = "https://beta.pokeapi.co/graphql/v1beta2"
DB_NAME = "pokemon_champions.db"


def init_type_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS types (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS type_matchups (
            attack_type_id INTEGER,
            defense_type_id INTEGER,
            multiplier REAL,
            PRIMARY KEY (attack_type_id, defense_type_id)
        )
    """)
    conn.commit()
    return conn


def fetch_and_build_types():
    conn = init_type_db()
    cursor = conn.cursor()

    print("=== 1. GraphQLでタイプと相性データを一括取得中 ===")

    # 🌟 正しい呪文（フィールド名を正しく修正しました）
    type_query = """
    query getTypeMatchups {
      types: pokemon_v2_type(where: {id: {_lt: 10000}}) {
        id
        name
        pokemon_v2_typeefficacies {
          target_type_id
          damage_factor
        }
      }
    }
    """

    response = requests.post(GRAPHQL_URL, json={"query": type_query})
    response_json = response.json()

    if "errors" in response_json:
        print("❌ PokeAPIのサーバーからエラーが返されました:")
        print(response_json["errors"])
        return

    if "data" not in response_json or "types" not in response_json["data"]:
        print("❌ 想定外のデータ構造が返ってきました。返却データ:")
        print(response_json)
        return

    type_data = response_json["data"]["types"]
    print(f"-> {len(type_data)} 個のタイプデータをパース中...")

    # === 2. データの解読とSQLiteへの保存 ===
    # まず、すべての組み合わせをいったん「1.0倍（等倍）」で初期化する
    for t_atk in type_data:
        cursor.execute(
            "INSERT OR REPLACE INTO types (id, name) VALUES (?, ?)",
            (t_atk["id"], t_atk["name"]),
        )
        for t_def in type_data:
            cursor.execute(
                "INSERT OR REPLACE INTO type_matchups VALUES (?, ?, 1.0)",
                (t_atk["id"], t_def["id"]),
            )
    conn.commit()

    # 次に、APIから届いた倍率（2倍、0.5倍、0倍）を上書きしていく
    for t in type_data:
        atk_id = t["id"]
        # 🌟 ここも正しいフィールド名に修正
        for efficacy in t["pokemon_v2_typeefficacies"]:
            def_id = efficacy["target_type_id"]
            multiplier = efficacy["damage_factor"] / 100.0

            cursor.execute(
                """
                UPDATE type_matchups 
                SET multiplier = ? 
                WHERE attack_type_id = ? AND defense_type_id = ?
            """,
                (multiplier, atk_id, def_id),
            )

    conn.commit()
    conn.close()
    print("=== 【ステップ1完了】タイプのDB構築が正常に終わりました！ ===")


if __name__ == "__main__":
    fetch_and_build_types()
