try:
    from .party_manager_logic import PartyManagerLogic
except ImportError:
    from party_manager_logic import PartyManagerLogic


class PartyManagerCUI:
    """パーティ管理の操作を対話形式で行うCUIクラス。"""

    def __init__(self, builder=None, input_func=input, output_func=print):
        self.builder = builder or PartyManagerLogic()
        self.input = input_func
        self.print = output_func

    def start(self):
        """セッションを開始し、パーティの表示・編集・保存を繰り返す。"""
        self.print("==========================================")
        self.print("⚔️  PartyManager CUI セッション開始  ⚔️")
        self.print("==========================================")

        if not self.builder.party_data:
            party_name = self._ask_party_name()
            self.builder.create_empty_party(party_name)
            self.print(f"新しいパーティを作成しました: {self.builder.party_path}")
        else:
            self.print(f"既存パーティを読み込みました: {self.builder.party_path}")

        while True:
            self._display_party()
            action = self._choose_action()
            if action == "quit":
                break
            self._execute_action(action)

    def _ask_party_name(self):
        while True:
            party_name = self.input("パーティ名を入力してください: ").strip()
            if party_name:
                return party_name
            self.print("🚨 パーティ名を入力してください。")

    def _display_party(self):
        party = self.builder.get_current_party()
        self.print("\n=== 現在のパーティ ===")
        for idx, pokemon in enumerate(party["pokemon"]):  # type: ignore
            self.print(
                f"[{idx}] {pokemon['name']} (ID:{pokemon['pokemon_id']}), "
                f"Lv{pokemon['level']}, Nature:{pokemon['nature_name']} ({pokemon['nature_id']}), "
                f"Ability:{pokemon['ability_name']} ({pokemon['ability_id']}), Moves:{pokemon['moves']}, EVs:{pokemon['evs']}"
            )
        self.print("=======================")

    def _choose_action(self):
        """ユーザーに選択肢を示して、次の操作を決める。"""
        self.print("\n操作を選択してください:")
        self.print("  1) スロットを変更")
        self.print("  2) ポケモンを読み込み")
        self.print("  3) 保存")
        self.print("  q) 終了")
        choice = self.input("> ").strip().lower()
        if choice == "1":
            return "slot"
        if choice == "2":
            return "load"
        if choice == "3":
            return "save"
        if choice == "q":
            return "quit"
        self.print("🚨 無効な選択です。もう一度入力してください。")
        return self._choose_action()

    def _execute_action(self, action):
        if action == "slot":
            self._change_slot_flow()
        elif action == "load":
            self._load_party_flow()
        elif action == "save":
            self.builder.save_changes()
            self.print("パーティを保存しました。")

    def _load_party_flow(self):
        filepath = self.input("読み込むファイル名またはパス: ").strip()
        try:
            self.builder.load_party(filepath)
            self.print(
                f"パーティを party/ から読み込みました: {self.builder.party_path}"
            )
        except Exception as exc:
            self.print(f"🚨 読み込みに失敗しました: {exc}")

    def _change_slot_flow(self):
        try:
            slot_index = int(
                self.input("スロット番号を入力してください (0-5): ").strip()
            )
        except ValueError:
            self.print("🚨 数字を入力してください。")
            return

        if slot_index < 0 or slot_index > 5:
            self.print("🚨 0から5までの番号を入力してください。")
            return

        self.print("何を変更しますか?")
        self.print("  1) ポケモン種族")
        self.print("  2) 技")
        self.print("  3) 努力値")
        self.print("  4) 性格")
        self.print("  5) 特性")
        choice = self.input("> ").strip()

        if choice == "1":
            self._change_species(slot_index)
        elif choice == "2":
            self._change_moves(slot_index)
        elif choice == "3":
            self._change_ev(slot_index)
        elif choice == "4":
            self._change_nature(slot_index)
        elif choice == "5":
            self._change_ability(slot_index)
        else:
            self.print("🚨 無効な選択です。")

    def _change_species(self, slot_index):
        try:
            pokemon_id = int(self.input("ポケモンIDを入力してください: ").strip())
            self.builder.change_pokemon_species(slot_index, pokemon_id)
            self.print("ポケモンを変更しました。")
        except Exception as exc:
            self.print(f"🚨 変更に失敗しました: {exc}")

    def _change_moves(self, slot_index):
        try:
            pokemon = self.builder.get_current_party()["pokemon"][slot_index]  # type: ignore
            pokemon_id = pokemon["pokemon_id"]
            if pokemon_id == 0:
                self.print(
                    "🚨 空の枠には技を割り当てることはできません。まずポケモンを選択してください。"
                )
                return

            learnable = self.builder.get_learnable_moves(pokemon_id)
            self.print(f"候補技: {learnable}")
            raw_moves = self.input(
                "4つの技IDをスペース区切りで入力してください: "
            ).strip()
            move_ids = [int(value) for value in raw_moves.split()]
            self.builder.change_pokemon_moves(slot_index, move_ids)
            self.print("技を更新しました。")
        except ValueError:
            self.print("🚨 4つの技IDを数字でスペース区切りで入力してください。")
        except Exception as exc:
            self.print(f"🚨 更新に失敗しました: {exc}")

    def _change_ev(self, slot_index):
        try:
            stat_name = self.input("ステータス名を入力してください: ").strip()
            value = int(self.input("値を入力してください: ").strip())
            self.builder.change_pokemon_ev(slot_index, stat_name, value)
            self.print("努力値を更新しました。")
        except Exception as exc:
            self.print(f"🚨 更新に失敗しました: {exc}")

    def _change_nature(self, slot_index):
        try:
            natures = self.builder.get_nature_list()
            self.print("性格候補:")
            for nature in natures:
                self.print(f"  {nature['nature_id']}: {nature['nature_name']}")
            nature_id = int(self.input("性格IDを入力してください: ").strip())
            self.builder.change_pokemon_nature(slot_index, nature_id)
            self.print("性格を変更しました。")
        except ValueError:
            self.print("🚨 数字で性格IDを入力してください。")
        except Exception as exc:
            self.print(f"🚨 変更に失敗しました: {exc}")

    def _change_ability(self, slot_index):
        try:
            pokemon = self.builder.get_current_party()["pokemon"][slot_index]  # type: ignore
            pokemon_id = pokemon["pokemon_id"]
            if pokemon_id == 0:
                self.print(
                    "🚨 空の枠には特性を割り当てることはできません。まずポケモンを選択してください。"
                )
                return

            abilities = self.builder.get_available_abilities(pokemon_id)
            if not abilities:
                self.print("🚨 このポケモンには利用可能な特性がありません。")
                return

            self.print("特性候補:")
            for ability in abilities:
                self.print(f"  {ability['ability_id']}: {ability['ability_name']}")
            ability_id = int(self.input("特性IDを入力してください: ").strip())
            self.builder.change_pokemon_ability(slot_index, ability_id)
            self.print("特性を変更しました。")
        except ValueError:
            self.print("🚨 数字で特性IDを入力してください。")
        except Exception as exc:
            self.print(f"🚨 変更に失敗しました: {exc}")


if __name__ == "__main__":
    PartyManagerCUI().start()
