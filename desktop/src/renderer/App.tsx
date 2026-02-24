import { useState, useEffect } from 'react'
import { TitleBar } from './components/TitleBar'
import { Sidebar, Page } from './components/Sidebar'
import { VLECalculatorPage } from './pages/VLECalculatorPage'
import { PackedColumnPage } from './pages/PackedColumnPage'
import { ComingSoonPage } from './pages/ComingSoonPage'
import { checkEngineHealth } from './hooks/useEngine'

/** Shared preset passed from VLE → Column Design */
export interface GasMixtureComponent {
  name: string
  mw: number
  molPercent: number
}

export interface ColumnDesignPreset {
  gasMixture: GasMixtureComponent[]
  targetGas: string       // name of the gas to remove
  solventName: string
  solventMW: number
  T_celsius: number
  P_bar: number
  mixtureMW: number       // mol-fraction-weighted average MW
  rho_G: number           // estimated gas density [kg/m³]
  rho_L: number           // estimated liquid density [kg/m³]
}

export default function App() {
  const [activePage, setActivePage] = useState<Page>('vle-calculator')
  const [engineOnline, setEngineOnline] = useState(false)
  const [columnPreset, setColumnPreset] = useState<ColumnDesignPreset | null>(null)

  // Poll engine health every 5 seconds
  useEffect(() => {
    let cancelled = false

    async function check() {
      const ok = await checkEngineHealth()
      if (!cancelled) setEngineOnline(ok)
    }

    check()
    const interval = setInterval(check, 5000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  /** Called from VLE page to push system data to column design */
  function handleSendToColumnDesign(preset: ColumnDesignPreset) {
    setColumnPreset(preset)
    setActivePage('packed-column')
  }

  function renderPage() {
    switch (activePage) {
      case 'vle-calculator':
        return <VLECalculatorPage onSendToColumnDesign={handleSendToColumnDesign} />
      case 'packed-column':
        return <PackedColumnPage preset={columnPreset} onClearPreset={() => setColumnPreset(null)} />
      case 'tray-column':
        return (
          <ComingSoonPage
            title="Tray Column Design"
            phase="Phase 4"
            description="McCabe-Thiele, Kremser method, MESH equations, tray hydraulics."
          />
        )
      case 'projects':
        return (
          <ComingSoonPage
            title="Project Manager"
            phase="Phase 2"
            description="Save, load, and manage .smc simulation files."
          />
        )
      case 'database':
        return (
          <ComingSoonPage
            title="Chemical Database"
            phase="Phase 2"
            description="Browse compounds, solvents, and packing materials. Add custom entries."
          />
        )
      case 'settings':
        return (
          <ComingSoonPage
            title="Settings"
            phase="Phase 2"
            description="Unit system, default values, engine configuration."
          />
        )
      default:
        return null
    }
  }

  return (
    <div className="flex flex-col h-screen bg-surface-900">
      <TitleBar engineOnline={engineOnline} />

      <div className="flex flex-1 min-h-0">
        <Sidebar activePage={activePage} onNavigate={setActivePage} />

        <main className="flex-1 min-w-0 overflow-hidden flex flex-col">
          {renderPage()}
        </main>
      </div>
    </div>
  )
}

// Type augmentation so TypeScript knows about window.simco
declare global {
  interface Window {
    simco?: {
      engine: {
        getStatus: () => Promise<{ ready: boolean; url: string }>
        getUrl: () => Promise<string>
        onReady: (callback: () => void) => void
        onOffline: (callback: () => void) => void
      }
      window: {
        minimize: () => void
        maximize: () => void
        close: () => void
      }
      shell: {
        openExternal: (url: string) => void
      }
    }
  }
}
