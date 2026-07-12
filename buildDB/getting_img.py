from POKEMON import manager
import requests

poke = manager.get_selectable_pokemon_map()
url = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/"
saveing_path = "IMAGES/pokemon_sprites/"
for key, value in poke.items():
    img = requests.get(url + str(key) + ".png")
    with open(saveing_path + value + ".png", "wb") as f:
        f.write(img.content)
