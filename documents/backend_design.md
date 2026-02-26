# タスク管理システム バックエンド設計書

**バージョン:** v0.1  
**対象:** バックエンド（FastAPI）  
**作成日:** 2026-02-25

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
    ├─── 繰り越し確定操作                   │  タスク管理システム   │──▶ タスク一覧・詳細
    └─── 放置検知確認                       │                     │──▶ 放置アラート
                                            │                     │──▶ 繰り越し候補一覧
                                            └─────────────────────┘
                                                      │
                                                  [SQLite DB]
```

外部エンティティはユーザーのみ。チーム・通知・外部連携はv0.1スコープ外。

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
| GET | `/tasks` | 一覧取得（status/typeフィルタ対応） |
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
| PATCH | `/tasks/{id}/checklist/{item_id}` | チェックリストアイテム更新 |
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

X→Y（バッチ方式）への移行は局所的な実装変更のみで対応可能。APIインターフェースは変更不要。

### PATCH経由でのdone指定禁止

`PATCH /tasks/{id}`でのstatus=done指定はバリデーションエラー（400）とする。完了はかならず`POST /tasks/{id}/complete`を経由させ、completion_logの生成漏れを防ぐ。

---

## 4. APIスキーマ詳細

### 共通型定義

```
TaskType   : research | decision | execution
TaskStatus : todo | doing | done | carryover_candidate | needs_redefine | snoozed
Priority   : must | should
CarryoverAction : today | plus_2d | plus_7d | needs_redefine
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

**Response** `201 Created`
```json
{
  "id": "int",
  "title": "string",
  "task_type": "TaskType",
  "category": "string|null",
  "priority": "Priority",
  "status": "todo",
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
```

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

checklist未完了アイテム（is_done=false かつ extracted_task_id=null）が残っている場合は400 Bad Requestを返す。

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
├── main.py                         # FastAPIアプリ起動点
├── alembic.ini                     # Alembic設定
├── alembic/
│   ├── env.py                      # マイグレーション実行環境
│   └── versions/                   # マイグレーションファイル置き場
│         └── 001_create_initial_tables.py
├── app/
│   ├── api/                        # ルーター（エンドポイント定義）
│   │     ├── tasks.py              # /tasks/**
│   │     ├── checklist.py          # /tasks/{id}/checklist/**
│   │     ├── captures.py           # /captures/**
│   │     └── carryover.py          # /tasks/{id}/carryover（独立ルーター）
│   ├── models/                     # SQLAlchemyモデル定義
│   │     ├── task.py
│   │     ├── checklist_item.py
│   │     ├── completion_log.py
│   │     └── capture_item.py
│   ├── schemas/                    # Pydanticスキーマ
│   │     ├── task.py
│   │     ├── checklist_item.py
│   │     ├── completion_log.py
│   │     └── capture_item.py
│   ├── services/                   # ビジネスロジック
│   │     ├── task_service.py       # 状態遷移・放置検知・収束判定
│   │     ├── carryover_service.py  # 繰り越し動的判定
│   │     └── capture_service.py
│   ├── db/
│   │     ├── base.py               # SQLAlchemyベース定義
│   │     └── session.py            # DBセッション管理
│   └── core/
│         └── config.py             # 環境変数・設定値
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

task_service.pyが担うロジック：
- 放置検知（last_updated_atの閾値計算）
- 探索収束判定（is_convergeable）
- complete時のchecklist未完了バリデーション
- extract時の双方向参照書き込み
- carryover_candidateの動的判定

carryover.pyを独立ルーターにする理由：「繰り越し管理は通常のCRUDと文脈が異なる」という設計意図をディレクトリ構造として明示するため。

---

## 6. マイグレーション設計

### 設定

**`app/core/config.py`**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./tasks.db"

settings = Settings()
```

**`alembic/env.py`（抜粋）**
```python
from app.core.config import settings
from app.db.base import Base

config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata

context.configure(
    connection=connection,
    target_metadata=target_metadata,
    render_as_batch=True  # SQLite対応（カラム削除・変更を可能にする）
)
```

### SQLAlchemyモデル定義

**`app/models/task.py`**
```python
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    task_type = Column(String, nullable=False)
    category = Column(String, nullable=True)
    priority = Column(String, nullable=False)
    status = Column(String, nullable=False, default="todo")
    due_date = Column(Date, nullable=True)
    parent_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    done_criteria = Column(String, nullable=False)
    decision_criteria = Column(String, nullable=True)
    reversible = Column(Boolean, nullable=True)
    exploration_limit = Column(Integer, nullable=True)
    origin_checklist_item_id = Column(Integer, ForeignKey("task_checklist_items.id"), nullable=True)
    last_updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())
```

**`app/models/checklist_item.py`**
```python
class TaskChecklistItem(Base):
    __tablename__ = "task_checklist_items"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    text = Column(String, nullable=False)
    is_done = Column(Boolean, default=False)
    order_no = Column(Integer, nullable=False)
    extracted_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
```

### マイグレーションファイル構成

循環参照（tasks ↔ task_checklist_items）の解決のため、外部キー制約をテーブル作成後に後付けする。

```python
# 001_create_initial_tables.py

def upgrade():
    # 1. tasks作成（origin_checklist_item_idの外部キーなし）
    op.create_table("tasks", ...)

    # 2. task_checklist_items作成（tasks参照あり）
    op.create_table("task_checklist_items", ...)

    # 3. origin_checklist_item_idの外部キーを後付け
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.create_foreign_key(
            "fk_tasks_origin_checklist_item_id",
            "task_checklist_items",
            ["origin_checklist_item_id"],
            ["id"],
            ondelete="SET NULL"
        )

    # 4. インデックス作成
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_last_updated_at", "tasks", ["last_updated_at"])
    op.create_index("ix_tasks_due_date", "tasks", ["due_date"])
    op.create_index("ix_tasks_parent_id", "tasks", ["parent_id"])

    # 5. completion_logs, capture_items作成
    op.create_table("completion_logs", ...)
    op.create_table("capture_items", ...)

def downgrade():
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_constraint("fk_tasks_origin_checklist_item_id")
    op.drop_table("capture_items")
    op.drop_table("completion_logs")
    op.drop_table("task_checklist_items")
    op.drop_table("tasks")
```

### 循環参照の設計メモ

```
tasks.origin_checklist_item_id → task_checklist_items.id
task_checklist_items.task_id   → tasks.id
```

- 外部キー制約を維持（DBレベルで整合性を保証）
- `ondelete="SET NULL"`でchecklist_item削除時に自動NULL化
- 削除処理はtask_service.pyで順序を保証する

### インデックス設計

| インデックス | 用途 |
|---|---|
| ix_tasks_status | GET /tasks フィルタ |
| ix_tasks_last_updated_at | /tasks/stale 放置検知 |
| ix_tasks_due_date | /tasks/carryover-candidates 期限超過判定 |
| ix_tasks_parent_id | /tasks/{id}/children 子タスク取得 |

### SQLite制約と対処方針

| 操作 | SQLite | 対処方針 |
|---|---|---|
| カラム追加 | ◎ 可能 | 通常通りAlembicで対応 |
| カラム削除 | ✕ 不可 | batch_alter_tableで対応 |
| カラム型変更 | ✕ 不可 | batch_alter_tableで対応 |
| 外部キー変更 | ✕ 不可 | batch_alter_tableで対応 |

`render_as_batch=True`を初期設定済みのため、追加設定なしで対応可能。

---

## 7. OpenAPI定義

```yaml
openapi: 3.0.3
info:
  title: タスク管理システム API
  version: 0.1.0

tags:
  - name: tasks
  - name: checklist
  - name: captures
  - name: carryover

components:
  schemas:
    TaskType:
      type: string
      enum: [research, decision, execution]

    TaskStatus:
      type: string
      enum: [todo, doing, done, carryover_candidate, needs_redefine, snoozed]

    Priority:
      type: string
      enum: [must, should]

    CarryoverAction:
      type: string
      enum: [today, plus_2d, plus_7d, needs_redefine]

    TaskResponse:
      type: object
      properties:
        id:
          type: integer
        title:
          type: string
        task_type:
          $ref: '#/components/schemas/TaskType'
        category:
          type: string
          nullable: true
        priority:
          $ref: '#/components/schemas/Priority'
        status:
          $ref: '#/components/schemas/TaskStatus'
        due_date:
          type: string
          format: date
          nullable: true
        parent_id:
          type: integer
          nullable: true
        done_criteria:
          type: string
        decision_criteria:
          type: string
          nullable: true
        reversible:
          type: boolean
          nullable: true
        exploration_limit:
          type: integer
          nullable: true
        origin_checklist_item_id:
          type: integer
          nullable: true
        last_updated_at:
          type: string
          format: date-time
        created_at:
          type: string
          format: date-time

    TaskDetailResponse:
      allOf:
        - $ref: '#/components/schemas/TaskResponse'
        - type: object
          properties:
            children:
              type: array
              items:
                $ref: '#/components/schemas/TaskResponse'
            checklist:
              type: array
              items:
                $ref: '#/components/schemas/ChecklistItemResponse'
            origin:
              nullable: true
              type: object
              properties:
                parent_task_id:
                  type: integer
                parent_task_title:
                  type: string
                checklist_item_text:
                  type: string

    TaskCreateRequest:
      type: object
      required: [title, task_type, priority, done_criteria]
      properties:
        title:
          type: string
        task_type:
          $ref: '#/components/schemas/TaskType'
        category:
          type: string
          nullable: true
        priority:
          $ref: '#/components/schemas/Priority'
        due_date:
          type: string
          format: date
          nullable: true
        parent_id:
          type: integer
          nullable: true
        done_criteria:
          type: string
        decision_criteria:
          type: string
          nullable: true
        reversible:
          type: boolean
          nullable: true
        exploration_limit:
          type: integer
          nullable: true

    TaskUpdateRequest:
      type: object
      properties:
        title:
          type: string
        task_type:
          $ref: '#/components/schemas/TaskType'
        category:
          type: string
        priority:
          $ref: '#/components/schemas/Priority'
        status:
          $ref: '#/components/schemas/TaskStatus'
        due_date:
          type: string
          format: date
          nullable: true
        done_criteria:
          type: string
        decision_criteria:
          type: string
          nullable: true
        reversible:
          type: boolean
          nullable: true
        exploration_limit:
          type: integer
          nullable: true

    ChecklistItemResponse:
      type: object
      properties:
        id:
          type: integer
        text:
          type: string
        is_done:
          type: boolean
        order_no:
          type: integer
        extracted_task_id:
          type: integer
          nullable: true

    ChecklistItemUpdateRequest:
      type: object
      properties:
        is_done:
          type: boolean
        text:
          type: string

    CompletionLogResponse:
      type: object
      properties:
        id:
          type: integer
        task_id:
          type: integer
        completed_at:
          type: string
          format: date-time
        note:
          type: string
          nullable: true

    ConvergenceResponse:
      type: object
      properties:
        task_id:
          type: integer
        exploration_limit:
          type: integer
          nullable: true
        exploration_used:
          type: integer
        exploration_remaining:
          type: integer
          nullable: true
        reversible:
          type: boolean
          nullable: true
        decision_criteria:
          type: string
          nullable: true
        is_convergeable:
          type: boolean
        convergence_checklist:
          type: object
          properties:
            options_within_limit:
              type: boolean
            structure_simplified:
              type: boolean
            reversible_confirmed:
              type: boolean

    StaleTaskResponse:
      allOf:
        - $ref: '#/components/schemas/TaskResponse'
        - type: object
          properties:
            stale_days:
              type: integer
            threshold_days:
              type: integer

    CarryoverCandidateResponse:
      allOf:
        - $ref: '#/components/schemas/TaskResponse'
        - type: object
          properties:
            overdue_days:
              type: integer

    CarryoverRequest:
      type: object
      required: [action]
      properties:
        action:
          $ref: '#/components/schemas/CarryoverAction'

    CaptureItemResponse:
      type: object
      properties:
        id:
          type: integer
        text:
          type: string
        related_task_id:
          type: integer
          nullable: true
        created_at:
          type: string
          format: date-time
        is_resolved:
          type: boolean

    CaptureCreateRequest:
      type: object
      required: [text]
      properties:
        text:
          type: string
        related_task_id:
          type: integer
          nullable: true

    CaptureUpdateRequest:
      type: object
      properties:
        text:
          type: string
        is_resolved:
          type: boolean
        related_task_id:
          type: integer
          nullable: true

    ExtractRequest:
      type: object
      properties:
        title:
          type: string
          nullable: true
        task_type:
          $ref: '#/components/schemas/TaskType'
        priority:
          $ref: '#/components/schemas/Priority'
        due_date:
          type: string
          format: date
          nullable: true
        done_criteria:
          type: string
          nullable: true

    ExtractResponse:
      type: object
      properties:
        extracted_task:
          $ref: '#/components/schemas/TaskResponse'
        checklist_item:
          $ref: '#/components/schemas/ChecklistItemResponse'

  responses:
    NotFound:
      description: リソースが見つかりません
      content:
        application/json:
          schema:
            type: object
            properties:
              detail:
                type: string
    BadRequest:
      description: バリデーションエラー
      content:
        application/json:
          schema:
            type: object
            properties:
              detail:
                type: string

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
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/TaskResponse'
    post:
      tags: [tasks]
      summary: タスク登録
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TaskCreateRequest'
      responses:
        '201':
          description: 作成成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskResponse'
        '400':
          $ref: '#/components/responses/BadRequest'

  /tasks/stale:
    get:
      tags: [tasks]
      summary: 放置タスク一覧
      parameters:
        - in: query
          name: priority
          schema:
            $ref: '#/components/schemas/Priority'
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/StaleTaskResponse'

  /tasks/carryover-candidates:
    get:
      tags: [carryover]
      summary: 繰り越し候補一覧
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/CarryoverCandidateResponse'

  /tasks/{id}:
    get:
      tags: [tasks]
      summary: タスク詳細取得
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskDetailResponse'
        '404':
          $ref: '#/components/responses/NotFound'
    patch:
      tags: [tasks]
      summary: タスク部分更新
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TaskUpdateRequest'
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '404':
          $ref: '#/components/responses/NotFound'
    delete:
      tags: [tasks]
      summary: タスク削除
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: integer
      responses:
        '204':
          description: 削除成功
        '400':
          $ref: '#/components/responses/BadRequest'
        '404':
          $ref: '#/components/responses/NotFound'

  /tasks/{id}/children:
    get:
      tags: [tasks]
      summary: 子タスク一覧
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/TaskResponse'
    post:
      tags: [tasks]
      summary: 子タスク登録
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TaskCreateRequest'
      responses:
        '201':
          description: 作成成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskResponse'

  /tasks/{id}/convergence:
    get:
      tags: [tasks]
      summary: 探索収束状態確認
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ConvergenceResponse'

  /tasks/{id}/complete:
    post:
      tags: [tasks]
      summary: タスク完了
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: integer
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                note:
                  type: string
                  nullable: true
      responses:
        '201':
          description: 完了成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CompletionLogResponse'
        '400':
          $ref: '#/components/responses/BadRequest'

  /tasks/{id}/completion-log:
    get:
      tags: [tasks]
      summary: 完了ログ取得
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/CompletionLogResponse'

  /tasks/{id}/checklist:
    get:
      tags: [checklist]
      summary: チェックリスト取得
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/ChecklistItemResponse'

  /tasks/{id}/checklist/{item_id}:
    patch:
      tags: [checklist]
      summary: チェックリストアイテム更新
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: integer
        - in: path
          name: item_id
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ChecklistItemUpdateRequest'
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ChecklistItemResponse'

  /tasks/{id}/checklist/{item_id}/extract:
    post:
      tags: [checklist]
      summary: チェックリストアイテムをタスクとして切り出す
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: integer
        - in: path
          name: item_id
          required: true
          schema:
            type: integer
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ExtractRequest'
      responses:
        '201':
          description: 切り出し成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ExtractResponse'
        '400':
          $ref: '#/components/responses/BadRequest'

  /tasks/{id}/carryover:
    post:
      tags: [carryover]
      summary: 繰り越し確定
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CarryoverRequest'
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskResponse'
        '400':
          $ref: '#/components/responses/BadRequest'

  /captures:
    get:
      tags: [captures]
      summary: キャプチャ一覧
      parameters:
        - in: query
          name: is_resolved
          schema:
            type: boolean
            default: false
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/CaptureItemResponse'
    post:
      tags: [captures]
      summary: キャプチャ登録
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CaptureCreateRequest'
      responses:
        '201':
          description: 作成成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CaptureItemResponse'

  /captures/{id}:
    patch:
      tags: [captures]
      summary: キャプチャ更新
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CaptureUpdateRequest'
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CaptureItemResponse'
    delete:
      tags: [captures]
      summary: キャプチャ削除
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: integer
      responses:
        '204':
          description: 削除成功
```

---

## 8. 今後の課題

### フロントエンド設計（未着手）
- Nuxt3ディレクトリ構成
- 画面設計

### テスト設計（未着手）
- APIテスト設計
- サービス層ユニットテスト設計
