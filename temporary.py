from battle.damage_calculator import Damagecalculator
from POKEMON import factory

AA = factory.create_pokemon_by_id(3)
BB = factory.create_pokemon_by_name("eevee")

CC = Damagecalculator()

print(CC.damage_calculator(AA,AA,1))