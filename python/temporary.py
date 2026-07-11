# testing code
from battle.instance_making import Pokemon_Instance

pokemon = Pokemon_Instance.from_toml("party/test1.toml", 0)
pokemon.show_status()
