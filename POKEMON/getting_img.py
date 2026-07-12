import manager
import requests

import os


poke = manager.get_selectable_pokemon_map()
url = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/"
saveing_path = "IMAGES/pokemon_selection/"

# 💡 ここを追加：保存先のフォルダがなければ自動で作成する
os.makedirs(saveing_path, exist_ok=True)

for key, value in poke.items():
    # 画像のURLを組み立て
    img_url = f"{url}{key}.png"

    img = requests.get(img_url)

    # 💡 ステータスコードが200（成功）の場合のみ保存する（404エラー対策）
    if img.status_code == 200:
        file_path = os.path.join(saveing_path, f"{value}.png")
        with open(file_path, "wb") as f:
            f.write(img.content)
        print(f"保存成功: {value}.png")
    else:
        print(f"スキップ（画像が見つかりません）: ID {key} - {value}")
