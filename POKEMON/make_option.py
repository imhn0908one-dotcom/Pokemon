import json


def get_pokemon_list():
    with open("pokemon.json", "r", encoding="utf-8") as f:
        get_pokemon_list = json.load(f)
    result = []
    for key, value in get_pokemon_list.items():
        result.append({"id": key, "name": value["jpname"]})
    return result


print(get_pokemon_list())
