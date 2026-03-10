# タスク管理システム フロントエンド設計書

作成日: 2026-02-26 | バージョン: 1.5 | 最終更新: 2026-03-10

> v1.4 → v1.5 変更点：
> - プッシュ通知機能追加（`usePushNotification.ts`、`/public/sw.js`）
> - タスク一覧：ベルアイコンで通知ON/OFF切り替え・紙飛行機アイコンで手動送信
> - 通知設定画面 `/settings` 追加（定時通知有効/無効・通知時刻×2）
> - `app.vue`：ナビゲーションにギアアイコン（設定リンク）追加

> v1.3 → v1.4 変更点：
> - タスク一覧：スリープ防止トグルボタン追加（Screen Wake Lock API）
> - `useWakeLock.ts` composable 追加

> v1.2 → v1.3 変更点：
> - TaskCard.vue：タスク名フォントサイズを `text-2xl` に拡大
> - TaskCard.vue：完了条件と期限を同一行に横並び表示（期限を右端に配置）
> - TaskCard.vue：期限の日付フォーマットを `MM/dd` に短縮
> - タスク一覧：期限フィルタ追加（今日・明日 / 全て）。デフォルトは「今日・明日」
> - タスク一覧：今日・明日のタスクが3件以下の場合、次に予定がある日まで自動拡張

> v1.1 → v1.2 変更点：
> - タスク一覧：デフォルトフィルタ（todo/doing）・デフォルトソート（due_date昇順）を明記
> - タスク一覧：子タスクをデフォルト表示・バッジで識別
> - タスク一覧：PCでの2カラムレイアウト追加
> - タスク詳細：タスク名称の表示を明記（設計漏れ補完）
> - TaskCard.vue：子タスクバッジ表示仕様追加
> - taskStore.ts：selectedTaskId の状態管理仕様追加

---

## 0. 構成概要

| 項目 | 内容 |
|------|------|
| フレームワーク | Nuxt 4 |
| UIライブラリ | Nuxt UI（Tailwindベース） |
| 状態管理 | Pinia |
| API通信 | Repositoryパターン（$fetch） |
| 言語 | TypeScript |

---

## 1. ディレクトリ構成

```
frontend/
├── app.vue
├── nuxt.config.ts
├── .env
│
├── pages/
│   ├── index.vue                 # タスク一覧（メイン画面）
│   ├── tasks/
│   │   ├── new.vue               # タスク新規作成
│   │   └── [id]/
│   │       ├── index.vue         # タスク詳細
│   │       └── edit.vue          # タスク編集
│   ├── carryover.vue             # 繰り越し候補一覧
│   ├── stale.vue                 # 放置タスク一覧
│   ├── capture.vue               # CaptureBox
│   └── settings.vue              # 通知設定（定時プッシュ通知）
│
├── components/
│   ├── task/
│   │   ├── TaskCard.vue          # タスクカード（子タスクバッジ表示対応）
│   │   ├── TaskForm.vue          # 作成・編集フォーム
│   │   ├── TaskStatusBadge.vue   # ステータスバッジ
│   │   ├── TaskTypeBadge.vue     # タスクタイプバッジ
│   │   └── TaskChildList.vue     # 子タスク一覧
│   ├── checklist/
│   │   ├── ChecklistPanel.vue    # チェックリスト全体
│   │   └── ChecklistItem.vue     # 1アイテム（extract操作含む）
│   ├── carryover/
│   │   └── CarryoverActionBar.vue
│   ├── capture/
│   │   └── CaptureInput.vue
│   └── common/
│       ├── PageHeader.vue
│       └── ConfirmDialog.vue
│
├── composables/
│   ├── useTask.ts                # デフォルトフィルタ・ソート仕様あり
│   ├── useChecklist.ts
│   ├── useCarryover.ts
│   ├── useStale.ts
│   ├── useCapture.ts
│   ├── useWakeLock.ts            # Screen Wake Lock API ラッパー
│   └── usePushNotification.ts   # Web Push 通知（購読・解除・手動送信）
│
├── stores/
│   ├── taskStore.ts              # selectedTaskId 追加
│   ├── carryoverStore.ts
│   └── captureStore.ts
│
├── repositories/
│   ├── taskRepository.ts         # sort_by / order パラメータ対応
│   ├── checklistRepository.ts
│   ├── carryoverRepository.ts
│   ├── captureRepository.ts
│   └── index.ts
│
├── types/
│   ├── task.ts
│   ├── checklist.ts
│   ├── carryover.ts
│   └── capture.ts
│
├── utils/
│   ├── staleThreshold.ts
│   ├── dateFormat.ts
│   └── apiBase.ts
│
└── public/
    └── sw.js                     # Service Worker（push イベント処理・通知表示）
```

---

## 2. Repositoryパターン

### 基本方針

- `repositories/` はAPI通信のみを担う（ビジネスロジック禁止）
- エラーはそのまま投げ上げる（catchは `composables/` で行う）
- `runtimeConfig.public.apiBase` でAPIベースURLを管理

### taskRepository.ts（v1.2更新）

```typescript
// GET /tasks に sort_by / order パラメータを追加

export interface TaskListParams {
  status?: TaskStatus | TaskStatus[]  // 複数指定対応（将来）
  task_type?: TaskType
  priority?: Priority
  parent_id?: number | null
  sort_by?: 'due_date' | 'created_at' | 'priority' | 'title'  // v1.2追加
  order?: 'asc' | 'desc'                                        // v1.2追加
}

export const taskRepository = {
  fetchAll: (params: TaskListParams = {}) =>
    $fetch<Task[]>(`${apiBase}/tasks`, { params }),
  // ... 他のメソッドは変更なし
}
```

---

## 3. Piniaストア設計

### taskStore.ts（v1.2更新）

```typescript
// selectedTaskId を追加（2カラムレイアウトの選択状態管理）

interface TaskState {
  tasks: Task[]
  selectedTaskId: number | null  // v1.2追加：2カラム時の選択タスクID
  loading: boolean
  error: string | null
}

// アクション追加
actions: {
  selectTask(id: number | null) {
    this.selectedTaskId = id
  }
}
```

### carryoverStore.ts / captureStore.ts

変更なし。

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
| 通知設定 | `/settings` | プッシュ通知の定時設定（v1.5追加） |

---

### 4.2 タスク一覧画面 `/`（v1.3更新）

#### モバイル（lg未満）

1カラム表示。タスクカードをタップするとタスク詳細ページ（`/tasks/[id]`）に遷移する。

```
┌─────────────────────────────────────────┐
│  タスク一覧   [🌙] [🔔] [✈] [+ 新規]   │  ← スリープ防止/ベル/紙飛行機(購読時のみ)
│  ─────────────────────────────────────  │
│  [未完了/進行中▼] タイプ▼  優先度▼      │  ← デフォルト: todo/doing
│  [今日・明日] [全て]                    │  ← 期限フィルタ（デフォルト: 今日・明日）
│  ─────────────────────────────────────  │
│  ⚠ 放置タスク 3件  ⚠ 繰り越し候補 2件  │
│  ─────────────────────────────────────  │
│  ┌─────────────────────────────────┐   │
│  │ [research] [doing] [must]  >    │   │
│  │ タスクタイトル（text-2xl）        │   │
│  │ 完了条件: ○○       期限: 02/28  │   │  ← 完了条件と期限を同一行・期限はMM/dd
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ [execution] [todo] [子タスク] > │   │
│  │ 子タスクタイトル                  │   │
│  │ 完了条件テキスト      期限: 03/01 │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

#### PC（lg以上）：2カラムレイアウト

左カラムでタスクを選択すると、右カラムに詳細をインライン表示する。

```
┌──────────────────────────────────────────────────────────────────────┐
│  タスク一覧                            [+ 新規作成]                  │
│  ──────────────────────────────────────────────────────────────────  │
│  [未完了/進行中▼] タイプ▼  優先度▼                                   │
│  ──────────────────────────────────────────────────────────────────  │
│  ┌──────────────────────────┐  ┌──────────────────────────────────┐ │
│  │ ⚠ 放置 3  繰り越し 2    │  │  タスクタイトル    [編集] [削除] │ │
│  │ ─────────────────────── │  │  ─────────────────────────────── │ │
│  │ [research] タスクA       │  │  [research]  doing  must         │ │
│  │ 期限: 2026-02-28 must   │  │  期限: 2026-02-28                │ │
│  │ [doing ▼]               │  │                                  │ │
│  │ ─────────────────────── │  │  完了条件                        │ │
│  │ [execution] 子タスクB   │  │  ○○になったら完了                │ │
│  │ [子タスク]              │  │  ─────────────────────────────── │ │
│  │ 期限: 2026-03-01        │  │  チェックリスト           [+追加] │ │
│  │ [todo ▼]                │  │  ☑ 項目A                        │ │
│  │ ─────────────────────── │  │  ☐ 項目B  [✎編集] [タスクとして切り出し] │ │
│  │  ...                    │  │  ─────────────────────────────── │ │
│  │                         │  │  子タスク                 [+追加] │ │
│  │                         │  │  └ 子タスクB  [doing]            │ │
│  │                         │  │  ─────────────────────────────── │ │
│  │                         │  │              [完了にする]         │ │
│  └──────────────────────── ┘  └──────────────────────────────────┘ │
│   ↑ 固定幅 360px                ↑ 残り幅（flex-1）                  │
└──────────────────────────────────────────────────────────────────────┘
```

**未選択時の右カラム（プレースホルダー）**

```
┌──────────────────────────────────┐
│                                  │
│                                  │
│      タスクを選択してください      │
│                                  │
│                                  │
└──────────────────────────────────┘
```

**主要コンポーネント（更新）**

| コンポーネント | 役割 |
|---|---|
| `TaskCard.vue` | タスクカード。子タスクバッジ・チェックリスト切り出しバッジを表示 |
| `TaskStatusBadge.vue` | ステータスバッジ |
| `TaskTypeBadge.vue` | タスクタイプバッジ |

---

### 4.3 タスク詳細画面 `/tasks/[id]`（v1.2更新）

タスク名称（title）をページタイトルに明示する。2カラム時は右カラムのヘッダーとして機能する。

```
┌─────────────────────────────────────────┐
│  ← 戻る                 [編集] [削除]  │
│  ─────────────────────────────────────  │
│  タスクタイトル（title を大きく表示）    │  ← v1.2: title 表示を明記
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
│  ☐ 項目B    [✎編集] [タスクとして切り出し] │
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

主要コンポーネント：`ChecklistPanel.vue`、`ChecklistItem.vue`、`TaskChildList.vue`、`CaptureInput.vue`

---

### 4.4 タスク作成・編集フォーム `/tasks/new`, `/tasks/[id]/edit`

変更なし。

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

---

### 4.5 繰り越し候補画面 `/carryover`

変更なし。

---

### 4.6 放置タスク画面 `/stale`

変更なし。

---

### 4.7 CaptureBox画面 `/capture`

変更なし。

---

### 4.8 通知設定画面 `/settings`（v1.5追加）

```
┌─────────────────────────────────────────┐
│  通知設定                               │
│  ─────────────────────────────────────  │
│  ┌─────────────────────────────────┐   │
│  │  定時通知                        │   │
│  │  毎日指定した時刻に今日期限の    │   │
│  │  タスクをプッシュ通知します      │   │
│  │                                  │   │
│  │  [定時通知を有効にする  ○──]     │   │  ← USwitch
│  │                                  │   │
│  │  通知時刻 1  [09:00]             │   │  ← <input type="time">
│  │  通知時刻 2  [16:00]             │   │  ← <input type="time">
│  │                                  │   │
│  │  [         保存          ]       │   │
│  └─────────────────────────────────┘   │
│  ※ プッシュ通知の受信には通知許可が必要  │
└─────────────────────────────────────────┘
```

- マウント時に `GET /push/notification-setting` で現在の設定を読み込む
- 保存ボタンで `PUT /push/notification-setting` を呼び出す
- 通知時刻は常に表示（enabled の有無に依らない）

---

## 5. composables 仕様

### useTask.ts（v1.2更新）

```typescript
// デフォルトパラメータを明示

const DEFAULT_PARAMS = {
  status: ['todo', 'doing'] as TaskStatus[],  // 未完了・進行中のみ
  sort_by: 'due_date' as const,
  order: 'asc' as const,
}

export function useTask() {
  // 初期ロード時は DEFAULT_PARAMS を使用
  // フィルタUI操作時はパラメータを上書き
}
```

**設計上の注意点**

- `due_date = null` のタスクはバックエンド側でNULLs LASTになるため、フロントは考慮不要
- フィルタ変更時は `taskStore.selectedTaskId` をリセットする（2カラムの選択状態をクリア）

#### 期限フィルタ（v1.3追加）

| 選択値 | 表示対象 |
|--------|---------|
| `today_tomorrow`（デフォルト） | due_date が翌日23:59以前のタスク。3件以下なら次の予定日まで自動拡張 |
| `all` | 期限フィルタなし（全件表示） |

**自動拡張ロジック：**
1. 今日・明日の件数が3件以下の場合、due_date が明日より後で最も近い日付を探す
2. その日付の23:59までを上限として拡張表示する
3. due_date が null のタスクは期限フィルタ時は除外される

---

## 6. コンポーネント仕様追記

### TaskCard.vue（v1.3更新）

**レイアウト構造**

```
┌──────────────────────────────────────────────┐
│ [タイプ] [ステータス] [must]  [子タスク]    >  │
│ タスク名（text-2xl font-medium）               │
│ 完了条件テキスト（truncate）   期限: MM/dd     │
└──────────────────────────────────────────────┘
```

- タスク名：`text-2xl font-medium`
- 完了条件と期限は同一行・flexで横並び（完了条件 truncate、期限 shrink-0 右端）
- 期限フォーマット：`MM/dd`（カード内のみ。他画面は `yyyy/MM/dd` のまま）

**バッジ表示ロジック**

```
parent_id != null
  → 「子タスク」バッジを表示（薄いグレー系）

origin_checklist_item_id != null（かつ parent_id != null）
  → 「子タスク」バッジに加えて「切り出し」バッジを表示（薄いブルー系）
```

**2カラム時のクリック挙動**

```typescript
// lg以上: selectedTaskId を更新（ページ遷移しない）
// lg未満: /tasks/[id] にページ遷移
```

---

### usePushNotification.ts（v1.5追加）

```typescript
// Web Push API（Service Worker + VAPID）のラッパー

export function usePushNotification() {
  const isSubscribed = ref(false)

  async function subscribe(): Promise<void>
  // 1. navigator.serviceWorker.register('/sw.js')
  // 2. GET /push/vapid-public-key
  // 3. registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey })
  // 4. POST /push/subscribe (endpoint, keys.p256dh, keys.auth)

  async function unsubscribe(): Promise<void>
  // 1. DELETE /push/subscribe (エラーは無視)
  // 2. pushSubscription.unsubscribe()

  async function sendTodayDue(): Promise<void>
  // POST /push/send-today-due

  return { isSubscribed, subscribe, unsubscribe, sendTodayDue }
}
```

**制約事項：**
- **HTTPS 必須**（Service Worker は http://localhost のみ例外）
- `urlBase64ToUint8Array` は ArrayBuffer を返す（Uint8Array より型互換性が高い）
- 通知許可はブラウザのダイアログで行う（アプリ内UIなし）

**タスク一覧ヘッダーのアイコン：**

| アイコン | 役割 | 表示条件 |
|---------|------|---------|
| `i-lucide-bell-off` | 未購読（クリックで購読） | 常に表示 |
| `i-lucide-bell` | 購読済み（クリックで解除） | 購読中のみ |
| `i-lucide-send` | 今日期限のタスクを今すぐ通知 | 購読中のみ |

---

## 7. 実装上の注意点・既知の挙動

### 7.1 日本語IME入力（isComposing）

`@keydown.enter` で処理をトリガーするフォームでは、日本語変換確定の Enter と送信の Enter が競合する。`event.isComposing === true` の間はハンドラをスキップすることで対処する。

```typescript
async function handleAdd(e?: KeyboardEvent) {
  if (e?.isComposing) return  // IME変換中は無視
}
```

対象コンポーネント：`ChecklistPanel.vue`、`ChecklistItem.vue`

### 7.2 チェックリストのインライン編集

| 操作 | 動作 |
|------|------|
| テキストをダブルクリック | 編集モードに入る |
| 鉛筆アイコンをクリック | 編集モードに入る |
| Enter / フォーカスを外す | 変更を保存 |
| Esc | 編集キャンセル |

切り出し済みアイテム（`extracted_task_id` あり）は編集不可。

### 7.3 スリープ防止（Wake Lock）

`useWakeLock.ts` composable で Screen Wake Lock API をラップ。タスク一覧画面のヘッダーにトグルボタンを配置する。

| 状態 | アイコン | 色 |
|------|---------|-----|
| OFF | 月（i-lucide-moon） | neutral / ghost |
| ON | 太陽（i-lucide-sun） | warning / solid |

**制約事項：**
- **HTTPS 必須**。`http://` でのアクセス（LAN IP 経由など）では `navigator.wakeLock` が利用不可
- 非対応環境ではトーストで「このブラウザはスリープ防止に対応していません」を表示
- ページ離脱時（`onUnmounted`）に自動解除

```typescript
// useWakeLock.ts の返り値
{ isActive: Ref<boolean>, isSupported: Ref<boolean>, toggle: () => Promise<void> }
```

### 7.4 プッシュ通知（Web Push / VAPID）

- HTTPS 必須（localhost は例外）。LAN IP（http://192.168.x.x）は動作不可
- Nuxt UI v4 は `UToggle` 廃止 → `USwitch` を使用
- Service Worker は `frontend/public/sw.js` に配置（Nuxt の static ファイルとして提供）
- `sw.js` は `push` イベントでトーストを表示、`notificationclick` で `/` を開く

```javascript
// sw.js の主要ロジック
self.addEventListener('push', (event) => {
  const data = event.data?.json() ?? {}
  event.waitUntil(
    self.registration.showNotification(data.title, { body: data.body })
  )
})
self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  event.waitUntil(clients.openWindow('/'))
})
```

### 7.5 Docker開発環境でのHMR

macOS + Docker では inotify によるファイル変更検知が機能しないため、ポーリングを使用する。

`nuxt.config.ts`:

```typescript
vite: {
  server: {
    watch: { usePolling: true, interval: 1000 }
  }
}
```

---

## 8. 次回スコープ

| 項目 | 優先度 | 内容 |
|------|-------|------|
| 複数statusフィルタ | 高 | `status=todo&status=doing` の複数値送信対応（バックエンドと合わせて） |
| 2カラムのスクロール独立 | 中 | 左右カラムで独立してスクロールできるよう overflow-y-auto を設定 |
| タスク詳細の遅延ロード | 低 | 2カラム時は選択時に初めてAPIを叩く（初期ロードの節約） |
| モバイル対応拡張 | 低 | スワイプジェスチャー等 |