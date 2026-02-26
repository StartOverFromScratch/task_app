# タスク管理システム フロントエンド設計書

作成日: 2026-02-26 | バージョン: 1.0

---

## 0. 構成概要

| 項目 | 内容 |
|------|------|
| フレームワーク | Nuxt 3 |
| UIライブラリ | Nuxt UI（Tailwindベース） |
| 状態管理 | Pinia |
| API通信 | Repositoryパターン（$fetch） |
| 言語 | TypeScript |

---

## 1. ディレクトリ構成

Nuxt 3の規約に従いつつ、API通信層（repositories）とビジネスロジック層（composables）を明確に分離する。

```
frontend/
├── app.vue
├── nuxt.config.ts
├── .env
│
├── pages/                        # ルーティング
│   ├── index.vue                 # タスク一覧（メイン画面）
│   ├── tasks/
│   │   ├── new.vue               # タスク新規作成
│   │   └── [id]/
│   │       ├── index.vue         # タスク詳細
│   │       └── edit.vue          # タスク編集
│   ├── carryover.vue             # 繰り越し候補一覧
│   ├── stale.vue                 # 放置タスク一覧
│   └── capture.vue               # CaptureBox
│
├── components/
│   ├── task/
│   │   ├── TaskCard.vue          # タスクカード（一覧用）
│   │   ├── TaskForm.vue          # 作成・編集フォーム
│   │   ├── TaskStatusBadge.vue   # ステータスバッジ
│   │   ├── TaskTypeBadge.vue     # タスクタイプバッジ
│   │   └── TaskChildList.vue     # 子タスク一覧
│   ├── checklist/
│   │   ├── ChecklistPanel.vue    # チェックリスト全体
│   │   └── ChecklistItem.vue     # 1アイテム（extract操作含む）
│   ├── carryover/
│   │   └── CarryoverActionBar.vue # 今日やる・+2日・+7日・要再定義
│   ├── capture/
│   │   └── CaptureInput.vue      # 分岐論点の投入UI
│   └── common/
│       ├── PageHeader.vue
│       └── ConfirmDialog.vue
│
├── composables/                  # ビジネスロジック・ストア更新
│   ├── useTask.ts
│   ├── useChecklist.ts
│   ├── useCarryover.ts
│   ├── useStale.ts
│   └── useCapture.ts
│
├── stores/                       # Pinia ストア
│   ├── taskStore.ts
│   ├── carryoverStore.ts
│   └── captureStore.ts
│
├── repositories/                 # API通信層
│   ├── taskRepository.ts
│   ├── checklistRepository.ts
│   ├── carryoverRepository.ts
│   ├── captureRepository.ts
│   └── index.ts                  # まとめてexport
│
├── types/
│   ├── task.ts
│   ├── checklist.ts
│   ├── carryover.ts
│   └── capture.ts
│
└── utils/
    ├── staleThreshold.ts         # 放置判定ロジック（must:7日 / should:21日）
    └── dateFormat.ts             # 日付フォーマット共通処理
```

---

## 2. API通信層の設計

### 2.1 アーキテクチャ

Repositoryパターンを採用する。各層の責務を以下のように分離する。

| 層 | 責務 |
|----|------|
| pages / components | 表示・ユーザー操作のみ。composablesを呼ぶ |
| composables | ビジネスロジック・ストア更新・エラーハンドリング |
| repositories | API通信のみ（fetch・エラー投げ上げ） |
| FastAPI backend | データ処理・DB操作 |

呼び出しフロー：

```
pages/components → composables → repositories → FastAPI
```

### 2.2 Repositoryの基本形

baseURLは`.env`の`NUXT_PUBLIC_API_BASE`から取得する。

```typescript
// repositories/taskRepository.ts
export const taskRepository = {
  async fetchAll(params?: TaskQueryParams): Promise<Task[]> {
    return await $fetch('/tasks', { baseURL: useRuntimeConfig().public.apiBase, params })
  },
  async fetchById(id: number): Promise<Task> {
    return await $fetch(`/tasks/${id}`, { baseURL: useRuntimeConfig().public.apiBase })
  },
  async create(body: TaskCreateRequest): Promise<Task> {
    return await $fetch('/tasks', { method: 'POST', baseURL: useRuntimeConfig().public.apiBase, body })
  },
  async update(id: number, body: TaskUpdateRequest): Promise<Task> {
    return await $fetch(`/tasks/${id}`, { method: 'PATCH', baseURL: useRuntimeConfig().public.apiBase, body })
  },
  async remove(id: number): Promise<void> {
    return await $fetch(`/tasks/${id}`, { method: 'DELETE', baseURL: useRuntimeConfig().public.apiBase })
  },
  async complete(id: number): Promise<Task> {
    return await $fetch(`/tasks/${id}/complete`, { method: 'POST', baseURL: useRuntimeConfig().public.apiBase })
  },
}
```

### 2.3 エラーハンドリング方針

repositories層はエラーをそのまま投げ上げる。composables層でcatchし、Nuxt UIの`useToast`で通知する。

| ステータスコード | ケース | トースト表示 |
|----------------|--------|------------|
| 400 | チェックリスト未完了で完了操作 | 未対応のチェックリストが残っています |
| 404 | 存在しないリソース | 対象が見つかりませんでした |
| 422 | バリデーションエラー | 入力内容を確認してください |
| 500 | サーバーエラー | エラーが発生しました。しばらく後に再試行してください |

```typescript
// composables/useTask.ts（エラーハンドリング例）
async function completeTask(id: number) {
  try {
    const updated = await taskRepository.complete(id)
    taskStore.upsert(updated)
  } catch (e: any) {
    if (e.statusCode === 400) {
      toast.add({
        title: '完了できません',
        description: 'チェックリストに未対応のアイテムが残っています',
        color: 'red'
      })
    } else {
      toast.add({ title: 'エラーが発生しました', color: 'red' })
    }
  }
}
```

---

## 3. Piniaストア分割方針

### 3.1 ストア一覧

| ストア名 | ファイル | 責務 |
|---------|---------|------|
| taskStore | stores/taskStore.ts | タスク一覧・詳細の状態管理 |
| carryoverStore | stores/carryoverStore.ts | 繰り越し候補の状態管理・操作 |
| captureStore | stores/captureStore.ts | CaptureBoxアイテムの状態管理 |

### 3.2 taskStore

タスクCRUD・詳細表示の中心ストア。一覧と現在表示中のタスクを管理する。

```typescript
export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Task[]>([])
  const currentTask = ref<Task | null>(null)

  function upsert(task: Task) {
    const idx = tasks.value.findIndex(t => t.id === task.id)
    if (idx >= 0) tasks.value[idx] = task
    else tasks.value.unshift(task)
  }

  function remove(id: number) {
    tasks.value = tasks.value.filter(t => t.id !== id)
  }

  return { tasks, currentTask, upsert, remove }
})
```

### 3.3 carryoverStore

繰り越し候補はtaskStoreと文脈が異なるため分離する。各操作（今日やる・+2日・+7日・要再定義）の実行後はcandidatesから除去し、taskStoreにも反映する。

```typescript
export const useCarryoverStore = defineStore('carryover', () => {
  const candidates = ref<Task[]>([])

  function removeCandidate(id: number) {
    candidates.value = candidates.value.filter(t => t.id !== id)
  }

  return { candidates, removeCandidate }
})
```

### 3.4 captureStore

CaptureBoxはタスクとは独立した概念のため完全分離する。`is_resolved`フラグで未解決・解決済みをフィルタリングする。

```typescript
export const useCaptureStore = defineStore('capture', () => {
  const items = ref<CaptureItem[]>([])
  const unresolved = computed(() => items.value.filter(i => !i.is_resolved))
  const resolved = computed(() => items.value.filter(i => i.is_resolved))

  return { items, unresolved, resolved }
})
```

---

## 4. 画面設計（ワイヤーレベル）

### 4.1 画面一覧

| 画面名 | パス | 主な役割 |
|-------|------|---------|
| タスク一覧 | `/` | 全タスク表示・フィルタ・ステータス変更 |
| タスク詳細 | `/tasks/[id]` | 詳細確認・チェックリスト・子タスク・CaptureBox |
| タスク作成 | `/tasks/new` | 新規登録フォーム |
| タスク編集 | `/tasks/[id]/edit` | 編集フォーム |
| 繰り越し候補 | `/carryover` | 期限超過タスクの処理 |
| 放置タスク | `/stale` | 放置タスクへの対応 |
| CaptureBox | `/capture` | 分岐論点一覧・解決済み管理 |

### 4.2 タスク一覧画面 `/`

メイン画面。放置タスク・繰り越し候補のバナー通知を表示し、各ページへ誘導する。

```
┌─────────────────────────────────────────┐
│  タスク一覧          [+ 新規作成]        │
│  ─────────────────────────────────────  │
│  [全て] [todo] [doing] [done]           │
│  タイプ▼  優先度▼  カテゴリ▼            │
│  ─────────────────────────────────────  │
│  ⚠ 放置タスク 3件  ⚠ 繰り越し候補 2件  │
│  ─────────────────────────────────────  │
│  ┌─────────────────────────────────┐   │
│  │ [research] タスクタイトル        │   │
│  │ 完了条件: ○○になったら完了       │   │
│  │ 期限: 2026-02-28  優先: must     │   │
│  │ ステータス: [doing ▼]            │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

主要コンポーネント：`TaskCard.vue`、`TaskStatusBadge.vue`、`TaskTypeBadge.vue`

### 4.3 タスク詳細画面 `/tasks/[id]`

タスクの全情報を表示する。チェックリスト・子タスク・CaptureBoxをパネルとして配置する。

```
┌─────────────────────────────────────────┐
│  ← 戻る  タスクタイトル   [編集] [削除] │
│  ─────────────────────────────────────  │
│  [research]  doing  must               │
│  期限: 2026-02-28                       │
│                                         │
│  完了条件                               │
│  ○○になったら完了                       │
│                                         │
│  決定基準（decision_criteriaがある場合） │
│  ○○であれば採用                         │
│                                         │
│  可逆: はい  探索上限: 3件              │
│  ─────────────────────────────────────  │
│  チェックリスト                [+ 追加] │
│  ☑ 項目A                               │
│  ☐ 項目B          [タスクとして切り出し] │
│  ─────────────────────────────────────  │
│  子タスク                    [+ 追加]   │
│  └ 子タスクタイトル  [doing]            │
│  ─────────────────────────────────────  │
│  CaptureBox（分岐論点）        [+ 追加] │
│  • 論点メモ                             │
│  ─────────────────────────────────────  │
│           [完了にする]                  │
└─────────────────────────────────────────┘
```

主要コンポーネント：`ChecklistPanel.vue`、`ChecklistItem.vue`（extract操作含む）、`TaskChildList.vue`、`CaptureInput.vue`

### 4.4 タスク作成・編集フォーム `/tasks/new`, `/tasks/[id]/edit`

researchタイプを選択した場合のみ、探索上限・決定基準フィールドを動的に表示する。

```
┌─────────────────────────────────────────┐
│  タスクを作成                            │
│  ─────────────────────────────────────  │
│  タイトル *         [                 ] │
│  タイプ *           [research       ▼] │
│  完了条件 *         [                 ] │
│  優先度             [must           ▼] │
│  カテゴリ           [                 ] │
│  期限               [  yyyy-mm-dd    ] │
│  親タスク           [（任意）         ] │
│  可逆               [ ○ はい  ○ いいえ] │
│                                         │
│  ── researchタイプの場合のみ表示 ──     │
│  探索上限           [   3           ] 件│
│  決定基準           [                 ] │
│                                         │
│  [キャンセル]              [作成する]   │
└─────────────────────────────────────────┘
```

主要コンポーネント：`TaskForm.vue`（作成・編集を共通化）

### 4.5 繰り越し候補画面 `/carryover`

期限超過タスクを一覧表示し、4つのアクションボタンで処理する。操作後はカードが消える。

```
┌─────────────────────────────────────────┐
│  繰り越し候補                            │
│  ─────────────────────────────────────  │
│  ┌─────────────────────────────────┐   │
│  │ タスクタイトル                   │   │
│  │ 元の期限: 2026-02-20             │   │
│  │ 完了条件: ○○                    │   │
│  │                                  │   │
│  │ [今日やる][+2日][+7日][要再定義] │   │
│  └─────────────────────────────────┘   │
│  （カード繰り返し）                      │
└─────────────────────────────────────────┘
```

主要コンポーネント：`CarryoverActionBar.vue`

### 4.6 放置タスク画面 `/stale`

must（7日）・should（21日）の閾値で2セクションに分けて表示する。「向き合う」ボタンでタスク詳細へ遷移する。

```
┌─────────────────────────────────────────┐
│  放置タスク                              │
│  ─────────────────────────────────────  │
│  must（7日以上更新なし）                 │
│  ┌─────────────────────────────────┐   │
│  │ タスクタイトル  最終更新: 14日前  │   │
│  │ [向き合う → 詳細へ]              │   │
│  └─────────────────────────────────┘   │
│                                         │
│  should（21日以上更新なし）              │
│  ┌─────────────────────────────────┐   │
│  │ タスクタイトル  最終更新: 25日前  │   │
│  │ [向き合う → 詳細へ]              │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

放置判定ロジックは`utils/staleThreshold.ts`に集約する（must: 7日、should: 21日）。

### 4.7 CaptureBox画面 `/capture`

実行中に湧いた分岐論点を素早く記録する画面。未解決・解決済みのタブ切り替えで管理する。

```
┌─────────────────────────────────────────┐
│  CaptureBox                             │
│  ─────────────────────────────────────  │
│  [ 論点・メモを入力...       ] [追加]   │
│  ─────────────────────────────────────  │
│  [未解決] [解決済み]                    │
│  ─────────────────────────────────────  │
│  ┌─────────────────────────────────┐   │
│  │ 論点メモの内容                   │   │
│  │ 関連: タスクタイトル             │   │
│  │ 2026-02-25          [解決済みに] │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

主要コンポーネント：`CaptureInput.vue`

---

## 5. 次回スコープ

| 項目 | 優先度 | 内容 |
|------|-------|------|
| APIテスト | 中 | エンドポイント単位のテスト設計 |
| サービス層ユニットテスト | 中 | FastAPIサービス層のロジックテスト |
