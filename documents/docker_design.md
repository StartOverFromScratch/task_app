# タスク管理システム Docker環境構築設計書

バージョン: 1.0 | 作成日: 2026-02-27

---

## 目次

1. [設計方針](#1-設計方針)
2. [サービス構成](#2-サービス構成)
3. [ディレクトリ構成](#3-ディレクトリ構成)
4. [Composeファイル分離戦略](#4-composeファイル分離戦略)
5. [各サービスのコンテナ設計](#5-各サービスのコンテナ設計)
6. [ネットワーク設計](#6-ネットワーク設計)
7. [ボリューム設計](#7-ボリューム設計)
8. [環境変数管理](#8-環境変数管理)
9. [将来のPostgreSQL移行パス](#9-将来のpostgresql移行パス)
10. [起動・停止手順](#10-起動停止手順)
11. [制約・前提条件](#11-制約前提条件)

---

## 1. 設計方針

### 1.1 基本方針

- 開発環境（dev）と本番環境（prod）でComposeファイルを分離する
- 現時点ではDBはSQLite（ファイルベース）のままコンテナ化し、PostgreSQL移行を最小変更で実現できる構造を維持する
- 各サービスは独立したコンテナで動作し、Docker内ネットワークで通信する
- 環境差分は環境変数と`.env`ファイルで吸収し、コードは変更しない

### 1.2 開発・本番の主な差分

| 項目 | 開発（dev） | 本番（prod） |
|------|-----------|------------|
| フロントエンドビルド | `nuxt dev`（HMR有効） | `nuxt build` + `nuxt preview` または静的サーブ |
| バックエンド起動 | `uvicorn --reload`（ホットリロード有効） | `uvicorn`（reload無効、ワーカー数指定） |
| ソースコードマウント | ホストのソースをボリュームでマウント | イメージにCOPYして内包 |
| CORSオリジン | `http://localhost:3000` | 本番ドメイン |
| SQLiteファイル | `backend/tasks.db`（ホストに永続化） | コンテナ外ボリュームに永続化 |
| ログレベル | DEBUG / SQLエコーあり | INFO / SQLエコーなし |

---

## 2. サービス構成

### v0.1（現在）

```
┌─────────────────────────────────────────────┐
│  Docker Compose                             │
│                                             │
│  ┌───────────────┐   ┌───────────────────┐  │
│  │  frontend     │   │  backend          │  │
│  │  Nuxt 4       │──▶│  FastAPI          │  │
│  │  :3000        │   │  :8000            │  │
│  └───────────────┘   └────────┬──────────┘  │
│                               │             │
│                        [SQLite ファイル]     │
│                        (volume mount)       │
└─────────────────────────────────────────────┘
```

### 将来（PostgreSQL導入後）

```
┌─────────────────────────────────────────────┐
│  Docker Compose                             │
│                                             │
│  ┌───────────────┐   ┌───────────────────┐  │
│  │  frontend     │   │  backend          │  │
│  │  Nuxt 4       │──▶│  FastAPI          │  │
│  │  :3000        │   │  :8000            │  │
│  └───────────────┘   └────────┬──────────┘  │
│                               │             │
│                      ┌────────▼──────────┐  │
│                      │  db               │  │
│                      │  PostgreSQL       │  │
│                      │  :5432            │  │
│                      └───────────────────┘  │
└─────────────────────────────────────────────┘
```

---

## 3. ディレクトリ構成

Dockerに関するファイルはリポジトリルートに集約する。

```
project-root/
├── docker-compose.yml              # 共通定義（ベース）
├── docker-compose.dev.yml          # 開発環境オーバーライド
├── docker-compose.prod.yml         # 本番環境オーバーライド
│
├── .env.example                    # 環境変数テンプレート（コミット対象）
├── .env                            # 実際の環境変数（.gitignore対象）
├── .env.dev                        # 開発環境用（.gitignore対象）
├── .env.prod                       # 本番環境用（.gitignore対象）
│
├── backend/
│   ├── Dockerfile                  # バックエンドコンテナ定義
│   ├── Dockerfile.dev              # 開発環境用（ホットリロード対応）
│   ├── requirements.txt
│   └── ...（既存ファイル）
│
├── frontend/
│   ├── Dockerfile                  # フロントエンドコンテナ定義
│   ├── Dockerfile.dev              # 開発環境用（HMR対応）
│   └── ...（既存ファイル）
│
└── documents/
    └── docker_design.md            # 本ドキュメント
```

---

## 4. Composeファイル分離戦略

Docker Composeのオーバーライド方式を採用する。`docker-compose.yml`に共通定義を置き、環境固有の差分を`docker-compose.dev.yml` / `docker-compose.prod.yml`で上書きする。

### 4.1 ファイル役割

| ファイル | 役割 | コミット |
|---------|------|---------|
| `docker-compose.yml` | サービス定義・ネットワーク・ボリュームの骨格 | ○ |
| `docker-compose.dev.yml` | 開発用オーバーライド（マウント・HMR・reload） | ○ |
| `docker-compose.prod.yml` | 本番用オーバーライド（ビルド済みイメージ・ワーカー数） | ○ |
| `.env` / `.env.dev` / `.env.prod` | 実際の秘密情報・環境固有値 | ✗ |
| `.env.example` | テンプレート（値は空またはダミー） | ○ |

### 4.2 起動コマンドの対応

```bash
# 開発環境
docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up

# 本番環境
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d
```

---

## 5. 各サービスのコンテナ設計

### 5.1 backend（FastAPI）

#### Dockerfile方針（本番）

| ステップ | 内容 |
|---------|------|
| ベースイメージ | `python:3.11-slim` |
| 作業ディレクトリ | `/app` |
| 依存インストール | `requirements.txt`をCOPYしてpip install |
| ソースCOPY | `backend/`以下を`/app`にCOPY |
| 起動コマンド | `uvicorn main:app --host 0.0.0.0 --port 8000` |

#### Dockerfile.dev追加事項

- ソースはホストからボリュームマウント（COPYしない）
- `--reload`オプションを付与してホットリロードを有効化
- SQLAlchemyのSQLエコーを有効化（`echo=True`）

#### 公開ポート

| 環境 | ホスト | コンテナ |
|------|-------|---------|
| 開発 | 8000 | 8000 |
| 本番 | （リバースプロキシ経由が望ましい） | 8000 |

#### ヘルスチェック

既存の`GET /health`エンドポイントを使用する。

```
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

---

### 5.2 frontend（Nuxt 4）

#### Dockerfile方針（本番）

| ステップ | 内容 |
|---------|------|
| ベースイメージ | `node:20-slim`（ビルドステージ） / `node:20-slim`（実行ステージ） |
| マルチステージビルド | ビルド成果物のみ実行イメージにCOPY |
| 作業ディレクトリ | `/app` |
| ビルドコマンド | `npm ci && npm run build` |
| 起動コマンド | `node .output/server/index.mjs` |

#### Dockerfile.dev追加事項

- ソースはホストからボリュームマウント
- `npm run dev -- --host`でHMR有効（コンテナ外から接続可能にするため`--host`必須）
- `node_modules`はコンテナ内に隔離（名前付きボリュームを使用し、ホストの`node_modules`と干渉させない）

#### 公開ポート

| 環境 | ホスト | コンテナ |
|------|-------|---------|
| 開発 | 3000 | 3000 |
| 本番 | 3000（またはリバースプロキシ経由） | 3000 |

---

### 5.3 db（PostgreSQL）—将来追加

現時点では定義しないが、追加時の仕様を以下に記録しておく。

| 項目 | 値 |
|------|---|
| ベースイメージ | `postgres:16-alpine` |
| 公開ポート | コンテナ内のみ（5432）。ホストには原則非公開 |
| データ永続化 | 名前付きボリューム（`postgres_data`）にマウント |
| 初期化 | `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD`を環境変数で設定 |
| ヘルスチェック | `pg_isready`コマンドを使用 |
| backendの依存 | `depends_on: db: condition: service_healthy`でDB起動後にbackendを起動 |

---

## 6. ネットワーク設計

### 6.1 ネットワーク構成

単一のDockerブリッジネットワーク（`app-network`）を定義し、全サービスを所属させる。

```
app-network（bridge）
  ├── frontend   → backend への通信: http://backend:8000
  ├── backend    → db（将来）への通信: postgresql://db:5432/...
  └── db（将来）
```

### 6.2 サービス間通信のホスト名

Docker Compose内では、サービス名がそのままホスト名として機能する。

| 通信元 | 通信先 | URL |
|-------|-------|-----|
| frontend（SSR/サーバー側） | backend | `http://backend:8000` |
| frontend（ブラウザ側） | backend | `http://localhost:8000`（開発）/ 本番ドメイン経由 |
| backend | db（将来） | `postgresql://db:5432/taskdb` |

> **注意:** Nuxt 4のSSR（サーバーサイドレンダリング）ではAPIリクエストがサーバー側で発生するため、環境変数を2つに分ける。
> - `NUXT_PUBLIC_API_BASE`: ブラウザからアクセスするURL（例: `http://localhost:8000`）
> - `NUXT_API_BASE_SERVER`: サーバーサイド（SSR）からアクセスするURL（例: `http://backend:8000`）

### 6.3 外部公開ポート

| サービス | 開発 | 本番（案） |
|---------|------|----------|
| frontend | 3000 | 80/443（リバースプロキシ推奨） |
| backend | 8000 | リバースプロキシ経由（非公開推奨） |
| db（将来） | 非公開 | 非公開 |

---

## 7. ボリューム設計

### 7.1 現在（SQLite）

| ボリューム | 種別 | 用途 |
|---------|-----|------|
| `./backend/tasks.db` | バインドマウント（開発） | SQLiteファイルの永続化 |
| `sqlite_data`（名前付き） | 名前付きボリューム（本番） | SQLiteファイルの永続化 |
| `frontend_node_modules` | 名前付きボリューム | `node_modules`のホスト隔離 |

### 7.2 将来（PostgreSQL追加後）

| ボリューム | 種別 | 用途 |
|---------|-----|------|
| `postgres_data` | 名前付きボリューム | PostgreSQLデータの永続化 |
| `frontend_node_modules` | 名前付きボリューム | `node_modules`のホスト隔離 |

### 7.3 開発時のソースマウント方針

| サービス | マウント | 理由 |
|---------|---------|------|
| backend | `./backend:/app`（バインドマウント） | ホットリロードのためソースを直接マウント |
| frontend | `./frontend:/app`（バインドマウント） | HMRのためソースを直接マウント |
| frontend（node_modules） | `frontend_node_modules:/app/node_modules`（名前付き） | ホストのnode_modulesとの競合を防ぐ |

---

## 8. 環境変数管理

### 8.1 変数一覧

| 変数名 | 設定先 | 開発値 | 本番値 |
|--------|-------|-------|-------|
| `DATABASE_URL` | backend | `sqlite:///./tasks.db` | `sqlite:///./tasks.db` または `postgresql://...`（移行後） |
| `CORS_ORIGINS` | backend | `http://localhost:3000` | 本番フロントエンドURL |
| `LOG_LEVEL` | backend | `DEBUG` | `INFO` |
| `WORKERS` | backend | 1 | 2以上（CPUコア数に応じて） |
| `NUXT_PUBLIC_API_BASE` | frontend | `http://localhost:8000` | 本番バックエンドURL |
| `NUXT_API_BASE_SERVER` | frontend | `http://backend:8000` | `http://backend:8000` |

### 8.2 .env.exampleの内容（テンプレート）

```dotenv
# === Backend ===
DATABASE_URL=sqlite:///./tasks.db
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=DEBUG
WORKERS=1

# === Frontend ===
# ブラウザ側API URL（ホストから見たURL）
NUXT_PUBLIC_API_BASE=http://localhost:8000
# サーバーサイド（SSR）API URL（Docker内ネットワーク経由）
NUXT_API_BASE_SERVER=http://backend:8000

# === DB（将来: PostgreSQL）===
# POSTGRES_DB=taskdb
# POSTGRES_USER=taskuser
# POSTGRES_PASSWORD=（強力なパスワードを設定）
# POSTGRES_HOST=db
# POSTGRES_PORT=5432
```

### 8.3 秘密情報の管理方針

| ファイル | 用途 | Gitコミット |
|---------|------|-----------|
| `.env.example` | テンプレート（値は空またはダミー） | ○ |
| `.env.dev` | 開発用実値 | ✗（.gitignoreに追加） |
| `.env.prod` | 本番用実値 | ✗（.gitignoreに追加） |

本番環境でパスワード等の機密情報を扱う場合は、Docker Secretsまたは外部シークレット管理ツール（AWS Secrets Manager等）への移行を検討する。

---

## 9. 将来のPostgreSQL移行パス

### 9.1 移行ステップ

本設計はSQLite→PostgreSQL移行を最小変更で実現できるよう、以下の方針で構成している。

| ステップ | 作業内容 |
|---------|---------|
| 1. dbサービス追加 | `docker-compose.yml`にPostgreSQLサービスブロックを追加 |
| 2. 環境変数変更 | `DATABASE_URL`を`postgresql://...`形式に変更 |
| 3. Alembicマイグレーション実行 | `alembic upgrade head`（既存マイグレーションはそのまま使用可能） |
| 4. backendのdepends_on追加 | `db`サービスのヘルスチェック完了を待機するよう設定 |
| 5. requirements.txtにpsycopg2追加 | `psycopg2-binary`を追加 |
| 6. データ移行 | 必要に応じてSQLiteからPostgreSQLへデータをエクスポート・インポート |

### 9.2 アプリケーションコードへの影響

SQLAlchemy + Alembicを採用しているため、`DATABASE_URL`の変更のみでORM・マイグレーションの挙動が切り替わる。アプリケーションコード（`services/` / `models/`）の変更は不要。

ただし以下の点は確認が必要：
- SQLite固有の`batch_alter_table`を使った既存マイグレーションファイルは、PostgreSQL向けに新規マイグレーションを作成する
- `render_as_batch=True`はSQLite専用のため、PostgreSQL環境では除外する

### 9.3 移行後のdocker-compose.yml追加イメージ

```yaml
# 将来追加するブロックのイメージ（実装時に詳細化）
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    depends_on:
      db:
        condition: service_healthy

volumes:
  postgres_data:
```

---

## 10. 起動・停止手順

### 10.1 初回セットアップ

```bash
# 1. 環境変数ファイルを作成
cp .env.example .env.dev

# 2. .env.devを編集して値を設定（必要に応じて）

# 3. イメージのビルド
docker compose -f docker-compose.yml -f docker-compose.dev.yml build

# 4. マイグレーション実行（初回のみ）
docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm backend alembic upgrade head

# 5. 起動
docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up
```

### 10.2 日常的な起動・停止（開発）

```bash
# 起動
docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up

# バックグラウンド起動
docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up -d

# 停止
docker compose down

# コンテナ・ボリュームごと削除（完全リセット）
docker compose down -v
```

### 10.3 本番環境の起動

```bash
# イメージビルド
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# マイグレーション実行
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod run --rm backend alembic upgrade head

# 起動（デタッチモード）
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d
```

### 10.4 マイグレーション操作

```bash
# 最新へ適用
docker compose run --rm backend alembic upgrade head

# 1ステップロールバック
docker compose run --rm backend alembic downgrade -1

# 現在のリビジョン確認
docker compose run --rm backend alembic current

# 新規マイグレーション生成
docker compose run --rm backend alembic revision --autogenerate -m "説明"
```

### 10.5 ログ確認

```bash
# 全サービス
docker compose logs -f

# サービス指定
docker compose logs -f backend
docker compose logs -f frontend
```

---

## 11. 制約・前提条件

| 項目 | 内容 |
|------|------|
| Docker Engine | 26以上を推奨（`docker compose`プラグイン方式を使用） |
| 対応OS | Linux / macOS / Windows（WSL2経由） |
| SQLiteの制約 | SQLiteはファイルロックの仕様上、コンテナを複数レプリカで起動することは非推奨。スケールアウトが必要になった時点でPostgreSQL移行を行う |
| ポート競合 | ホストの3000番・8000番が使用中の場合はComposeファイルで変更する |
| CORSの本番対応 | `CORS_ORIGINS`に本番フロントエンドのURLを正確に設定すること |
| セキュリティ | 本番環境でbackendポートをホストに直接公開しないこと。Nginx等のリバースプロキシを前段に置くことを推奨 |
