import sqlite3
import requests

GRAPHQL_URL = "https://graphql.pokeapi.co/v1beta2"
DB_NAME = "pokemon_champions.db"

# 📜 あなたが提示してくれた完璧なクエリをそのままセット
GRAPHQL_QUERY = """
query samplePokeAPIquery {
  nature {
    id
    name
    increased_stat_id
    decreased_stat_id
  }
}
"""


def fetch_and_save_natures():
    print("🌐 PokeAPIから性格補正データを取得中...")
    try:
        response = requests.post(GRAPHQL_URL, json={"query": GRAPHQL_QUERY})
        response.raise_for_status()
        data = response.json().get("data", {}).get("nature", [])
    except Exception as e:
        print(f"🚨 API通信エラー: {e}")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 性格データテーブルの作成
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nature_data (
            id INTEGER PRIMARY KEY,
            name TEXT,
            increased_stat_id INTEGER,
            decreased_stat_id INTEGER
        )
    """)

    for n in data:
        # 手書きTOMLの表記（"Adamant"など）と完全に一致させるため、頭文字を大文字に変換
        name = n["name"].capitalize()
        cursor.execute(
            """
            INSERT OR REPLACE INTO nature_data (id, name, increased_stat_id, decreased_stat_id)
            VALUES (?, ?, ?, ?)
        """,
            (n["id"], name, n["increased_stat_id"], n["decreased_stat_id"]),
        )

    conn.commit()
    conn.close()
    print(
        f"✨ 正常に {len(data)} 種類の性格補正データを `nature_data` に保存しました！"
    )


if __name__ == "__main__":
    fetch_and_save_natures()
