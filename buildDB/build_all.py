import argparse
import logging
import sqlite3
import time
import requests

# 共通設定
GRAPHQL_URL = "https://graphql.pokeapi.co/v1beta2"
DB_NAME = "pokemon_champions.db"

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("log/build_all.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


def post_graphql_request(query, variables=None, max_retries=3, timeout=10):
    payload = {"query": query}
    if variables is not None:
        payload["variables"] = variables

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(GRAPHQL_URL, json=payload, timeout=timeout)
            response.raise_for_status()
            try:
                return response.json()
            except ValueError as err:
                raise RuntimeError(
                    f"GraphQL response was not valid JSON: {err}, text={response.text!r}"
                ) from err
        except requests.exceptions.RequestException as err:
            if attempt == max_retries:
                raise
            logging.warning(
                f"GraphQL request failed (attempt {attempt}/{max_retries}): {err}. Retrying..."
            )
            time.sleep(2 ** (attempt - 1))

    raise RuntimeError("GraphQL request retries exhausted")


# --- build_types.py の機能 ---


def fetch_and_build_types():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    logging.info("=== 1. GraphQLでタイプと相性データを一括取得中 ===")

    type_query = """
    query samplePokeAPIquery {
        type {
            id
            name
            typeefficacies {
            damage_type_id
            damage_factor
            }
        }
        }
    """

    try:
        response_json = post_graphql_request(type_query)
    except Exception as err:
        logging.critical(f"🚨 GraphQL通信エラー: {err}")
        conn.close()
        return

    if "errors" in response_json:
        logging.critical(
            f"🚨 PokeAPIのサーバーからエラーが返されました: {response_json['errors']}"
        )
        return

    if "data" not in response_json or "type" not in response_json["data"]:
        logging.critical(f"🚨 想定外のデータ構造が返ってきました: {response_json}")
        return

    type_data = response_json["data"]["type"]
    logging.info(f"-> {len(type_data)} 個のタイプデータをパース中...")

    cursor.execute("DROP TABLE IF EXISTS types")
    cursor.execute("DROP TABLE IF EXISTS type_matchups")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS types (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS type_matchups (
            attack_type_id INTEGER,
            defense_type_id INTEGER,
            multiplier REAL,
            PRIMARY KEY (attack_type_id, defense_type_id)
        )
        """
    )
    conn.commit()

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

    for t in type_data:
        atk_id = t["id"]
        for efficacy in t.get("typeefficacies", []):
            def_id = efficacy["damage_type_id"]
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
    logging.info("=== 【ステップ1完了】タイプのDB構築が正常に終わりました！ ===")


# --- build_ability_basicdata.py の機能 ---


def rebuild_ability_basicdata():
    logging.info("=== 🌐 データベース(pokemon_ability)から必要な特性IDを抽出 ===")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
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
        json_data = post_graphql_request(
            graphql_query,
            variables={"abilityIds": target_ability_ids},
        )
    except Exception as err:
        logging.critical(f"🚨 GraphQL通信エラー: {err}")
        conn.close()
        return

    if "errors" in json_data:
        logging.critical(f"🚨 GraphQLクエリエラー: {json_data['errors']}")
        conn.close()
        return

    logging.info("✨ データのダウンロードに成功しました！DBの再構築を開始します。")

    logging.info("🧹 既存の ability_basicdata テーブルを削除して初期化します...")
    cursor.execute("DROP TABLE IF EXISTS ability_basicdata")

    cursor.execute("""
        CREATE TABLE ability_basicdata (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    """)
    conn.commit()

    try:
        target_ids_set = set(target_ability_ids)
        ability_list = json_data.get("data", {}).get("ability", [])

        insert_count = 0

        for a_data in ability_list:
            a_id = a_data.get("id")

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


# --- build_move_basicdata.py の機能 ---


def rebuild_move_basicdata():
    logging.info("=== 🌐 データベース(pokemon_move)から必要な技IDを抽出 ===")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

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
        json_data = post_graphql_request(
            graphql_query,
            variables={"moveIds": target_move_ids},
        )
    except Exception as err:
        logging.critical(f"🚨 GraphQL通信エラー: {err}")
        conn.close()
        return

    logging.info("✨ データのダウンロードに成功しました！DBの再構築を開始します。")

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

    try:
        target_ids_set = set(target_move_ids)
        move_list = json_data.get("data", {}).get("move", [])

        insert_count = 0

        for m_data in move_list:
            m_id = m_data.get("id")

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


# --- build_move_detail.py の機能 ---


def fetch_and_build_move_details():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler("move_meta_fetch.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    logging.info("=== 🌐 データベース(pokemon_move)から必要な技IDを抽出 ===")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

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
        json_data = post_graphql_request(
            graphql_query,
            variables={"moveIds": target_move_ids},
        )
    except Exception as err:
        logging.critical(f"🚨 GraphQL通信エラー: {err}")
        return

    if "errors" in json_data:
        logging.critical(f"🚨 GraphQLクエリエラー: {json_data['errors']}")
        return

    logging.info(
        "✨ データのダウンロードに成功しました！DBの初期化と解析を開始します。"
    )

    logging.info(
        "🧹 既存の move_meta, move_stat_change テーブルを削除して初期化します..."
    )
    cursor.execute("DROP TABLE IF EXISTS move_meta")
    cursor.execute("DROP TABLE IF EXISTS move_stat_change")

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

    try:
        target_ids_set = set(target_move_ids)

        move_list = json_data.get("data", {}).get("move", [])
        meta_count = 0

        for m_data in move_list:
            m_id = m_data.get("id")

            if not m_id or m_id not in target_ids_set:
                continue

            meta_data_list = m_data.get("movemeta") or []

            if len(meta_data_list) > 0:
                meta_data = meta_data_list[0]

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


# --- build_pokemon_st.py の機能 ---


def fetch_and_build_tables():
    logging.info(
        "=== 🌐 PokeAPI GraphQL からポケモン＆複数特性データの同時取得を開始 ==="
    )

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

    try:
        json_data = post_graphql_request(GRAPHQL_QUERY)
    except Exception as err:
        logging.critical(f"🚨 GraphQL通信エラー: {err}")
        return

    logging.info("✨ データのダウンロードに成功しました！解析を開始します。")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("Drop table if exists pokemon")
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pokemon_ability (
            pokemon_id INTEGER,
            ability_id INTEGER,
            is_hidden INTEGER,
            PRIMARY KEY (pokemon_id, ability_id)
        )
    """)
    conn.commit()

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

            types_list = p_data.get("pokemontypes", [])
            type_id1 = types_list[0].get("type_id") if len(types_list) > 0 else None
            type_id2 = types_list[1].get("type_id") if len(types_list) > 1 else None

            stats_list = p_data.get("pokemonstats", [])
            HP = stats_list[0].get("base_stat", 0) if len(stats_list) > 0 else 0
            Atk = stats_list[1].get("base_stat", 0) if len(stats_list) > 1 else 0
            Def = stats_list[2].get("base_stat", 0) if len(stats_list) > 2 else 0
            SpA = stats_list[3].get("base_stat", 0) if len(stats_list) > 3 else 0
            SpD = stats_list[4].get("base_stat", 0) if len(stats_list) > 4 else 0
            Spe = stats_list[5].get("base_stat", 0) if len(stats_list) > 5 else 0

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
                    HP,
                    Atk,
                    Def,
                    SpA,
                    SpD,
                    Spe,
                ),
            )
            total_pokemon += 1

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


# --- build_nature.py の機能 ---


def fetch_and_save_natures():
    logging.info("🌐 PokeAPIから性格補正データを取得中...")
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

    try:
        json_data = post_graphql_request(GRAPHQL_QUERY)
        data = json_data.get("data", {}).get("nature", [])
    except Exception as err:
        logging.critical(f"🚨 API通信エラー: {err}")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nature_data (
            id INTEGER PRIMARY KEY,
            name TEXT,
            increased_stat_id INTEGER,
            decreased_stat_id INTEGER
        )
    """)

    for n in data:
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
    logging.info(
        f"✨ 正常に {len(data)} 種類の性格補正データを `nature_data` に保存しました！"
    )


def fetch_and_build_gender_rate():
    logging.info(
        "=== 🌐 データベース(pokemon)から対象IDを取得し、gender_rateを構築します ==="
    )

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT DISTINCT id FROM pokemon")
        pokemon_ids = [row[0] for row in cursor.fetchall()]
        logging.info(
            f"✨ pokemonテーブルから {len(pokemon_ids)} 件のIDを取得しました。"
        )
    except sqlite3.OperationalError as e:
        logging.critical(f"🚨 pokemonテーブルが見つからないかエラーです: {e}")
        conn.close()
        return

    if not pokemon_ids:
        logging.warning(
            "⚠️ pokemonテーブルにIDが存在しません。gender_rateの構築をスキップします。"
        )
        conn.close()
        return

    graphql_query = """
    query GetPokemonSpeciesGenderRate($speciesIds: [Int!]) {
        pokemonspecies(where: {id: {_in: $speciesIds}}) {
            id
            gender_rate
        }
    }
    """

    try:
        json_data = post_graphql_request(
            graphql_query,
            variables={"speciesIds": pokemon_ids},
        )
    except Exception as err:
        logging.critical(f"🚨 GraphQL通信エラー: {err}")
        conn.close()
        return

    if "errors" in json_data:
        logging.critical(f"🚨 GraphQLクエリエラー: {json_data['errors']}")
        conn.close()
        return

    logging.info(
        "✨ pokemonspeciesデータのダウンロードに成功しました！gender_rateの構築を開始します。"
    )

    cursor.execute("DROP TABLE IF EXISTS gender_rate")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS gender_rate (
            pokemon_id INTEGER PRIMARY KEY,
            gender_rate INTEGER
        )
        """
    )
    conn.commit()

    try:
        species_list = json_data.get("data", {}).get("pokemonspecies", [])
        species_id_set = set(pokemon_ids)
        insert_count = 0

        for species in species_list:
            species_id = species.get("id")
            if species_id not in species_id_set:
                continue

            cursor.execute(
                "INSERT OR REPLACE INTO gender_rate (pokemon_id, gender_rate) VALUES (?, ?)",
                (species_id, species.get("gender_rate", 0)),
            )
            insert_count += 1

        conn.commit()
        logging.info("=== 🏁 gender_rate テーブル構築が完了しました！ ===")
        logging.info(f"・gender_rate 登録数: {insert_count} 件")
    except Exception as e:
        logging.critical(
            f"🚨 gender_rate データ解析・DB書き込み中にエラーが発生しました: {e}"
        )
    finally:
        conn.close()


def finalize_db():
    """Finalize DB changes: checkpoint WAL and vacuum to persist changes."""
    try:
        conn = sqlite3.connect(DB_NAME)
        # Try to checkpoint WAL and compact DB to ensure on-disk consistency
        try:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        except Exception:
            pass
        try:
            conn.execute("VACUUM;")
        except Exception:
            pass
        conn.commit()
        conn.close()
        logging.info("✅ データベースの最終確定（checkpoint + vacuum）を完了しました。")
    except Exception as e:
        logging.warning(f"⚠️ データベース確定処理で警告: {e}")


# CLI


def main():
    parser = argparse.ArgumentParser(description="Build DB utilities consolidated")
    parser.add_argument("--all", action="store_true", help="Run all build steps")
    parser.add_argument("--types", action="store_true", help="Build type tables")
    parser.add_argument(
        "--ability", action="store_true", help="Build ability basicdata"
    )
    parser.add_argument(
        "--move-basic", action="store_true", help="Build move basicdata"
    )
    parser.add_argument("--move-detail", action="store_true", help="Build move details")
    parser.add_argument("--pokemon", action="store_true", help="Build pokemon tables")
    parser.add_argument(
        "--gender-rate", action="store_true", help="Build gender_rate table"
    )
    parser.add_argument("--natures", action="store_true", help="Build nature data")
    args = parser.parse_args()

    if args.all:
        # Build order adjusted to satisfy dependencies:
        # 1) pokemon tables (provides `pokemon_ability` for ability basicdata)
        # 2) ability basicdata (reads `pokemon_ability`)
        # 3) types
        # 4) move basicdata
        # 5) move details
        # 6) gender_rate
        # 7) natures
        fetch_and_build_tables()
        rebuild_ability_basicdata()
        fetch_and_build_types()
        rebuild_move_basicdata()
        fetch_and_build_move_details()
        fetch_and_build_gender_rate()
        fetch_and_save_natures()
        finalize_db()
        return

    if args.types:
        fetch_and_build_types()
    if args.ability:
        rebuild_ability_basicdata()
    if args.move_basic:
        rebuild_move_basicdata()
    if args.move_detail:
        fetch_and_build_move_details()
    if args.pokemon:
        fetch_and_build_tables()
    if args.gender_rate:
        fetch_and_build_gender_rate()
    if args.natures:
        fetch_and_save_natures()
    if args.ability:
        rebuild_ability_basicdata()
    if args.move_basic:
        rebuild_move_basicdata()
    if args.move_detail:
        fetch_and_build_move_details()
    if args.pokemon:
        fetch_and_build_tables()
    if args.natures:
        fetch_and_save_natures()
    # If running individual steps, optionally finalize DB when requested via --all only


if __name__ == "__main__":
    main()
