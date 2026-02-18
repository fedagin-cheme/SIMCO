import { useState, useEffect } from 'react'
import { TitleBar } from './components/TitleBar'
import { Sidebar, Page } from './components/Sidebar'
import { VLECalculatorPage } from './pages/VLECalculatorPage'
import { ComingSoonPage } from './pages/ComingSoonPage'
import { checkEngineHealth } from './hooks/useEngine'

export default function App() {
  const [activePage, setActivePage] = useState<Page>('vle-calculator')
  const [engineOnline, setEngineOnline] = useState(false)

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

  function renderPage() {
    switch (activePage) {
      case 'vle-calculator':
        return <VLECalculatorPage />
      case 'packed-column':
        return (
          <ComingSoonPage
            title="Packed Column Design"
            phase="Phase 3"
            description="HTU-NTU, HETP, flooding analysis, rate-based sizing. Coming after VLE foundation is complete."
          />
        )
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
