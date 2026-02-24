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
  Ruler,
} from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
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

interface MassTransferResult {
  y_in: number
  y_out: number
  removal_percent: number
  m_equilibrium: number
  absorption_factor_A: number
  N_OG: number
  H_G_m: number
  H_L_m: number
  H_OG_m: number
  lambda_stripping: number
  Z_htu_ntu_m: number
  Z_hetp_m: number
  HETP_m: number
  kG_a_per_s: number
  kL_a_per_s: number
  G_mol_flux: number
  L_mol_flux: number
  G_mass_flux: number
  L_mass_flux: number
  total_dP_Pa: number | null
  total_dP_mbar: number | null
  lines: {
    x_eq: number[]
    y_eq: number[]
    x_op: number[]
    y_op: number[]
    x_in: number
    x_out: number
  }
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
  label: string; value: string; unit?: string; highlight?: boolean; warn?: boolean
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

const ENGINE_URL = 'http://127.0.0.1:8742'

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

  // Hydraulic inputs
  const [G_mass, setG_mass] = useState('1.0')
  const [L_mass, setL_mass] = useState('3.0')
  const [rho_G, setRho_G] = useState('1.2')
  const [rho_L, setRho_L] = useState('998')
  const [T_celsius, setT_celsius] = useState('25')
  const [P_bar, setP_bar] = useState('1.01325')
  const [floodFrac, setFloodFrac] = useState('70')
  const [mu_L, setMu_L] = useState('1.0')
  const [sigma, setSigma] = useState('0.072')

  // Mass transfer inputs
  const [y_in, setY_in] = useState('5.0')
  const [y_out, setY_out] = useState('0.5')
  const [m_eq, setM_eq] = useState('0.8')
  const [G_mol, setG_mol] = useState('40')
  const [L_mol, setL_mol] = useState('100')
  const [D_G, setD_G] = useState('1.5e-5')
  const [D_L, setD_L] = useState('1.5e-9')

  // Results
  const [hydResult, setHydResult] = useState<HydraulicResult | null>(null)
  const [mtResult, setMtResult] = useState<MassTransferResult | null>(null)
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

  // Run both calculations
  async function runDesign() {
    if (!selectedPacking) return
    setLoading(true)
    setError(null)
    setHydResult(null)
    setMtResult(null)

    try {
      // Step 1: Hydraulic design
      const hydRes = await fetch(`${ENGINE_URL}/api/column/hydraulic-design`, {
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
          mu_L_Pas: parseFloat(mu_L) * 1e-3,
          sigma_Nm: parseFloat(sigma),
        }),
      })

      if (!hydRes.ok) {
        const err = await hydRes.json().catch(() => ({ detail: hydRes.statusText }))
        throw new Error(err.detail || `Hydraulic: HTTP ${hydRes.status}`)
      }

      const hydData: HydraulicResult = await hydRes.json()
      setHydResult(hydData)

      // Step 2: Mass transfer design (uses column area from Step 1)
      const mtRes = await fetch(`${ENGINE_URL}/api/column/mass-transfer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          y_in: parseFloat(y_in) / 100,
          y_out: parseFloat(y_out) / 100,
          m_equilibrium: parseFloat(m_eq),
          G_mol_per_s: parseFloat(G_mol),
          L_mol_per_s: parseFloat(L_mol),
          A_column_m2: hydData.A_column_m2,
          packing_name: selectedPacking.name,
          rho_G_kgm3: parseFloat(rho_G),
          rho_L_kgm3: parseFloat(rho_L),
          mu_G_Pas: 1.8e-5,
          mu_L_Pas: parseFloat(mu_L) * 1e-3,
          D_G_m2s: parseFloat(D_G),
          D_L_m2s: parseFloat(D_L),
          sigma_Nm: parseFloat(sigma),
          P_total_Pa: parseFloat(P_bar) * 1e5,
          dP_per_m_Pa: hydData.pressure_drop_Pa_m,
        }),
      })

      if (!mtRes.ok) {
        const err = await mtRes.json().catch(() => ({ detail: mtRes.statusText }))
        throw new Error(err.detail || `Mass transfer: HTTP ${mtRes.status}`)
      }

      const mtData: MassTransferResult = await mtRes.json()
      setMtResult(mtData)

    } catch (e) {
      setError(e instanceof Error ? e.message : 'Calculation failed')
    } finally {
      setLoading(false)
    }
  }

  // Prepare chart data
  const chartData = mtResult?.lines ? (() => {
    const lines = mtResult.lines
    const data: { x: number; y_eq: number; y_op: number | null }[] = []
    const n = lines.x_eq.length
    for (let i = 0; i < n; i++) {
      data.push({
        x: lines.x_eq[i],
        y_eq: lines.y_eq[i],
        y_op: i < lines.x_op.length ? lines.y_op[i] : null,
      })
    }
    return data
  })() : null

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
              Hydraulic sizing + mass transfer — column diameter, packed height, operating lines
            </p>
          </div>
        </div>
      </div>

      {/* System banner */}
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

          {/* Hydraulic Inputs */}
          <div className="panel p-4 space-y-3">
            <div className="flex items-center gap-2">
              <Info size={14} className="text-slate-500" />
              <p className="label text-xs">Hydraulic Design</p>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <Field label="Gas flow rate" hint="kg/s">
                <input type="number" value={G_mass} onChange={e => setG_mass(e.target.value)} className="input-field w-full" step="0.1" />
              </Field>
              <Field label="Liquid flow rate" hint="kg/s">
                <input type="number" value={L_mass} onChange={e => setL_mass(e.target.value)} className="input-field w-full" step="0.1" />
              </Field>
              <Field label="Flooding fraction" hint="%">
                <input type="number" value={floodFrac} onChange={e => setFloodFrac(e.target.value)} className="input-field w-full" min="10" max="95" step="5" />
              </Field>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <Field label="ρ_G" hint="kg/m³">
                <input type="number" value={rho_G} onChange={e => setRho_G(e.target.value)} className="input-field w-full" step="0.1" />
              </Field>
              <Field label="ρ_L" hint="kg/m³">
                <input type="number" value={rho_L} onChange={e => setRho_L(e.target.value)} className="input-field w-full" step="1" />
              </Field>
              <Field label="μ_L" hint="mPa·s">
                <input type="number" value={mu_L} onChange={e => setMu_L(e.target.value)} className="input-field w-full" step="0.1" />
              </Field>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <Field label="Temperature" hint="°C">
                <input type="number" value={T_celsius} onChange={e => setT_celsius(e.target.value)} className="input-field w-full" />
              </Field>
              <Field label="Pressure" hint="bar">
                <input type="number" value={P_bar} onChange={e => setP_bar(e.target.value)} className="input-field w-full" step="0.01" />
              </Field>
              <Field label="σ" hint="N/m">
                <input type="number" value={sigma} onChange={e => setSigma(e.target.value)} className="input-field w-full" step="0.001" />
              </Field>
            </div>
          </div>

          {/* Mass Transfer Inputs */}
          <div className="panel p-4 space-y-3">
            <div className="flex items-center gap-2">
              <Ruler size={14} className="text-slate-500" />
              <p className="label text-xs">Separation & Mass Transfer</p>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <Field label="Inlet gas y_in" hint="mol%">
                <input type="number" value={y_in} onChange={e => setY_in(e.target.value)} className="input-field w-full" step="0.1" min="0" />
              </Field>
              <Field label="Outlet gas y_out" hint="mol%">
                <input type="number" value={y_out} onChange={e => setY_out(e.target.value)} className="input-field w-full" step="0.1" min="0" />
              </Field>
              <Field label="Equilibrium slope m" hint="y* = m·x">
                <input type="number" value={m_eq} onChange={e => setM_eq(e.target.value)} className="input-field w-full" step="0.1" />
              </Field>
            </div>
            <div className="grid grid-cols-4 gap-3">
              <Field label="G (gas molar)" hint="mol/s">
                <input type="number" value={G_mol} onChange={e => setG_mol(e.target.value)} className="input-field w-full" step="1" />
              </Field>
              <Field label="L (liquid molar)" hint="mol/s">
                <input type="number" value={L_mol} onChange={e => setL_mol(e.target.value)} className="input-field w-full" step="1" />
              </Field>
              <Field label="D_G" hint="m²/s">
                <input type="text" value={D_G} onChange={e => setD_G(e.target.value)} className="input-field w-full" />
              </Field>
              <Field label="D_L" hint="m²/s">
                <input type="text" value={D_L} onChange={e => setD_L(e.target.value)} className="input-field w-full" />
              </Field>
            </div>
          </div>

          {/* Calculate button */}
          <button
            className="btn-primary w-full flex items-center justify-center gap-2"
            onClick={runDesign}
            disabled={loading || !selectedPacking}
          >
            {loading ? (
              <><Loader2 size={14} className="animate-spin" /> Calculating…</>
            ) : (
              <><Play size={14} /> Calculate Column Design</>
            )}
          </button>

          {error && (
            <div className="flex items-start gap-2 text-red-400 text-xs bg-red-500/10 p-2 rounded">
              <AlertCircle size={14} className="mt-0.5 flex-shrink-0" />
              {error}
            </div>
          )}

          {/* ── Results ── */}
          {hydResult && mtResult && (
            <div className="space-y-4">
              {/* Headline cards */}
              <div className="grid grid-cols-5 gap-3">
                <ResultCard
                  label="Column Diameter"
                  value={hydResult.D_column_m >= 1
                    ? hydResult.D_column_m.toFixed(2)
                    : hydResult.D_column_mm.toFixed(0)}
                  unit={hydResult.D_column_m >= 1 ? 'm' : 'mm'}
                  highlight
                />
                <ResultCard
                  label="Packed Height (HTU×NTU)"
                  value={mtResult.Z_htu_ntu_m.toFixed(2)}
                  unit="m"
                  highlight
                />
                <ResultCard
                  label="Packed Height (HETP)"
                  value={mtResult.Z_hetp_m.toFixed(2)}
                  unit="m"
                />
                <ResultCard
                  label="Removal"
                  value={mtResult.removal_percent.toFixed(1)}
                  unit="%"
                />
                <ResultCard
                  label="Total ΔP"
                  value={mtResult.total_dP_mbar !== null ? mtResult.total_dP_mbar.toFixed(1) : '—'}
                  unit="mbar"
                />
              </div>

              {/* Detail panels */}
              <div className="grid grid-cols-3 gap-4">
                {/* Hydraulic */}
                <div className="panel p-4 space-y-2">
                  <p className="label text-xs mb-2">Hydraulic Summary</p>
                  <PropRow label="Packing" value={hydResult.packing_name} />
                  <PropRow label="Flow parameter X" value={hydResult.flow_parameter_X.toFixed(4)} />
                  <PropRow label="Flooding velocity" value={`${hydResult.u_flood_ms.toFixed(3)} m/s`} />
                  <PropRow label="Flooding fraction" value={`${(hydResult.flooding_fraction * 100).toFixed(0)}%`} />
                  <PropRow label="Design velocity" value={`${hydResult.u_design_ms.toFixed(3)} m/s`} />
                  <PropRow label="Column area" value={`${hydResult.A_column_m2.toFixed(4)} m²`} />
                  <PropRow label="Column diameter" value={`${hydResult.D_column_m.toFixed(3)} m (${hydResult.D_column_mm.toFixed(0)} mm)`} />
                  <PropRow label="ΔP/Z" value={`${hydResult.pressure_drop_Pa_m.toFixed(1)} Pa/m`} />
                  <div className="mt-2 pt-2 border-t border-surface-700/50">
                    <div className={`flex items-center gap-2 text-xs ${hydResult.wetting_adequate ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {hydResult.wetting_adequate ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
                      <span>{hydResult.wetting_adequate ? 'Wetting adequate' : 'Below min. wetting rate'}</span>
                    </div>
                  </div>
                </div>

                {/* Mass transfer */}
                <div className="panel p-4 space-y-2">
                  <p className="label text-xs mb-2">Mass Transfer</p>
                  <PropRow label="Absorption factor A" value={mtResult.absorption_factor_A.toFixed(3)} />
                  <PropRow label="N_OG (transfer units)" value={mtResult.N_OG.toFixed(3)} />
                  <PropRow label="H_G (gas HTU)" value={`${mtResult.H_G_m.toFixed(3)} m`} />
                  <PropRow label="H_L (liquid HTU)" value={`${mtResult.H_L_m.toFixed(3)} m`} />
                  <PropRow label="H_OG (overall HTU)" value={`${mtResult.H_OG_m.toFixed(3)} m`} />
                  <PropRow label="λ (stripping factor)" value={mtResult.lambda_stripping.toFixed(4)} />
                  <PropRow label="kG·a" value={`${mtResult.kG_a_per_s.toFixed(2)} s⁻¹`} />
                  <PropRow label="kL·a" value={`${mtResult.kL_a_per_s.toFixed(4)} s⁻¹`} />
                  <div className="mt-2 pt-2 border-t border-surface-700/50">
                    <div className={`flex items-center gap-2 text-xs ${mtResult.absorption_factor_A > 1.0 ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {mtResult.absorption_factor_A > 1.0 ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
                      <span>{mtResult.absorption_factor_A > 1.0 ? 'A > 1 — absorption feasible' : 'A < 1 — increase L/G'}</span>
                    </div>
                  </div>
                </div>

                {/* Column dimensions */}
                <div className="panel p-4 space-y-2">
                  <p className="label text-xs mb-2">Column Dimensions</p>
                  <PropRow label="Diameter" value={`${hydResult.D_column_m.toFixed(3)} m`} />
                  <PropRow label="Height (HTU×NTU)" value={`${mtResult.Z_htu_ntu_m.toFixed(3)} m`} />
                  <PropRow label="Height (HETP)" value={`${mtResult.Z_hetp_m.toFixed(3)} m`} />
                  <PropRow label="HETP" value={`${mtResult.HETP_m} m`} />
                  <PropRow label="Aspect ratio H/D" value={
                    hydResult.D_column_m > 0 ? (mtResult.Z_htu_ntu_m / hydResult.D_column_m).toFixed(1) : '—'
                  } />
                  <PropRow label="Total ΔP" value={
                    mtResult.total_dP_Pa !== null
                      ? `${mtResult.total_dP_Pa.toFixed(1)} Pa (${mtResult.total_dP_mbar?.toFixed(2)} mbar)`
                      : '—'
                  } />
                  <div className="mt-2 pt-2 border-t border-surface-700/50 text-[10px] text-slate-600">
                    <p>Gas flux: {mtResult.G_mass_flux.toFixed(2)} kg/(m²·s)</p>
                    <p>Liquid flux: {mtResult.L_mass_flux.toFixed(2)} kg/(m²·s)</p>
                  </div>
                </div>
              </div>

              {/* x-y diagram */}
              {chartData && (
                <div className="panel p-4">
                  <p className="label text-xs mb-3">Operating & Equilibrium Lines (x-y diagram)</p>
                  <ResponsiveContainer width="100%" height={320}>
                    <LineChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis
                        dataKey="x" type="number"
                        label={{ value: 'x (liquid mole fraction)', position: 'bottom', offset: -2, fill: '#94a3b8', fontSize: 11 }}
                        tick={{ fill: '#94a3b8', fontSize: 10 }}
                        stroke="#475569"
                        tickFormatter={(v: number) => v.toFixed(3)}
                      />
                      <YAxis
                        label={{ value: 'y (gas mole fraction)', angle: -90, position: 'insideLeft', offset: 10, fill: '#94a3b8', fontSize: 11 }}
                        tick={{ fill: '#94a3b8', fontSize: 10 }}
                        stroke="#475569"
                        tickFormatter={(v: number) => v.toFixed(3)}
                      />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 6, fontSize: 11 }}
                        labelFormatter={(v: number) => `x = ${v.toFixed(4)}`}
                        formatter={(v: number, name: string) => [v.toFixed(4), name]}
                      />
                      <Legend wrapperStyle={{ fontSize: 11 }} />
                      <Line name="Equilibrium (y* = mx)" dataKey="y_eq" stroke="#f59e0b" dot={false} strokeWidth={2} />
                      <Line name="Operating line" dataKey="y_op" stroke="#3b82f6" dot={false} strokeWidth={2} connectNulls />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}

          {/* Empty state */}
          {!hydResult && !loading && !error && (
            <div className="flex-1 flex items-center justify-center panel">
              <div className="text-center text-slate-500 py-12">
                <Columns size={32} className="mx-auto mb-3 opacity-30" />
                <p className="text-sm">Select a packing and enter design parameters</p>
                <p className="text-xs mt-1">Hydraulic sizing + mass transfer in one calculation</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
