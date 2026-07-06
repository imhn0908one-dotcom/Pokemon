# Pokemon battle systems

ポケモンの戦闘システムを、ダメージ計算・パーティ管理・バトルシミュレーションへ展開するための Python プロジェクトです。CUI で試作しながら、将来的には GUI や AI 学習環境へスケールできる構成を目指しています。

This project is a Python-based implementation of Pokémon battle systems, designed to facilitate damage calculation, party management, and battle simulation. It starts with a command-line interface (CUI) prototype and aims to scale towards a graphical user interface (GUI) and AI learning environment in the future.

## 🌟 プロジェクトの概要

このプロジェクトは、ポケモンの戦闘ロジックを段階的に実装していくための基盤です。現時点では、CUI ベースでパーティ管理やバトル関連のロジックを実装し、今後の機能拡張に備えた構成になっています。

This project is basis of implementing Pokémon battle logic in stages. Currently, it focuses on command-line interface (CUI) based party management and battle-related logic, with a structure designed to accommodate future feature expansions.

## ✅ 完成済みの内容

現在のリポジトリには、以下の内容が実装されています。

- ポケモンのパーティを TOML 形式で作成・編集できる仕組み
- パーティ編集のための CUI インターフェース
- バトルロジック用の基本クラス群
  - `Single_Battle_Manager`
  - `Field_State` / `Side_State`
  - `Pokemon_Instance`
- 技・性格・特性・努力値を扱うためのデータ構造とロジック

## 🔭 これからの展望

今後の開発では、以下を目標に進める予定です。

- F1: 独立ダメージ計算ツールの完成
- F2: チェンジ型パーティマネージャーの改善
- F3: GUI 化
- F4: 完全バトルの実装
- F5: AI / 機械学習による最適化

## 🧠 設計思想

- UI 層とロジック層を分離し、CUI から GUI への移行を容易にする
- データ駆動型の構成で、パーティ・技・性格・特性を柔軟に扱えるようにする
- 高速なシミュレーションを前提とした、保守しやすい構造を意識する


## 🧰 必要な環境

- Python 3.12 以上
- uv（Astral 製の Python パッケージ管理ツール）

## 🚀 セットアップ手順（uv 前提）

### 1. uv をインストールする

macOS / Homebrew を使う場合:

```bash
brew install uv
```

または公式インストーラーを使う場合:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. リポジトリをクローンする

```bash
git clone <your-repository-url>
cd Pokemon
```

### 3. 仮想環境を作成し、依存関係をインストールする

このプロジェクトでは、依存関係の管理に uv を使用します。次のコマンドを実行すると、仮想環境が作成され、必要なパッケージが自動で入ります。

```bash
uv sync
```

### 4. 実行する

現在の実装は、主要なロジックや CUI 画面を直接実行する構成です。必要に応じて、対象スクリプトを `uv run python ...` で実行してください。

```bash
uv run python battle/party_manager_cui.py
```

## Recomend Extension

- [vscode-pokemon](https://marketplace.visualstudio.com/items?itemName=jakobhoeg.vscode-pokemon)
- [SQLite Viewer](https://marketplace.visualstudio.com/items?itemName=qwtel.sqlite-viewer)

## 📁 プロジェクト構成

- `battle/` : 戦闘ロジック、フィールド状態、パーティ管理関連
- `buildDB/` : ポケモン・技・タイプ・特性データの構築スクリプト
- `party/` : パーティの TOML ファイル

## 🗂️ 開発メモ
- MEMO.mdを確認すると開発に必要なことがまとめられている。
### データベースで扱う主要テーブル

- `pokemon` : ポケモンの基本情報と種族値
- `pokemon_move` : ポケモンが覚える技の対応関係
- `move_basicdata` : 技の基本情報
- `move_meta` : 技の追加効果・状態異常関連情報
- `move_stat_change` : 技による能力変化情報
- `nature_data` : 性格補正データ
- `pokemon_ability` : 特性の対応関係
- `ability_basicdata` : 特性の基本情報

## 📄 ライセンス

このプロジェクトは MIT License のもとで公開されています。