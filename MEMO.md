# MEMO

このドキュメントは、ポケモンバトルシステム開発で使う主要なデータ構造・変数・DBテーブルの意味をまとめたメモです。

## 0. 今後の優先順位

1. ダメージ計算機の実装
   - アタック側 / ディフェンス側のポケモン選択
   - 技、環境、努力値を設定
   - 最低/最大ダメージを算出
2. 計算機能を組み込んだモダンな GUI の構築
3. ダメージ計算メソッドを用いたバトルシステム開発
4. パーティ管理、バトル拡張、AI 最適化

`battle/` フォルダ内の既存インスタンスメソッドは、現在の優先度に合わせて不要なら削除して構いません。


## 1. DBの主要テーブルと用途

### pokemon
- ポケモンの基本情報と種族値を保持する。
- 主要カラム例:
  - `id`: ポケモンID（主キー）
  - `name`: 名前
  - `hp`: HP種族値（DB列名）
  - `attack`: こうげき種族値（DB列名）
  - `defense`: ぼうぎょ種族値（DB列名）
  - `special_attack`: とくこう種族値（DB列名）
  - `special_defense`: とくぼうさ種族値（DB列名）
  - `speed`: すばやさ種族値（DB列名）
- `POKEMON` ドメイン層では、非 `battle/` コード上で `HP`, `Atk`, `Def`, `SpA`, `SpD`, `Spe` を標準ステータス名として扱う。

### pokemon_move
- ポケモンが覚える技の対応関係を保持する中間テーブル。
- 主要カラム例:
  - `pokemon_id`: ポケモンID
  - `move_id`: 技ID

### move_basicdata
- 技の基本情報を保持する。
- 主要カラム例:
  - `id`: 技ID（主キー）
  - `name`: 技名
  - `type_id`: タイプID
  - `power`: 威力
  - `accuracy`: 命中率
  - `pp`: PP
  - `priority`: 優先度
  - `damage_class_id`: ダメージクラスID
  - `target_id`: 対象ID

### move_meta
- 技の追加効果や状態異常に関するメタ情報を保持する。
- 主要カラム例:
  - `id`: 技ID（主キー）
  - `min_hits`: 最小ヒット数
  - `max_hits`: 最大ヒット数
  - `min_turns`: 最小ターン数
  - `max_turns`: 最大ターン数
  - `drain`: 吸収量
  - `healing`: 回復量
  - `crit_rate`: クリティカル率
  - `ailment_id`: 状態異常ID
  - `ailment_chance`: 状態異常確率
  - `flinch_chance`: ひるみ確率
  - `stat_chance`: 能力変化確率

### move_stat_change
- 技による能力変化の内容を保持する。
- 主要カラム例:
  - `id`: 技ID（主キー）
  - `stat_id`: 能力値ID
  - `change`: 能力変化量

### nature_data
- 性格補正データを保持する。
- 主要カラム例:
  - `id`: 性格ID（主キー）
  - `name`: 性格名
  - `increased_stat_id`: 上昇する能力値ID
  - `decreased_stat_id`: 下降する能力値ID

### pokemon_ability
- ポケモンが持つ特性の対応関係を保持する。
- 主要カラム例:
  - `pokemon_id`: ポケモンID
  - `ability_id`: 特性ID
  - `is_hidden`: 隠れ特性かどうか

### ability_basicdata
- 特性の基本情報を保持する。
- 主要カラム例:
  - `id`: 特性ID（主キー）
  - `name`: 特性名

### gender_rate
- `pokemonspecies` から取得したメスになる確率を 8 分率で表現する。
- 主要カラム例:
  - `pokemon_id`: ポケモンID
  - `gender_rate`: 0〜8 の値で性別比を表す。
    - `0`: オスのみ
    - `8`: メスのみ
    - `-1`: 性別不明 / undefined

## 2. 主要な変数・概念

### ポケモンの状態に関する変数
- `id`: ポケモンID
- `name`: ポケモン名
- `moves`: 所持技IDのリスト
- `level`: レベル
- `nature`: 性格ID
- `evs`: 努力値
- `ability`: 特性ID
- `hp`: 現在HP
- `hp_max`: 最大HP
- `attack`, `defense`, `sp_attack`, `sp_defense`, `speed`: 実数値ステータス
- `moves_pp`: 技ごとの現在PP
- `moves_name`: 技IDに対応する技名
- `condition`: 状態異常などの状態
- `ranks`: ランク補正

### フィールド・場に関する変数
- `weather`: 天候
- `weather_turns`: 天候の残りターン数
- `trick_room_turns`: トリックルームの残りターン数
- `side_a`, `side_b`: 両サイドの状態
- `stealth_rock`: ステルスロックの有無
- `spikes_layers`: まきびしの層数
- `toxic_spikes_layers`: どくびしの層数
- `reflect_turns`: リフレクターの残りターン数
- `light_screen_turns`: ひかりのかべの残りターン数

## 3. 主要クラスと責務

### Pokemon_Instance
- 1匹分のポケモンをインスタンス化し、戦闘に必要な基礎情報・実数値・PP管理を行う。
- 主要メソッド:
  - `__init__`: 初期化
  - `init_moves_and_pp`: 技とPPを初期化
  - `get_rank_multiplier`: ランク補正倍率を計算
  - `get_effective_stat`: 実効ステータスを計算
  - `show_status`: ステータス表示
  - `from_toml`: TOML からポケモン情報を生成

### Single_Battle_Manager
- 2体のポケモンを用いたシングルバトルの進行を管理する。
- 主要メソッド:
  - `move_basic_data`: 技データを取得
  - `move_meta_data`: 技メタデータを取得
  - `calculate_final_priority`: 優先度を計算

### PartyManagerLogic
- パーティの作成・読み込み・保存・編集を管理する。
- 主要な責務:
  - 空のパーティの生成
  - 既存パーティの読み込み
  - スロットの変更
  - 努力値・性格・特性・技の更新
  - TOML への保存

### PartyManagerCUI
- パーティ管理の CUI インターフェースを提供する。
- 主要な責務:
  - ユーザー入力の受け付け
  - パーティ表示
  - 操作メニューの表示
  - 変更処理の実行

## 4. 開発時に見ると良いポイント

- `battle_manager.py` では技の基本データを `move_basicdata` から取得する。
- `move_meta` と `move_stat_change` は、将来的な追加効果・状態異常・能力変化実装に使う。
- `instance_making.py` では、ポケモンの種族値・性格補正・PP・実数値を計算する。
- `party_manager_logic.py` では、TOML と DB をつなぐ処理が中心となる。

## 5. 補足

- [Poke API GraphiQL console](https://graphql.pokeapi.co/v1beta2/console) を参照しながらデータ構造を確認している。
- 今後の実装では、まずダメージ計算機を完成させ、その後 GUI とバトルフェーズへ展開していく予定。
