# タスク管理システム フロントエンド設計書

作成日: 2026-02-26 | バージョン: 1.9 | 最終更新: 2026-04-12

> v1.8 → v1.9 変更点：
> - `TaskDetailPanel.vue`：戻るボタンの動作を `emit('back')` に変更（ローカル `mobileView` ref を削除）
> - `pages/tasks/[id]/index.vue`：`@back="router.push('/?view=list')"` でタスクリストに戻る
> - `pages/index.vue`：`route.query.view === 'list'` の場合に `mobileView = 'list'` で復元

> v1.7 → v1.8 変更点：
> - `app.vue`：ヘッダーをシンプル化（「Tapp」ロゴのみ、右側アイコン群を廃止）
> - `index.vue`：ヘッダーのウェイクロック・プッシュ通知アイコンを削除、左カラム下部に設定リンクを追加
> - `pages/settings.vue`：カラーモード切替（`UColorModeButton`）・ウェイクロック・プッシュ通知トグル・手動送信ボタンを集約
> - `composables/useNavItems.ts`：ナビ項目を更新（ログ追加・全ての statuses 明示・Capture 追加）
> - `components/AppNav.vue`：配置を `components/nav/` → `components/` ルートに変更（Nuxt 命名規則対応）、フォントサイズを `text-xl` に変更

> v1.6 → v1.7 変更点：
> - ナビゲーション構造をThings型に再設計（左ペインをフィルタUIからナビゲーションに変更）
> - `components/nav/AppNav.vue` 追加
> - `composables/useNavItems.ts` 追加
> - `index.vue`：左カラムをAppNavに置き換え、フィルタ状態をナビ選択に委譲
> - カテゴリナビを将来機能（v1.0スコープ）として設計書に記載
> - `taskRepository.ts`：`category`パラメータ追加

> v1.5 → v1.6 変更点：
> - `sw.js`：`skipWaiting` / `clients.claim()` 追加（更新時の即時反映）
> - `sw.js`：`requireInteraction: true` 追加（macOS でバナー表示を促進）
> - `sw.js`：icon 指定を削除（存在しないアイコンによる通知失敗を防止）
> - `usePushNotification.ts` 復元（scheduled_notification ブランチに欠落していた）

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
│   ├── AppNav.vue                # 左ペインナビゲーション（v1.7追加、v1.8でルートに移動）
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
│   ├── useNavItems.ts            # ナビ項目定義・選択状態管理（v1.7追加）
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

### taskRepository.ts（v1.7更新）

```typescript
// GET /tasks に category パラメータを追加

export interface TaskListParams {
  status?: TaskStatus | TaskStatus[]  // 複数指定対応（将来）
  task_type?: TaskType
  priority?: Priority
  parent_id?: number | null
  category?: string                                              // v1.7追加
  sort_by?: 'due_date' | 'created_at' | 'priority' | 'title'
  order?: 'asc' | 'desc'
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

### 4.2 タスク一覧画面 `/`（v1.8更新）

#### グローバルヘッダー（app.vue・v1.8更新）

ヘッダーは「Tapp」ロゴのみ。ウェイクロック・プッシュ通知・設定アイコンは廃止し、settings.vue に集約した。

#### モバイル（lg未満）

左ペインのナビゲーションのみ表示。ナビ項目をタップするとタスクリスト画面に遷移し、タスクをタップすると詳細ページ（`/tasks/[id]`）に遷移する。

```
┌─────────────────────────────────────────┐
│  Tapp                                   │  ← ロゴのみ（v1.8）
│  ─────────────────────────────────────  │
│  ★ 今日・明日                          │
│  ≡ 全て                                │
│  ✓ ログ                                │
│  ─────────────────────────────────────  │
│  🕐 放置タスク                    2    │
│  📅 繰り越し候補                   7   │
│  ℹ Capture                             │
│  ─────────────────────────────────────  │
│  [+ 新規作成]                           │
│                                         │
│  [設定]                                 │
└─────────────────────────────────────────┘
```

ナビ項目タップ後（タスクリスト画面）：

```
┌─────────────────────────────────────────┐
│  ← 今日・明日              [+ 新規作成] │
│  ─────────────────────────────────────  │
│  ┌─────────────────────────────────┐   │
│  │ [execution] [must]   未着手  >  │   │
│  │ 支払い申請                       │   │
│  │ 支払い承認完了         期限:04/09 │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ [decision] [must]    未着手  >  │   │
│  │ 事業計画見直し                   │   │
│  │ 4月末までのアクション... 期限:04/10│  │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

#### PC（lg以上）：2カラムレイアウト（v1.8更新）

左カラム（240px固定）はThings型ナビゲーション。ナビ項目を選択すると右カラムにタスクリストを表示し、タスクを選択すると右カラムが詳細に切り替わる。

```
┌──────────────────────────────────────────────────────────────────────┐
│  Tapp                                                                │  ← ロゴのみ（v1.8）
│  ──────────────────────────────────────────────────────────────────  │
│  ┌──────────────────┐  ┌──────────────────────────────────────────┐ │
│  │                  │  │  今日・明日                [+ 新規作成]  │ │
│  │ ★ 今日・明日    │  │  ────────────────────────────────────── │ │
│  │ ≡ 全て          │  │  [execution][must]  未着手       >       │ │
│  │ ✓ ログ          │  │  支払い申請                              │ │
│  │ ────────────    │  │  支払い承認完了            期限:04/09   │ │
│  │ 🕐 放置      2  │  │  ────────────────────────────────────── │ │
│  │ 📅 繰り越し  7  │  │  [decision][must]   未着手       >       │ │
│  │ ℹ Capture       │  │  事業計画見直し                          │ │
│  │                  │  │  4月末までのアクション...  期限:04/10   │ │
│  │ [設定]           │  │  ...                                     │ │
│  └──────────────────┘  └──────────────────────────────────────────┘ │
│   ↑ 固定幅 240px         ↑ 残り幅（flex-1）                         │
└──────────────────────────────────────────────────────────────────────┘
```

**主要コンポーネント（v1.8更新）**

| コンポーネント | 役割 |
|---|---|
| `AppNav.vue` | 左ペインナビゲーション。ナビ項目の選択状態を管理 |
| `TaskCard.vue` | タスクカード。バッジをタイプ＋優先度の2個に絞る |
| `TaskStatusBadge.vue` | ステータスバッジ（右列に表示） |
| `TaskTypeBadge.vue` | タスクタイプバッジ |

---

### 4.3 タスク詳細画面 `/tasks/[id]`（v1.9更新）

タスク名称（title）をページタイトルに明示する。2カラム時は右カラムのヘッダーとして機能する。

```
┌─────────────────────────────────────────┐
│  ← 戻る                 [編集] [削除]  │
│  ─────────────────────────────────────  │
│  タスクタイトル（text-xl font-bold）     │
│  ─────────────────────────────────────  │
│  ┌─────────────────────────────────┐   │
│  │  [research]  must  期限: 04/28  │   │  ← タイプ・優先度・期限
│  │                                  │   │
│  │  完了条件                        │   │
│  │  ○○になったら完了                 │   │
│  │                                  │   │
│  │  決定基準（decision_criteriaあり）│   │
│  │  ○○であれば採用                   │   │
│  │                                  │   │
│  │  探索上限: 3件  可逆: はい        │   │
│  │                                  │   │
│  │  切り出し元: 「親タスク名」から    │   │  ← origin がある場合のみ
│  │  ─────────────────────────────   │   │
│  │  [未着手][進行中][要再定義][保留] │   │  ← ステータス変更ボタン（UCard footer）
│  │  [✓ 完了]                        │   │  ← done 以外のみ表示
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  チェックリスト          [+ 追加] │   │
│  │  ☑ 項目A                        │   │
│  │  ☐ 項目B  [✎] [→切り出し]       │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  子タスク               [+ 追加] │   │
│  │  └ 子タスクタイトル  [doing]     │   │
│  └─────────────────────────────────┘   │
│                                         │
│  最終更新: YYYY/MM/DD HH:MM / 作成: ... │
└─────────────────────────────────────────┘
```

**v1.9 の変更点：**
- モバイルの戻るボタン（`lg:hidden`）を `emit('back')` パターンに変更
  - `TaskDetailPanel.vue` 内のローカル `mobileView` ref を削除
  - `pages/tasks/[id]/index.vue` が `@back` を受け取り `router.push('/?view=list')` で遷移
  - `pages/index.vue` が `route.query.view === 'list'` を検出して `mobileView = 'list'` に復元
- これにより、タスク詳細からタスクリスト画面（nav 画面ではなく）に正しく戻れる

**v1.8 の変更点：**
- ステータスバッジ（`TaskStatusBadge`）を廃止 → ステータス変更ボタンの active 状態（solid variant）で現在ステータスを表現
- CaptureBox セクションを削除（`/capture` ページに集約）
- 完了ボタンを `UCard` フッターに統合
- 削除・完了の確認ダイアログを `ConfirmDialog` コンポーネント → `UModal` に変更
- タイムスタンプ表示（`last_updated_at` / `created_at`）を追加

主要コンポーネント：`ChecklistPanel.vue`、`ChecklistItem.vue`、`TaskChildList.vue`

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
│  │  [カラーモード切替]               │   │  ← UColorModeButton（v1.8追加）
│  │  [🌙 スリープ防止]               │   │  ← ウェイクロックボタン（v1.8移動）
│  │  [🔔 プッシュ通知ON/OFF]         │   │  ← プッシュ通知ボタン（v1.8移動）
│  │  [✈ 今日分を今すぐ通知]          │   │  ← 購読中のみ表示（v1.8移動）
│  │                                  │   │
│  │  [         保存          ]       │   │
│  └─────────────────────────────────┘   │
│  ※ プッシュ通知の受信には通知許可が必要  │
└─────────────────────────────────────────┘
```

- マウント時に `GET /push/notification-setting` で現在の設定を読み込む
- 保存ボタンで `PUT /push/notification-setting` を呼び出す
- 通知時刻は常に表示（enabled の有無に依らない）
- ウェイクロック・プッシュ通知ボタンは v1.8 でタスク一覧ヘッダーから移動（`index.vue` からは削除）

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

### AppNav.vue（v1.7追加、v1.8更新）

配置：`components/AppNav.vue`（Nuxt の命名規則により `components/` ルートに配置。サブディレクトリに置くと `NavAppNav` として登録されるため）

**ナビ項目定義（v1.8更新）**

| key | label | アイコン | 動作 |
|-----|-------|---------|------|
| `today` | 今日・明日 | i-lucide-star | status=todo/doing・due_date≦明日でフィルタ |
| `all` | 全て | i-lucide-layers | status=todo/doing/carryover_candidate/needs_redefine/snoozed（完了除く） |
| `log` | ログ | i-lucide-check-circle | status=done のみ |
| `stale` | 放置タスク | i-lucide-clock | `/stale` へ遷移 |
| `carryover` | 繰り越し候補 | i-lucide-calendar-x | `/carryover` へ遷移 |
| `capture` | Capture | i-lucide-info | `/capture` へ遷移 |

**セパレーター：** `stale` の直前に `UDivider` を挿入

**Props**

| prop | 型 | 説明 |
|------|----|------|
| `modelValue` | `string` | 選択中のナビキー（v-model） |
| `staleCount` | `number` | 放置タスク件数（右端バッジ） |
| `carryoverCount` | `number` | 繰り越し候補件数（右端バッジ） |

**Emits**

| イベント | 内容 |
|---------|------|
| `update:modelValue` | ナビ項目選択時にkeyを返す |
| `navigate` | 選択されたNavItemを返す（ページ遷移・フィルタ切り替えの判断に使用） |

**選択状態のスタイル**

- 選択中（`to`なし）：`bg-primary text-white`
- 非選択：`hover:bg-elevated`
- `to`あり（遷移アイテム）：選択状態を持たない
- フォントサイズ：`text-xl`（v1.8変更）

---

### useNavItems.ts（v1.7追加、v1.8更新）

```typescript
export interface NavItem {
  key: string
  label: string
  icon: string
  to?: string           // ページ遷移先（指定時はフィルタ不使用）
  filter?: {
    statuses?: TaskStatus[]
    dueDateLimit?: 'today_tomorrow'
  }
}

export function useNavItems() {
  const NAV_ITEMS: NavItem[] = [
    {
      key: 'today',
      label: '今日・明日',
      icon: 'i-lucide-star',
      filter: { statuses: ['todo', 'doing'], dueDateLimit: 'today_tomorrow' }
    },
    {
      key: 'all',
      label: '全て',
      icon: 'i-lucide-layers',
      filter: { statuses: ['todo', 'doing', 'carryover_candidate', 'needs_redefine', 'snoozed'] }
    },
    {
      key: 'log',
      label: 'ログ',
      icon: 'i-lucide-check-circle',
      filter: { statuses: ['done'] }
    },
    {
      key: 'stale',
      label: '放置タスク',
      icon: 'i-lucide-clock',
      to: '/stale'
    },
    {
      key: 'carryover',
      label: '繰り越し候補',
      icon: 'i-lucide-calendar-x',
      to: '/carryover'
    },
    {
      key: 'capture',
      label: 'Capture',
      icon: 'i-lucide-info',
      to: '/capture'
    }
  ]

  return { NAV_ITEMS }
}
```

---

### TaskCard.vue（v1.7更新）

**レイアウト構造**

```
┌──────────────────────────────────────────────┐
│ [タイプ] [must]                  [ステータス] >│
│ タスク名（text-base font-semibold truncate）   │
│ 完了条件テキスト（truncate）       期限: MM/dd │
└──────────────────────────────────────────────┘
```

- バッジをタイプ＋優先度の**2個**に絞る（ステータスは右列に移動）
- `子タスク`・`切り出し`バッジは詳細パネルで確認できるため**リストから除去**
- タスク名：`text-base font-semibold`（`text-2xl`から変更）
- `flex-wrap`を廃止しバッジ折り返しを防止

**バッジ表示ロジック（v1.7更新）**

```
タイプバッジ：常に表示（TaskTypeBadge）
mustバッジ：priority === 'must' の場合のみ表示
ステータスバッジ：右列に移動（TaskStatusBadge）
子タスク・切り出しバッジ：削除（詳細パネルで確認）
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
- `sw.js` は `push` イベントで OS 通知を表示、`notificationclick` で `/` を開く

```javascript
// sw.js の全ロジック
self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()))

self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : { title: '通知', body: '' }
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      requireInteraction: true,  // macOS でバナー表示を促進
    })
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  event.waitUntil(clients.openWindow('/'))
})
```

**SW 更新時の注意点：**
- `skipWaiting()` により SW 更新が即時反映される（waiting 状態にならない）
- `clients.claim()` により既存タブも新 SW の管理下に入る
- icon を指定しない（存在しないファイルを指定すると一部 Chrome バージョンで通知が表示されない）

**macOS での通知バナー表示について：**
- システム設定 → 通知 → Google Chrome → スタイルを「バナー」または「通知パネル」に設定必要
- `requireInteraction: true` を設定することで Chrome on macOS でのバナー表示を促進
- macOS Sonoma + Chrome の組み合わせで、通知センターのみ表示になる場合がある（OS/ブラウザ側の制約）

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

## 9. 将来スコープ（v1.0以降）

### カテゴリナビゲーション

**目的：** タスクを本業・個人開発・NPO・個人事業などの文脈で構造的に把握する。

**設計方針：**
- `categories` テーブルをマスタ管理として追加（自由入力文字列のままではナビ項目の表記ゆれが発生するため）
- タスク登録時はプルダウンで選択（任意）
- `GET /categories` エンドポイントを追加し、AppNavのナビ項目として動的生成
- カテゴリなしのタスクは「未分類」として扱う

**AppNavへの追加イメージ：**

```
★ 今日・明日
≡ 全て
────────────
🕐 放置タスク
📅 繰り越し候補
────────────
○ 本業
○ 個人開発
○ NPO
○ 個人事業
```

**バックエンド変更：**
- `categories` テーブル追加（マイグレーション）
- `tasks.category` を外部キー参照に変更（現状は自由入力文字列）
- `GET /categories`・`POST /categories`・`PATCH /categories/{id}`・`DELETE /categories/{id}` を追加