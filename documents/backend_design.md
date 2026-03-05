# タスク管理システム バックエンド設計書

**バージョン:** v0.2
**対象:** バックエンド（FastAPI）
**作成日:** 2026-02-25
**更新日:** 2026-03-05
**変更点:** `GET /tasks` にソートパラメータ（`sort_by` / `order`）を追加

---

## 目次

1. [DFD](#1-dfd)
2. [API一覧](#2-api一覧)
3. [状態遷移とAPI対応](#3-状態遷移とapi対応)
4. [APIスキーマ詳細](#4-apiスキーマ詳細)
5. [ディレクトリ構成](#5-ディレクトリ構成)
6. [マイグレーション設計](#6-マイグレーション設計)
7. [OpenAPI定義](#7-openapi定義)
8. [今後の課題](#8-今後の課題)

---

## 1. DFD

### レベル0（コンテキスト図）

```
[ユーザー]
    │
    ├─── タスク操作（登録/更新/完了/分割）──▶ ┌─────────────────────┐
    ├─── キャプチャ投入                       │                     │
    ├─── 繰り越し確定操作                     │  タスク管理システム  │──▶ タスク一覧・詳細
    └─── 放置検知確認                         │                     │──▶ 放置アラート
                                              │                     │──▶ 繰り越し候補一覧
                                              └─────────────────────┘
                                                        │
                                                    [SQLite DB]
```

外部エンティティはユーザーのみ。チーム・通知・外部連携はv0.2スコープ外。

---

### レベル1（主要プロセス分解）

```
[ユーザー]
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                                                     │
│  P1: タスク管理          P2: 探索収束管理            │
│  ・CRUD                  ・exploration_limit追跡     │
│  ・親子構造              ・decision_criteria確認     │
│  ・status遷移            ・reversible判定            │
│                                                     │
│  P3: 完了処理            P4: 放置検知               │
│  ・DoD確認               ・last_updated_at監視       │
│  ・completion_log生成    ・Must/Shouldで閾値分岐     │
│  ・checklist消込         ・needs_redefine誘導        │
│                                                     │
│  P5: 繰り越し管理        P6: CaptureBox             │
│  ・期限超過検知           ・capture_item登録         │
│  ・carryover_candidate化 ・関連タスクへの紐付け      │
│  ・手動確定操作           ・is_resolved管理          │
│                                                     │
└─────────────────────────────────────────────────────┘
            │
        [SQLite]
    tasks / completion_logs
    task_checklist_items / capture_items
```

### プロセスとAPIの対応

```
P1 タスク管理         → /tasks/**
P2 探索収束           → /tasks/{id}/convergence（+tasksのフィールドに埋め込み）
P3 完了処理           → /tasks/{id}/complete, /checklist
P4 放置検知           → /tasks/stale
P5 繰り越し           → /tasks/carryover-candidates, /carryover
P6 CaptureBox         → /captures/**
```

---

## 2. API一覧

### 設計方針

- エンドポイントは独立パス方式を採用（クエリパラメータ方式は不採用）
- `stale`は動的計算状態でありstatusカラムの値ではないため、`/tasks/stale`として独立させる
- `carryover`は通常のCRUDと文脈が異なるため、`carryover.py`として独立ルーターに分離する

### P1：タスク管理

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/tasks` | 一覧取得（status/typeフィルタ・ソート対応） |
| POST | `/tasks` | タスク登録 |
| GET | `/tasks/{id}` | 詳細取得（子タスク・チェックリスト含む） |
| PATCH | `/tasks/{id}` | 部分更新 |
| DELETE | `/tasks/{id}` | 削除 |
| GET | `/tasks/{id}/children` | 子タスク一覧 |
| POST | `/tasks/{id}/children` | 子タスク登録 |

### P2：探索収束管理

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/tasks/{id}/convergence` | 探索収束状態確認 |

### P3：完了処理

| メソッド | パス | 説明 |
|---|---|---|
| POST | `/tasks/{id}/complete` | タスク完了（completion_log生成） |
| GET | `/tasks/{id}/completion-log` | 完了ログ取得 |
| GET | `/tasks/{id}/checklist` | チェックリスト取得 |
| POST | `/tasks/{id}/checklist` | チェックリストアイテム追加 |
| PATCH | `/tasks/{id}/checklist/{item_id}` | チェックリストアイテム更新（is_done / text） |
| POST | `/tasks/{id}/checklist/{item_id}/extract` | アイテムをタスクとして切り出す |

### P4：放置検知

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/tasks/stale` | 放置タスク一覧（Must:7日/Should:21日超過） |

### P5：繰り越し管理

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/tasks/carryover-candidates` | 繰り越し候補一覧（動的判定） |
| POST | `/tasks/{id}/carryover` | 繰り越し確定 |

### P6：CaptureBox

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/captures` | キャプチャ一覧 |
| POST | `/captures` | キャプチャ登録 |
| PATCH | `/captures/{id}` | 更新（解決済み・関連タスク紐付け） |
| DELETE | `/captures/{id}` | 削除 |

---

## 3. 状態遷移とAPI対応

### 状態一覧

```
todo / doing / done / carryover_candidate / needs_redefine / snoozed
```

※ `stale`は動的計算状態のためstatusカラムには持たない

### 遷移図

```
[todo] ──────────────────────────────▶ [doing]
  │                                       │
  │                                       ▼
  │                                    [done]
  │
  ├──▶ [needs_redefine] ──▶ [doing]
  │
  └──▶ [snoozed] ──▶ [todo]

[doing] ──▶ [needs_redefine] ──▶ [doing]

期限超過（取得時動的判定）
  └──▶ [carryover_candidate]
           ├── 今日やる   ──▶ [todo]（due_date=today）
           ├── +2日       ──▶ [todo]（due_date+=2）
           ├── +7日       ──▶ [todo]（due_date+=7）
           └── 要再定義   ──▶ [needs_redefine]
```

### API対応表

| 遷移 | from → to | エンドポイント | 備考 |
|---|---|---|---|
| 着手 | todo → doing | `PATCH /tasks/{id}` | body: `status: doing` |
| 完了 | doing → done | `POST /tasks/{id}/complete` | completion_log生成 |
| 再定義要 | todo/doing → needs_redefine | `PATCH /tasks/{id}` | body: `status: needs_redefine` |
| 再定義から復帰 | needs_redefine → doing | `PATCH /tasks/{id}` | body: `status: doing` |
| 保留 | todo → snoozed | `PATCH /tasks/{id}` | body: `status: snoozed` |
| 保留解除 | snoozed → todo | `PATCH /tasks/{id}` | body: `status: todo` |
| 繰り越し候補化 | any → carryover_candidate | **動的判定（DBは変更しない）** | GET時に計算 |
| 繰り越し確定（今日） | carryover_candidate → todo | `POST /tasks/{id}/carryover` | body: `action: today` |
| 繰り越し確定（+2日） | carryover_candidate → todo | `POST /tasks/{id}/carryover` | body: `action: plus_2d` |
| 繰り越し確定（+7日） | carryover_candidate → todo | `POST /tasks/{id}/carryover` | body: `action: plus_7d` |
| 繰り越し→再定義 | carryover_candidate → needs_redefine | `POST /tasks/{id}/carryover` | body: `action: needs_redefine` |

### carryover_candidate遷移の設計方針

`GET /tasks/carryover-candidates`取得時にサーバー側でdue_date超過を計算して返す。DBのstatusは変更しない（動的判定方式）。

### PATCH経由でのdone指定禁止

`PATCH /tasks/{id}`でのstatus=done指定はバリデーションエラー（400）とする。完了はかならず`POST /tasks/{id}/complete`を経由させ、completion_logの生成漏れを防ぐ。

---

## 4. APIスキーマ詳細

### 共通型定義

```
TaskType        : research | decision | execution
TaskStatus      : todo | doing | done | carryover_candidate | needs_redefine | snoozed
Priority        : must | should
CarryoverAction : today | plus_2d | plus_7d | needs_redefine
SortBy          : due_date | created_at | priority | title  ※ v0.2追加
SortOrder       : asc | desc                                 ※ v0.2追加
```

### GET /tasks（v0.2更新）

**クエリパラメータ**

| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| status | TaskStatus | null（全ステータス） | ステータスフィルタ |
| task_type | TaskType | null | タスクタイプフィルタ |
| priority | Priority | null | 優先度フィルタ |
| parent_id | int \| null | 指定なし | 親IDフィルタ（0を渡すとparent_id=nullのみ取得） |
| sort_by | SortBy | `due_date` | ソートキー |
| order | SortOrder | `asc` | ソート順 |

**設計上の注意点**

- `parent_id` を指定しない場合、親タスク・子タスク両方を返す（一覧に子タスクを含める要件に対応）
- `due_date` ソート時、`due_date = null` のタスクは末尾に配置する（NULLs LAST）
- フロントエンド側でデフォルト呼び出しは `status=todo&status=doing&sort_by=due_date&order=asc` を想定

**Response** `200 OK`

```json
[
  {
    "id": "int",
    "title": "string",
    "task_type": "TaskType",
    "category": "string|null",
    "priority": "Priority",
    "status": "TaskStatus",
    "due_date": "date|null",
    "parent_id": "int|null",
    "done_criteria": "string",
    "decision_criteria": "string|null",
    "reversible": "bool|null",
    "exploration_limit": "int|null",
    "origin_checklist_item_id": "int|null",
    "last_updated_at": "datetime",
    "created_at": "datetime"
  }
]
```

### POST /tasks

**Request**

```json
{
  "title": "string, required",
  "task_type": "TaskType, required",
  "category": "string, optional",
  "priority": "Priority, required",
  "due_date": "date, optional",
  "parent_id": "int, optional",
  "done_criteria": "string, required",
  "decision_criteria": "string, optional",
  "reversible": "bool, optional",
  "exploration_limit": "int, optional"
}
```

**Response** `201 Created`：TaskResponse（上記と同形式）

### GET /tasks/{id}

**Response** `200 OK`（子タスク・チェックリスト・origin情報を含む）

```json
{
  "...TaskResponse",
  "children": ["...TaskResponse"],
  "checklist": [
    {
      "id": "int",
      "text": "string",
      "is_done": "bool",
      "order_no": "int",
      "extracted_task_id": "int|null"
    }
  ],
  "origin": {
    "parent_task_id": "int",
    "parent_task_title": "string",
    "checklist_item_text": "string"
  }
}
```

### POST /tasks/{id}/complete

checklist未完了アイテム（is_done=false かつ extracted_task_id=null）が残っている場合は400を返す。

**Request**

```json
{ "note": "string, optional" }
```

**Response** `201 Created`

```json
{
  "task_id": "int",
  "completed_at": "datetime",
  "note": "string|null"
}
```

### GET /tasks/{id}/convergence

**Response** `200 OK`

```json
{
  "task_id": "int",
  "exploration_limit": "int|null",
  "exploration_used": "int",
  "exploration_remaining": "int|null",
  "reversible": "bool|null",
  "decision_criteria": "string|null",
  "is_convergeable": "bool",
  "convergence_checklist": {
    "options_within_limit": "bool",
    "structure_simplified": "bool",
    "reversible_confirmed": "bool"
  }
}
```

### GET /tasks/stale

**Response** `200 OK`

```json
[
  {
    "...TaskResponse",
    "stale_days": "int",
    "threshold_days": "int"
  }
]
```

### POST /tasks/{id}/carryover

**Request**

```json
{ "action": "CarryoverAction" }
```

actionごとの処理：

```
today          → due_date=今日, status=todo
plus_2d        → due_date+=2,   status=todo
plus_7d        → due_date+=7,   status=todo
needs_redefine → status=needs_redefine
```

### POST /tasks/{id}/checklist/{item_id}/extract

切り出し時の内部処理：
1. parent_id={id}で新タスクを生成
2. checklist_item.extracted_task_id = 新タスクのid
3. checklist_item.is_done = true（切り出し済み＝完了扱い）
4. task.origin_checklist_item_id = item_id（逆参照）

**Request**

```json
{
  "title": "string, optional（省略時はchecklistのtextを使用）",
  "task_type": "TaskType, optional, default=execution",
  "priority": "Priority, optional, default=親と同じ",
  "due_date": "date, optional",
  "done_criteria": "string, optional（省略時はtitleを使用）"
}
```

**Response** `201 Created`

```json
{
  "extracted_task": "...TaskResponse",
  "checklist_item": "...ChecklistItemResponse"
}
```

---

## 5. ディレクトリ構成

```
backend/
├── main.py
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
│         └── 001_create_initial_tables.py
├── app/
│   ├── api/
│   │     ├── tasks.py
│   │     ├── checklist.py
│   │     ├── captures.py
│   │     └── carryover.py
│   ├── models/
│   │     ├── task.py
│   │     ├── checklist_item.py
│   │     ├── completion_log.py
│   │     └── capture_item.py
│   ├── schemas/
│   │     ├── task.py
│   │     ├── checklist_item.py
│   │     ├── completion_log.py
│   │     └── capture_item.py
│   ├── services/
│   │     ├── task_service.py
│   │     ├── carryover_service.py
│   │     └── capture_service.py
│   ├── db/
│   │     ├── base.py
│   │     └── session.py
│   └── core/
│         └── config.py          # DATABASE_URL / CORS_ORIGINS / LOG_LEVEL / WORKERS
└── tests/
      ├── test_tasks.py
      ├── test_carryover.py
      └── test_checklist.py
```

### 4層分離の設計意図

```
api（ルーター）
  └── schemas（入出力の型チェック）
  └── services（ビジネスロジック）
        └── models（DBアクセス）
```

---

## 6. マイグレーション設計

スキーマ変更はAlembicで管理する。v0.2では新規テーブル・カラムの追加はなし（ソートはクエリレベルの変更のみ）。

---

## 7. OpenAPI定義（v0.2更新箇所のみ抜粋）

```yaml
openapi: 3.0.3
info:
  title: タスク管理システム API
  version: 0.2.0

components:
  schemas:
    # v0.2追加
    SortBy:
      type: string
      enum: [due_date, created_at, priority, title]
      default: due_date

    SortOrder:
      type: string
      enum: [asc, desc]
      default: asc

paths:
  /tasks:
    get:
      tags: [tasks]
      summary: タスク一覧取得
      parameters:
        - in: query
          name: status
          schema:
            $ref: '#/components/schemas/TaskStatus'
        - in: query
          name: task_type
          schema:
            $ref: '#/components/schemas/TaskType'
        - in: query
          name: priority
          schema:
            $ref: '#/components/schemas/Priority'
        - in: query
          name: parent_id
          schema:
            type: integer
            nullable: true
          description: |
            指定なし → 親子両方返す
            null相当（0） → parent_id=nullのみ（親タスクのみ）
            整数値 → 指定親の子タスクのみ
        # ── v0.2 追加 ──
        - in: query
          name: sort_by
          schema:
            $ref: '#/components/schemas/SortBy'
          description: ソートキー（デフォルト: due_date）
        - in: query
          name: order
          schema:
            $ref: '#/components/schemas/SortOrder'
          description: ソート順（デフォルト: asc）。due_dateソート時はNULLs LAST
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/TaskResponse'
```

---

## 8. 今後の課題

| 項目 | 優先度 | 内容 |
|------|-------|------|
| ソートのテスト追加 | 高 | `GET /tasks` のソートパラメータに対するテストケース追加 |
| 複数statusフィルタ対応 | 中 | フロントから `status=todo&status=doing` のように複数値を渡せるようにする |
| PostgreSQL移行 | 低 | NULLs LAST の挙動はDBによって差異があるため移行時に要確認 |
| 認証 | 低 | JWT Bearer Token（v0.3以降） |