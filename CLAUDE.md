# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

「構造収束型タスク管理システム」。単純なTODO管理ではなく、探索・決定・実行を分離し、無限探索を防ぐ設計思想を持つ個人向けツール。

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| バックエンド | FastAPI (Python) |
| フロントエンド | Nuxt 4 + Nuxt UI + Pinia + TypeScript |
| DB | SQLite |
| ORM | SQLAlchemy |
| マイグレーション | Alembic |

## 開発コマンド

- 仮想環境は `backend/.venv`（Python 3.11.14）。`backend/.python-version` で pyenv バージョンを固定済み。
- コマンドはすべて **リポジトリルート** から実行。`source activate` は使用しない。
- 各バイナリは `backend/.venv/bin/` を直接指定する。

### セットアップ

```bash
backend/.venv/bin/pip install -r backend/requirements.txt
```

### バックエンド起動

```bash
cd backend && .venv/bin/uvicorn main:app --reload
```

### マイグレーション

```bash
cd backend && .venv/bin/alembic upgrade head
cd backend && .venv/bin/alembic revision --autogenerate -m "説明"
```

### テスト実行

```bash
backend/.venv/bin/pytest backend/tests/ -v
backend/.venv/bin/pytest backend/tests/test_tasks.py                      # 単一ファイル
backend/.venv/bin/pytest backend/tests/test_tasks.py::test_function_name  # 単一テスト
```

※ テスト実行は `backend/` 配下で行う（`pytest.ini` がそこにあるため）。

---

### フロントエンド（`frontend/`）

パッケージマネージャーは **npm**。

```bash
# セットアップ
cd frontend && npm install

# 開発サーバー起動（http://localhost:3000）
cd frontend && npm run dev

# 型チェック
cd frontend && npm run typecheck

# lint
cd frontend && npm run lint

# ビルド
cd frontend && npm run build
```

**環境変数:** `frontend/.env` に `NUXT_PUBLIC_API_BASE=http://localhost:8000` を設定（`.env.example` 参照）。

## バックエンドアーキテクチャ（`backend/`）

4層構造：

```
api/        ← FastAPIルーター（HTTPレイヤー）
schemas/    ← Pydanticモデル（入出力型定義）
services/   ← ビジネスロジック
models/     ← SQLAlchemyモデル（DBテーブル）
db/         ← セッション管理・ベース定義
```

リクエストは `api → schemas → services → models → SQLite` の順に流れる。

## データモデルの重要な設計

**tasks テーブルの特殊フィールド：**
- `task_type`: `research` / `decision` / `execution` の3種
- `status`: `todo` / `doing` / `done` / `carryover_candidate` / `needs_redefine` / `snoozed`
- `exploration_limit`: 調査タスクの探索上限件数（無限探索防止）
- `reversible`: 可逆判定フラグ（仮決定で止まれるように）
- `decision_criteria`: 決定基準テキスト
- `done_criteria`: 完了条件（DoD）テキスト
- `parent_id`: 親子タスク構造

**放置検知ルール（`last_updated_at` 基準）：**
- priority=must → 7日超で放置
- priority=should → 21日超で放置

## フロントエンドアーキテクチャ（`frontend/app/`）

Nuxt 4 の `app/` ディレクトリ規約に従う。

```
pages/        ← ファイルベースルーティング（7画面）
components/   ← UI部品（task/ checklist/ carryover/ capture/ common/）
composables/  ← ビジネスロジック・ストア更新・エラーハンドリング
stores/       ← Pinia ストア（taskStore / carryoverStore / captureStore）
repositories/ ← API通信のみ（$fetch ラッパー）
types/        ← TypeScript 型定義
utils/        ← 共通処理（staleThreshold / dateFormat）
```

**呼び出しフロー:** `pages/components → composables → repositories → FastAPI`

- `repositories/` はエラーをそのまま投げ上げる
- `composables/` で catch して `useToast` で通知
- `runtimeConfig.public.apiBase` で API ベース URL を管理（`.env` の `NUXT_PUBLIC_API_BASE`）

## 設計ドキュメント

- `README.md` - 要件定義書
- `documents/design_overview.md` - 全体設計・DFD・画面遷移・アーキテクチャ
- `documents/backend_design.md` - API一覧・スキーマ詳細・OpenAPI定義・マイグレーション設計
- `documents/frontend_design.md` - ディレクトリ構成・Repositoryパターン・Piniaストア設計

## 実装状況

### 2026-02-26 完了

**バックエンド基盤・API層の実装完了（テスト 55/55 PASS）**

- 環境: `backend/.venv`（Python 3.11.14）、`requirements.txt` 作成済み
- DB: `alembic upgrade head` 実行済み（`backend/tasks.db` 生成）
- 実装済みファイル:
  - `app/core/config.py` / `app/db/base.py` / `app/db/session.py`
  - `app/models/` — Task・TaskChecklistItem・CompletionLog・CaptureItem
  - `app/schemas/` — enums・task・checklist_item・completion_log・capture_item
  - `app/services/` — task_service・carryover_service・capture_service
  - `app/api/` — tasks・checklist・carryover・captures
  - `main.py` — ルーター登録済み
  - `tests/` — test_tasks・test_checklist・test_carryover + conftest

**実装済み API:**
- `GET/POST /tasks`、`GET/PATCH/DELETE /tasks/{id}`
- `GET /tasks/stale`（放置検知・動的計算）
- `GET /tasks/carryover-candidates`、`POST /tasks/{id}/carryover`
- `POST /tasks/{id}/complete`、`GET /tasks/{id}/completion-log`
- `GET /tasks/{id}/children`、`POST /tasks/{id}/children`
- `GET /tasks/{id}/convergence`
- `GET/POST /tasks/{id}/checklist`、`PATCH /tasks/{id}/checklist/{item_id}`
- `POST /tasks/{id}/checklist/{item_id}/extract`
- `GET/POST /captures`、`PATCH/DELETE /captures/{id}`

**注意点（実装時に判明した設計上の決定）:**
- `carryover.router` は `tasks.router` より先に `main.py` へ登録すること（`/carryover-candidates` が `/{task_id}` に捕捉されるのを防ぐ）
- `last_updated_at` は SQLite の `onupdate` が効かないため、service 層で `datetime.utcnow()` を明示的にセット
- Task の自己参照リレーションシップは `remote_side=[id]` を `parent` 側に指定

**次のステップ:** フロントエンド（Nuxt 4）の実装。`documents/frontend_design.md` 参照。

### 2026-02-27 完了

**フロントエンド全層の実装完了（lint PASS、typecheck PASS）**

- 環境: Nuxt 4 + Nuxt UI v4 + Pinia、パッケージマネージャーは npm
- `frontend/.env` に `NUXT_PUBLIC_API_BASE=http://localhost:8000` 設定済み
- 実装済みファイル:
  - `app/types/` — task・checklist・carryover・capture・completion（全型定義）
  - `app/repositories/` — task・checklist・carryover・capture（全 API 通信層）
  - `app/stores/` — taskStore・carryoverStore・captureStore
  - `app/utils/` — staleThreshold・dateFormat
  - `app/composables/` — useTask・useChecklist・useCarryover・useCapture・useStale・useErrorToast
  - `app/components/` — common/（PageHeader・ConfirmDialog）、task/（TaskCard・TaskForm・TaskStatusBadge・TaskTypeBadge・TaskChildList）、checklist/（ChecklistItem・ChecklistPanel）、carryover/（CarryoverActionBar）、capture/（CaptureInput）
  - `app/pages/` — index・tasks/new・tasks/[id]/index・tasks/[id]/edit・carryover・stale・capture（全7画面）

**実装時の注意点:**
- `@pinia/nuxt` は latest（Nuxt 4 対応版）を使用すること
- `app/` ディレクトリが Nuxt 4 のソースルート（Nuxt 3 の `/` 直下相当）
- `repositories/` ディレクトリに個別ファイルと `index.ts` が同居すると Nuxt の重複 auto-import WARN が出るが動作に問題なし
- Vue `<script setup>` の props は `const { foo } = defineProps<...>()` の形で分割代入する（`const props = defineProps<...>()` は `props` unused として ESLint エラーになる）
- `TaskUpdateRequest.status` は `Exclude<TaskStatus, 'done'>` 型（完了遷移は `POST /complete` のみ）
