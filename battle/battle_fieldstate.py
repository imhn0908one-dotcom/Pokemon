class Side_State:
    """プレイヤー個別の陣地（サイド）の状態を管理するクラス"""

    def __init__(self):
        # 設置物系
        self.stealth_rock = False  # ステルスロック
        self.spikes_layers = 0  # まきびし（最大3枚重なるので数値で管理）
        self.toxic_spikes_layers = 0  # どくびし

        # 壁系（残りターン数、0なら壁なし）
        self.reflect_turns = 0  # リフレクター
        self.light_screen_turns = 0  # ひかりのかべ


class Field_State:
    """バトルフィールド全体の空間状態を管理するクラス"""

    def __init__(self):
        # 1. 空間全体で共有する状態
        self.trick_room_turns = 0  # トリックルーム
        self.weather = "NONE"  # 天候
        self.weather_turns = 0

        # 2. プレイヤーA側・B側それぞれの陣地状態
        self.side_a = Side_State()  # プレイヤーAの陣地
        self.side_b = Side_State()  # プレイヤーBの陣地
