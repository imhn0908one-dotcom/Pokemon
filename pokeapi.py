import json
import numbers
import os
import re
import time
from tabnanny import check

import requests
from numpy import add

mainurl = "https://pokeapi.co/api/v2/"


def get_entried_pokemon():
    url = mainurl + "pokedex/36"  # champions dex
    response = requests.get(url)
    entry_numbers = []
    for pokemon in response.json()["pokemon_entries"]:
        entry_numbers.append(int(pokemon["entry_number"]))
    return entry_numbers


def get_pokemondetail(id):
    url = mainurl + "pokemon/" + str(id)
    response = requests.get(url)
    abilities = []
    name = response.json()["name"]
    moveids = []
    stats = dict()    
    for ability in response.json()["abilities"]:
        dc = {}
        dc["ability_id"] = int(ability["ability"]["url"].split("/")[-2])
        dc["ability_name"] = ability["ability"]["name"]
        dc["is_hidden"] = ability["is_hidden"]
        abilities.append(dc)
    for move in response.json()["moves"]:
        moveids.append(int(move["move"]["url"].split("/")[-2]))
    for stat in response.json()["stats"]:
        stats[stat["stat"]["name"]] = stat["base_stat"]
    return name, abilities, moveids, stats
    

def save_pokemon():
    entry_numbers = get_entried_pokemon()
    total_count = len(entry_numbers)
    filename = "pokemon.json"

    # 1. すでに保存されているデータを読み込む（ファイルがない場合は空の辞書）
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                all_pokemon = json.load(f)
            except json.JSONDecodeError:
                # 万が一ファイルが空っぽなどで壊れていた場合の保険
                all_pokemon = {}
    else:
        all_pokemon = {}

    # 2. ループを回してデータを取得していく
    for index, id in enumerate(entry_numbers, 1):
        
        # すでに保存済みのIDならスキップ（途中から再開できる！）
        if str(id) in all_pokemon:
            print(f"[{index}/{total_count}] ID: {id} は保存済みのためスキップします。")
            continue

        print(f"[{index}/{total_count}] ID: {id} のデータを取得中...")
        try:
            name, abilities, moveids, stats = get_pokemondetail(id)
        except Exception as e:
            print(f"  → ⚠️ ID: {id} の取得中にエラーが発生しました: {e}")
            continue

        # 3. データを追加する
        all_pokemon[id] = {
            "name": name,
            "abilities": abilities,
            "moves": moveids,
            "stats": stats
        }

        json_string = json.dumps(all_pokemon, ensure_ascii=False)

        nice_json_string = json_string.replace('},"', '},\n"')
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(nice_json_string)

        # 5. APIサーバーに負荷をかけないよう、少し待つ
        time.sleep(1)

    print("\nすべてのポケモンのデータ取得・保存が完了しました！")


def checkkey():
    url = mainurl + "pokemon-species/3"
    response = requests.get(url)
    print(response.json().keys())


def get_gender_jpname(id):
    url = mainurl + "pokemon-species/" + str(id)
    response = requests.get(url)
    gender = response.json()["gender_rate"]
    jpname = response.json()["names"][0]["name"]
    return gender, jpname


def add_info_to_json():
    filename = "pokemon.json"
    with open(filename, "r", encoding="utf-8") as f:
        all_pokemon = json.load(f)
    for id in all_pokemon:
        gender, jpname = get_gender_jpname(id)
        all_pokemon[id]["gender"] = gender
        all_pokemon[id]["jpname"] = jpname
        print(all_pokemon[id]["jpname"])
    json_string = json.dumps(all_pokemon, ensure_ascii=False)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(json_string)


add_info_to_json()