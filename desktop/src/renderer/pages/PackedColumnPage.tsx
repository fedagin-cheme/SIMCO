import { useState, useEffect } from 'react'
import {
  Columns,
  Play,
  AlertCircle,
  Loader2,
  ChevronRight,
  Info,
  CheckCircle2,
  AlertTriangle,
  FlaskConical,
  X,
} from 'lucide-react'
import { useEngine } from '../hooks/useEngine'

// ─── Types ──────────────────────────────────────────────────────────────────────

interface Packing {
  name: string
  type: 'random' | 'structured'
  material: string
  nominal_size_mm: number | null
  specific_area: number
  void_fraction: number
  packing_factor: number
  hetp: number
  source: string
}

interface PackingListResponse {
  packings: Packing[]
  count: number
}

interface HydraulicResult {
  packing_name: string
  packing_type: string
  packing_factor: number
  specific_area: number
  void_fraction: number
  T_celsius: number
  P_bar: number
  G_mass_kgs: number
  L_mass_kgs: number
  rho_G_kgm3: number
  rho_L_kgm3: number
  flow_parameter_X: number
  u_flood_ms: number
  flooding_fraction: number
  u_design_ms: number
  A_column_m2: number
  D_column_m: number
  D_column_mm: number
  pressure_drop_Pa_m: number
  pressure_drop_mbar_m: number
  min_wetting_rate_m3m2s: number
  actual_liquid_vel_m3m2s: number
  wetting_adequate: boolean
}

// ─── Helpers ────────────────────────────────────────────────────────────────────

function Field({ label, children, hint }: { label: string; children: React.ReactNode; hint?: string }) {
  return (
    <div>
      <label className="text-slate-400 text-xs font-medium block mb-1">{label}</label>
      {children}
      {hint && <p className="text-slate-600 text-[10px] mt-0.5">{hint}</p>}
    </div>
  )
}

function ResultCard({ label, value, unit, highlight = false, warn = false }: {
  label: string
  value: string
  unit?: string
  highlight?: boolean
  warn?: boolean
}) {
  return (
    <div className="panel p-3">
      <p className="text-slate-500 text-xs mb-1">{label}</p>
      <p className={`text-lg font-mono font-medium ${
        warn ? 'text-amber-400' : highlight ? 'text-primary-400' : 'text-slate-100'
      }`}>
        {value}
        {unit && <span className="text-xs text-slate-500 ml-1">{unit}</span>}
      </p>
    </div>
  )
}

function PropRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between py-1.5 border-b border-surface-700/50 last:border-0">
      <span className="text-slate-500 text-xs">{label}</span>
      <span className="text-slate-200 text-xs font-mono">{value}</span>
    </div>
  )
}

// ─── Main Component ─────────────────────────────────────────────────────────────

interface PackedColumnPageProps {
  preset?: import('../App').ColumnDesignPreset | null
  onClearPreset?: () => void
}

export function PackedColumnPage({ preset, onClearPreset }: PackedColumnPageProps) {
  // Packing data
  const [packings, setPackings] = useState<Packing[]>([])
  const [packingsLoading, setPackingsLoading] = useState(true)
  const [packingsError, setPackingsError] = useState<string | null>(null)
  const [filterType, setFilterType] = useState<'all' | 'random' | 'structured'>('all')
  const [selectedPacking, setSelectedPacking] = useState<Packing | null>(null)

  // Inputs
  const [G_mass, setG_mass] = useState('1.0')
  const [L_mass, setL_mass] = useState('3.0')
  const [rho_G, setRho_G] = useState('1.2')
  const [rho_L, setRho_L] = useState('998')
  const [T_celsius, setT_celsius] = useState('25')
  const [P_bar, setP_bar] = useState('1.01325')
  const [floodFrac, setFloodFrac] = useState('70')
  const [mu_L, setMu_L] = useState('1.0')
  const [sigma, setSigma] = useState('0.072')

  // Results
  const [result, setResult] = useState<HydraulicResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [systemLabel, setSystemLabel] = useState<string | null>(null)

  const engine = useEngine<PackingListResponse>()

  // Apply preset from VLE page
  useEffect(() => {
    if (!preset) return
    setRho_G(preset.rho_G.toString())
    setRho_L(preset.rho_L.toString())
    setT_celsius(preset.T_celsius.toString())
    setP_bar(preset.P_bar.toString())
    const mixtureDesc = preset.gasMixture
      .map(g => `${g.name} ${g.molPercent}%`)
      .join(', ')
    setSystemLabel(`${mixtureDesc} → Remove ${preset.targetGas} with ${preset.solventName}`)
    // Clear the preset so it doesn't re-apply on re-renders
    onClearPreset?.()
  }, [preset])

  // Fetch packings on mount
  useEffect(() => {
    async function fetchPackings() {
      setPackingsLoading(true)
      setPackingsError(null)
      const data = await engine.call('/api/packings')
      if (data) {
        setPackings(data.packings)
        if (data.packings.length > 0 && !selectedPacking) {
          setSelectedPacking(data.packings[0])
        }
      } else {
        setPackingsError(engine.error || 'Failed to load packings')
      }
      setPackingsLoading(false)
    }
    fetchPackings()
  }, [])

  const filteredPackings = filterType === 'all'
    ? packings
    : packings.filter(p => p.type === filterType)

  // Run design calculation
  async function runDesign() {
    if (!selectedPacking) return
    setLoading(true)
    setError(null)

    try {
      const res = await fetch('http://127.0.0.1:8742/api/column/hydraulic-design', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          G_mass_kgs: parseFloat(G_mass),
          L_mass_kgs: parseFloat(L_mass),
          rho_G_kgm3: parseFloat(rho_G),
          rho_L_kgm3: parseFloat(rho_L),
          T_celsius: parseFloat(T_celsius),
          P_bar: parseFloat(P_bar),
          packing_name: selectedPacking.name,
          flooding_fraction: parseFloat(floodFrac) / 100,
          mu_L_Pas: parseFloat(mu_L) * 1e-3, // mPa·s → Pa·s
          sigma_Nm: parseFloat(sigma),
        }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }

      const data: HydraulicResult = await res.json()
      setResult(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Calculation failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full p-4 gap-4 overflow-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary-600/20 rounded-lg">
            <Columns size={20} className="text-primary-400" />
          </div>
          <div>
            <h1 className="text-slate-100 font-semibold text-base">
              Packed Column Design
            </h1>
            <p className="text-slate-500 text-xs">
              Hydraulic sizing — flooding velocity, column diameter, pressure drop
            </p>
          </div>
        </div>
      </div>

      {/* System banner — shows when data came from VLE */}
      {systemLabel && (
        <div className="panel px-4 py-2 flex items-center gap-3 bg-primary-600/5 border-primary-600/20">
          <FlaskConical size={14} className="text-primary-400" />
          <span className="text-xs text-primary-400 font-medium">System: {systemLabel}</span>
          <span className="text-[10px] text-slate-600">
            ρ<sub>G</sub>={rho_G} kg/m³ · ρ<sub>L</sub>={rho_L} kg/m³ · {T_celsius}°C · {P_bar} bar
          </span>
          <button
            onClick={() => setSystemLabel(null)}
            className="ml-auto text-slate-600 hover:text-slate-400 transition-colors"
            title="Dismiss"
          >
            <X size={12} />
          </button>
        </div>
      )}

      {/* Main layout */}
      <div className="flex gap-4 flex-1 min-h-0">
        {/* Left panel: packing selection */}
        <div className="w-72 flex-shrink-0 flex flex-col gap-3 min-h-0">
          {/* Packing type filter */}
          <div className="panel p-2 flex flex-wrap gap-1">
            {(['all', 'random', 'structured'] as const).map(t => (
              <button
                key={t}
                onClick={() => setFilterType(t)}
                className={`px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
                  filterType === t
                    ? 'bg-primary-600/20 text-primary-400'
                    : 'text-slate-500 hover:text-slate-300 hover:bg-surface-700'
                }`}
              >
                {t === 'all' ? 'All Packings' : t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>

          {/* Packing list */}
          <div className="panel flex-1 overflow-y-auto min-h-0">
            {packingsLoading ? (
              <div className="flex items-center justify-center py-8 text-slate-500">
                <Loader2 size={16} className="animate-spin mr-2" /> Loading…
              </div>
            ) : packingsError ? (
              <div className="p-3 text-red-400 text-xs flex items-start gap-2">
                <AlertCircle size={14} className="mt-0.5 flex-shrink-0" />
                {packingsError}
              </div>
            ) : (
              filteredPackings.map(p => (
                <button
                  key={p.name}
                  onClick={() => setSelectedPacking(p)}
                  className={`w-full text-left px-3 py-2.5 border-b border-surface-700/50 transition-colors ${
                    selectedPacking?.name === p.name
                      ? 'bg-primary-600/10 border-l-2 border-l-primary-500'
                      : 'hover:bg-surface-700/30 border-l-2 border-l-transparent'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className={`text-sm font-medium ${
                        selectedPacking?.name === p.name ? 'text-primary-400' : 'text-slate-200'
                      }`}>{p.name}</p>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {p.type} · {p.material} · F<sub>p</sub>={p.packing_factor}
                      </p>
                    </div>
                    {selectedPacking?.name === p.name && (
                      <ChevronRight size={12} className="text-primary-500" />
                    )}
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Packing details card */}
          {selectedPacking && (
            <div className="panel p-3 space-y-1">
              <p className="label text-xs mb-2">Packing Properties</p>
              <PropRow label="Type" value={selectedPacking.type} />
              <PropRow label="Material" value={selectedPacking.material} />
              <PropRow label="Specific area aₚ" value={`${selectedPacking.specific_area} m²/m³`} />
              <PropRow label="Void fraction ε" value={selectedPacking.void_fraction.toFixed(2)} />
              <PropRow label="Packing factor Fₚ" value={`${selectedPacking.packing_factor} m⁻¹`} />
              <PropRow label="HETP" value={`${selectedPacking.hetp} m`} />
              {selectedPacking.nominal_size_mm && (
                <PropRow label="Nominal size" value={`${selectedPacking.nominal_size_mm} mm`} />
              )}
              <PropRow label="Source" value={selectedPacking.source} />
            </div>
          )}
        </div>

        {/* Right panel: inputs + results */}
        <div className="flex-1 flex flex-col gap-4 min-w-0 min-h-0 overflow-y-auto">
          {/* Input form */}
          <div className="panel p-4 space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <Info size={14} className="text-slate-500" />
              <p className="label text-xs">Design Inputs</p>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <Field label="Gas flow rate" hint="kg/s">
                <input
                  type="number"
                  value={G_mass}
                  onChange={e => setG_mass(e.target.value)}
                  className="input-field w-full"
                  step="0.1"
                />
              </Field>
              <Field label="Liquid flow rate" hint="kg/s">
                <input
                  type="number"
                  value={L_mass}
                  onChange={e => setL_mass(e.target.value)}
                  className="input-field w-full"
                  step="0.1"
                />
              </Field>
              <Field label="Flooding fraction" hint="%">
                <input
                  type="number"
                  value={floodFrac}
                  onChange={e => setFloodFrac(e.target.value)}
                  className="input-field w-full"
                  min="10"
                  max="95"
                  step="5"
                />
              </Field>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <Field label="Gas density ρ_G" hint="kg/m³">
                <input
                  type="number"
                  value={rho_G}
                  onChange={e => setRho_G(e.target.value)}
                  className="input-field w-full"
                  step="0.1"
                />
              </Field>
              <Field label="Liquid density ρ_L" hint="kg/m³">
                <input
                  type="number"
                  value={rho_L}
                  onChange={e => setRho_L(e.target.value)}
                  className="input-field w-full"
                  step="1"
                />
              </Field>
              <Field label="Liquid viscosity μ_L" hint="mPa·s">
                <input
                  type="number"
                  value={mu_L}
                  onChange={e => setMu_L(e.target.value)}
                  className="input-field w-full"
                  step="0.1"
                />
              </Field>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <Field label="Temperature" hint="°C">
                <input
                  type="number"
                  value={T_celsius}
                  onChange={e => setT_celsius(e.target.value)}
                  className="input-field w-full"
                />
              </Field>
              <Field label="Pressure" hint="bar">
                <input
                  type="number"
                  value={P_bar}
                  onChange={e => setP_bar(e.target.value)}
                  className="input-field w-full"
                  step="0.01"
                />
              </Field>
              <Field label="Surface tension σ" hint="N/m">
                <input
                  type="number"
                  value={sigma}
                  onChange={e => setSigma(e.target.value)}
                  className="input-field w-full"
                  step="0.001"
                />
              </Field>
            </div>

            <button
              className="btn-primary w-full flex items-center justify-center gap-2"
              onClick={runDesign}
              disabled={loading || !selectedPacking}
            >
              {loading ? (
                <><Loader2 size={14} className="animate-spin" /> Calculating…</>
              ) : (
                <><Play size={14} /> Calculate Column Size</>
              )}
            </button>

            {error && (
              <div className="flex items-start gap-2 text-red-400 text-xs bg-red-500/10 p-2 rounded">
                <AlertCircle size={14} className="mt-0.5 flex-shrink-0" />
                {error}
              </div>
            )}
          </div>

          {/* Results */}
          {result && (
            <div className="space-y-4">
              {/* Key results cards */}
              <div className="grid grid-cols-4 gap-3">
                <ResultCard
                  label="Column Diameter"
                  value={result.D_column_m >= 1
                    ? result.D_column_m.toFixed(2)
                    : result.D_column_mm.toFixed(0)
                  }
                  unit={result.D_column_m >= 1 ? 'm' : 'mm'}
                  highlight
                />
                <ResultCard
                  label="Flooding Velocity"
                  value={result.u_flood_ms.toFixed(2)}
                  unit="m/s"
                />
                <ResultCard
                  label="Design Velocity"
                  value={result.u_design_ms.toFixed(2)}
                  unit="m/s"
                />
                <ResultCard
                  label="Pressure Drop"
                  value={result.pressure_drop_Pa_m.toFixed(1)}
                  unit="Pa/m"
                />
              </div>

              {/* Detailed results */}
              <div className="grid grid-cols-2 gap-4">
                {/* Hydraulic summary */}
                <div className="panel p-4 space-y-2">
                  <p className="label text-xs mb-2">Hydraulic Summary</p>
                  <PropRow label="Packing" value={result.packing_name} />
                  <PropRow label="Flow parameter X" value={result.flow_parameter_X.toFixed(4)} />
                  <PropRow label="Flooding velocity" value={`${result.u_flood_ms.toFixed(3)} m/s`} />
                  <PropRow label="Flooding fraction" value={`${(result.flooding_fraction * 100).toFixed(0)}%`} />
                  <PropRow label="Design velocity" value={`${result.u_design_ms.toFixed(3)} m/s`} />
                  <PropRow label="Column area" value={`${result.A_column_m2.toFixed(4)} m²`} />
                  <PropRow label="Column diameter" value={`${result.D_column_m.toFixed(4)} m (${result.D_column_mm.toFixed(0)} mm)`} />
                  <PropRow label="ΔP/Z" value={`${result.pressure_drop_Pa_m.toFixed(1)} Pa/m (${result.pressure_drop_mbar_m.toFixed(2)} mbar/m)`} />
                </div>

                {/* Wetting & conditions */}
                <div className="panel p-4 space-y-2">
                  <p className="label text-xs mb-2">Operating Conditions</p>
                  <PropRow label="Temperature" value={`${result.T_celsius} °C`} />
                  <PropRow label="Pressure" value={`${result.P_bar.toFixed(4)} bar`} />
                  <PropRow label="Gas flow (G)" value={`${result.G_mass_kgs} kg/s`} />
                  <PropRow label="Liquid flow (L)" value={`${result.L_mass_kgs} kg/s`} />
                  <PropRow label="L/G mass ratio" value={(result.L_mass_kgs / result.G_mass_kgs).toFixed(2)} />
                  <PropRow label="ρ_G" value={`${result.rho_G_kgm3} kg/m³`} />
                  <PropRow label="ρ_L" value={`${result.rho_L_kgm3} kg/m³`} />

                  {/* Wetting check */}
                  <div className="mt-3 pt-2 border-t border-surface-700/50">
                    <div className={`flex items-center gap-2 text-xs ${
                      result.wetting_adequate ? 'text-emerald-400' : 'text-amber-400'
                    }`}>
                      {result.wetting_adequate ? (
                        <CheckCircle2 size={14} />
                      ) : (
                        <AlertTriangle size={14} />
                      )}
                      <span>
                        {result.wetting_adequate
                          ? 'Wetting adequate'
                          : 'Warning: below minimum wetting rate'}
                      </span>
                    </div>
                    <div className="mt-1 text-[10px] text-slate-600">
                      MWR: {result.min_wetting_rate_m3m2s.toExponential(2)} m³/(m²·s) ·
                      Actual: {result.actual_liquid_vel_m3m2s.toExponential(2)} m³/(m²·s)
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Empty state */}
          {!result && !loading && !error && (
            <div className="flex-1 flex items-center justify-center panel">
              <div className="text-center text-slate-500 py-12">
                <Columns size={32} className="mx-auto mb-3 opacity-30" />
                <p className="text-sm">Select a packing and enter design parameters</p>
                <p className="text-xs mt-1">Results will appear here after calculation</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
