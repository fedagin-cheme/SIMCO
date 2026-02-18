import {
  FlaskConical,
  Columns,
  FolderOpen,
  Settings,
  BookOpen,
  ChevronRight,
} from 'lucide-react'

export type Page =
  | 'vle-calculator'
  | 'packed-column'
  | 'tray-column'
  | 'projects'
  | 'database'
  | 'settings'

interface NavItem {
  id: Page
  label: string
  icon: React.ReactNode
  badge?: string
}

const NAV_ITEMS: NavItem[] = [
  {
    id: 'vle-calculator',
    label: 'VLE Calculator',
    icon: <FlaskConical size={16} />,
  },
  {
    id: 'packed-column',
    label: 'Packed Column',
    icon: <Columns size={16} />,
    badge: 'Phase 3',
  },
  {
    id: 'tray-column',
    label: 'Tray Column',
    icon: <Columns size={16} />,
    badge: 'Phase 4',
  },
]

const BOTTOM_ITEMS: NavItem[] = [
  { id: 'projects', label: 'Projects', icon: <FolderOpen size={16} /> },
  { id: 'database', label: 'Database', icon: <BookOpen size={16} /> },
  { id: 'settings', label: 'Settings', icon: <Settings size={16} /> },
]

interface SidebarProps {
  activePage: Page
  onNavigate: (page: Page) => void
}

function NavButton({ item, active, onClick }: {
  item: NavItem
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors group ${
        active
          ? 'bg-primary-600/20 text-primary-400 border border-primary-600/30'
          : 'text-slate-400 hover:text-slate-100 hover:bg-surface-600 border border-transparent'
      }`}
    >
      <span className={active ? 'text-primary-400' : 'text-slate-500 group-hover:text-slate-300'}>
        {item.icon}
      </span>
      <span className="text-sm font-medium flex-1">{item.label}</span>
      {item.badge ? (
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-600 text-slate-500 font-medium">
          {item.badge}
        </span>
      ) : active ? (
        <ChevronRight size={12} className="text-primary-500" />
      ) : null}
    </button>
  )
}

export function Sidebar({ activePage, onNavigate }: SidebarProps) {
  return (
    <div className="w-56 bg-surface-800 border-r border-surface-700 flex flex-col flex-shrink-0">
      {/* Main nav */}
      <div className="p-3 flex-1">
        <p className="label px-3 mb-2">Calculations</p>
        <nav className="space-y-1">
          {NAV_ITEMS.map(item => (
            <NavButton
              key={item.id}
              item={item}
              active={activePage === item.id}
              onClick={() => onNavigate(item.id)}
            />
          ))}
        </nav>
      </div>

      {/* Bottom nav */}
      <div className="p-3 border-t border-surface-700">
        <nav className="space-y-1">
          {BOTTOM_ITEMS.map(item => (
            <NavButton
              key={item.id}
              item={item}
              active={activePage === item.id}
              onClick={() => onNavigate(item.id)}
            />
          ))}
        </nav>
      </div>
    </div>
  )
}
