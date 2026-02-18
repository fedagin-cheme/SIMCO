import { Minus, Square, X, Wifi, WifiOff } from 'lucide-react'

interface TitleBarProps {
  engineOnline: boolean
}

export function TitleBar({ engineOnline }: TitleBarProps) {
  const isMac = navigator.platform.startsWith('Mac')

  const handleMinimize = () => window.simco?.window.minimize()
  const handleMaximize = () => window.simco?.window.maximize()
  const handleClose = () => window.simco?.window.close()

  return (
    <div className="drag-region h-10 bg-surface-900 border-b border-surface-700 flex items-center justify-between px-4 flex-shrink-0">
      {/* Mac: leave space for traffic lights on left */}
      {isMac ? <div className="w-16" /> : null}

      {/* App title */}
      <div className="flex items-center gap-2">
        <div className="w-5 h-5 bg-primary-600 rounded flex items-center justify-center">
          <span className="text-white font-bold text-[10px]">S</span>
        </div>
        <span className="text-slate-300 font-semibold text-sm tracking-wide">SIMCO</span>
        <span className="text-slate-600 text-xs">Gas Scrubbing & Mass-transfer Calculator</span>
      </div>

      {/* Right: engine status + window controls */}
      <div className="no-drag flex items-center gap-3">
        {/* Engine status pill */}
        <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${
          engineOnline
            ? 'bg-emerald-900/40 text-emerald-400'
            : 'bg-red-900/40 text-red-400'
        }`}>
          {engineOnline
            ? <><Wifi size={11} /> Engine online</>
            : <><WifiOff size={11} /> Engine offline</>
          }
        </div>

        {/* Windows-style window controls (hidden on Mac) */}
        {!isMac && (
          <div className="flex items-center">
            <button
              onClick={handleMinimize}
              className="w-8 h-8 flex items-center justify-center text-slate-400 hover:bg-surface-600 hover:text-slate-100 transition-colors"
            >
              <Minus size={13} />
            </button>
            <button
              onClick={handleMaximize}
              className="w-8 h-8 flex items-center justify-center text-slate-400 hover:bg-surface-600 hover:text-slate-100 transition-colors"
            >
              <Square size={11} />
            </button>
            <button
              onClick={handleClose}
              className="w-8 h-8 flex items-center justify-center text-slate-400 hover:bg-red-600 hover:text-white transition-colors rounded-r"
            >
              <X size={13} />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
