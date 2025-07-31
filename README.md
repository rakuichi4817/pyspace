# pyspace

![Quality & Test](https://github.com/rakuichi4817/pyspace/actions/workflows/quality-test.yml/badge.svg)

Pythonアプリケーションの実験・学習用リポジトリです。

## 主な特徴

- 最新のPython（>=3.12.3）で動作
- 依存管理・仮想環境は [uv](https://github.com/astral-sh/uv) を利用
- タスク管理は [mise](https://mise.jdx.dev/) を利用
- 静的解析・型チェック・テスト・フォーマットは ruff, mypy, pytest で自動化
- サンプルWebアプリ（Streamlit）付き
- GitHub ActionsによるCI（複数Pythonバージョンでのチェック）

## ディレクトリ構成

```text
pyspace/
├── src/              # アプリ本体
│   ├── main.py       # Streamlitサンプル
│   └── __init__.py
├── tests/            # テストコード
│   ├── test_sample.py
│   └── __init__.py
├── mise.toml         # miseタスク定義
├── pyproject.toml    # Pythonプロジェクト定義
├── uv.lock           # uvロックファイル
├── .github/
│   └── workflows/
│       └── quality-test.yml    # CI定義
└── README.md
```

## セットアップ

1. [mise](https://mise.jdx.dev/) をインストール
2. `mise install` で依存ツール・仮想環境をセットアップ
3. `mise init` で依存パッケージをインストール（`uv sync --all-extras` 実行）

## 開発・実行コマンド

- コード自動整形

  ```sh
  mise format
  ```

- 静的解析・型チェック

  ```sh
  mise lint
  ```

- テスト実行

  ```sh
  mise test
  ```

- サンプルアプリの起動（編集可能インストールで開発）

  ```sh
  mise app
  ```

  または

  ```sh
  uv run python -m streamlit run app/main.py
  ```

## CI（GitHub Actions）

- PR作成・mainブランチへのpush時に、Python 3.10/3.11/3.12で
  - ruffによるフォーマットチェック
  - mypyによる型チェック
  - pytestによるテスト
  を自動実行（Quality & Test job）

## 主要タスク（mise.toml）

- `mise init`   : 依存パッケージのインストール（`uv sync --all-extras`）
- `mise lint`   : ruff & mypyによる静的解析・型チェック
- `mise format` : ruffによる自動フォーマット
- `mise test`   : pytestによるテスト
- `mise mcp-server` : MCPサーバーの起動
- `mise app`    : Streamlitアプリの起動（mcp-serverも別途起動する必要があります）

