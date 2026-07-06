# Pokemon Project Notes

## move_basicdata の主要キー
- `id`: 技ID（主キー）
- `name`: 技名
- `type_id`: タイプID
- `power`: 威力
- `accuracy`: 命中率
- `pp`: PP
- `priority`: 優先度
- `damage_class_id`: ダメージクラスID
- `target_id`: 対象ID

## move_meta の主要キー
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

## move_stat_change の主要キー
- `id`: 技ID（主キー）
- `stat_id`: 能力値ID
- `change`: 能力変化量

## 主要テーブル一覧と用途
### pokemon
- ポケモンの基本情報と種族値を保持する。
- 主要カラム例: `id`, `name`, `hp`, `attack`, `defense`, `special_attack`, `special_defense`, `speed`

### pokemon_move
- ポケモンが覚える技の対応関係を保持する中間テーブル。
- 主要カラム例: `pokemon_id`, `move_id`

### move_basicdata
- 技の基本情報を保持する。
- 主要カラム例: `id`, `name`, `type_id`, `power`, `accuracy`, `pp`, `priority`, `damage_class_id`, `target_id`

### move_meta
- 技の追加効果や状態異常に関するメタ情報を保持する。
- 主要カラム例: `id`, `min_hits`, `max_hits`, `min_turns`, `max_turns`, `drain`, `healing`, `crit_rate`, `ailment_id`, `ailment_chance`, `flinch_chance`, `stat_chance`

### move_stat_change
- 技による能力変化の内容を保持する。
- 主要カラム例: `id`, `stat_id`, `change`

### nature_data
- 性格補正データを保持する。
- 主要カラム例: `id`, `name`, `increased_stat_id`, `decreased_stat_id`

### pokemon_ability
- ポケモンが持つ特性の対応関係を保持する。
- 主要カラム例: `pokemon_id`, `ability_id`, `is_hidden`

### ability_basicdata
- 特性の基本情報を保持する。
- 主要カラム例: `id`, `name`

## 利用メモ
- `battle_manager.py` では `move_basicdata` から技の基本情報を取得する。
- `move_meta` と `move_stat_change` は、技の追加効果・状態異常・能力変化を実装するために使う。
- `battle_engine.py` では `pokemon`, `nature_data`, `move_basicdata`, `pokemon_ability`, `ability_basicdata` を中心に初期化を行う。

## battle 配下のクラスとメソッドの説明

### Pokemon_Instance
- 役割: 1匹分のポケモンをインスタンス化し、戦闘に必要な基礎情報・実数値・PP管理を行う。
- メソッド一覧:
  - `__init__`: TOML から受け取ったポケモン情報をもとに、ID・名前・技・性格・努力値・特性を保持し、種族値・性格補正・HP・PPを初期化する。
  - `init_moves_and_pp`: 技ID一覧を受け取り、`move_basicdata` から PP と技名を取得して `moves_pp` / `moves_name` を作る。
  - `get_rank_multiplier`: ランク補正の倍率を計算する。
  - `get_effective_stat`: ランク補正を反映した実効ステータスを計算する。
  - `show_status`: 現在の HP・ステータス・PP・技名をコンソールへ表示する。
  - `toml_input`: TOML ファイルを読み込む補助関数。

### Single_Battle_Manager
- 役割: 2体のポケモンを用いたシングルバトルの進行を管理する。
- メソッド一覧:
  - `__init__`: 対戦する2体のポケモンを保持し、ターン数・勝者情報を初期化する。
  - `move_basic_data`: 指定技IDの `move_basicdata` レコードを取得する。
  - `move_meta_data`: 指定技IDの `move_meta` レコードを取得する。
  - `calculate_final_priority`: 技の優先度を計算する。現状は基本値を取得しているだけ。

### Field_State / Side_State
- 役割: バトルフィールドの状態を管理する。
- メソッド一覧:
  - `Side_State.__init__`: ステルスロック・まきびし・どくびし・リフレクター・ひかりのかべの残りターンなどを初期化する。
  - `Field_State.__init__`: 天候・トリックルーム・プレイヤーA/B側の陣地情報を初期化する。

### Party_Builder
- 役割: 対話形式でパーティを作成し、TOML に保存する。
- メソッド一覧:
  - `connect_db`: SQLite に接続する。
  - `close_db`: 接続を閉じる。
  - `start_session`: パーティ名入力・ポケモン追加・TOML保存までの全体フローを回す。
  - `_input_pokemon`: 1匹分のポケモン入力をまとめて処理する。
  - `_input_moves`: 4つの技IDを入力する。
  - `_input_nature`: 性格IDを入力する。
  - `_input_ability`: 特性IDを入力する。
  - `_input_evs`: 努力値を入力する。
  - `save_to_toml`: 作成したパーティを TOML へ書き出す。

## 構造上の改善点（変更なし）
- `battle_engine.py` と `battle_manager.py` の責務が混在しており、今後は「ポケモンの状態管理」と「バトル進行管理」を分けると保守しやすい。
- `Pokemon_Instance` の `__init__` が種族値計算・性格補正・PP初期化・DBアクセスをまとめて担当しているため、分割すると読みやすくなる。
- `Single_Battle_Manager` は今後 `turn_loop` や `apply_move_effects` などのバトルフェーズ処理を追加する前提で、メソッドを段階的に増やす構造にした方が自然。
- `Party_Builder` は対話入力ロジックと DB 依存のロジックが強く結びついているため、入力UI層とデータ取得層を分けると再利用しやすい。
- `Field_State` / `Side_State` は今後の状態異常・天候・場の効果を追加する前提で、メソッドを持つ構造に拡張しやすい。

[ダメージ計算式サイト](https://champions.pokewiki.net/%E3%83%80%E3%83%A1%E3%83%BC%E3%82%B8%E8%A8%88%E7%AE%97%E5%BC%8F)