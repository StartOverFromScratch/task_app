import type { TaskStatus } from '~/types/task'

export interface NavItem {
  key: string
  label: string
  icon: string
  to?: string
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
