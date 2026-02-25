import { useState, useEffect, useMemo } from 'react'
import {
  Columns, Play, AlertCircle, Loader2, ChevronRight, Info,
  CheckCircle2, AlertTriangle, X, Wind, Droplets, FlaskConical, Ruler,
} from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { useEngine } from '../hooks/useEngine'

// ─── Types ──────────────────────────────────────────────────────────────────────

interface CompactCompound {
  key: string; name: string; formula: string; mw: number; category: string
}

interface MixtureRow {
  compound: CompactCompound; molPercent: string
}

interface Packing {
  name: string; type: 'random' | 'structured'; material: string
  nominal_size_mm: number | null; specific_area: number; void_fraction: number
  packing_factor: number; hetp: number; source: string
}

interface AcidGasResult {
  name: string; formula: string; status: string
  m_eq: number | null; A_factor: number | null; NTU: number | null
  H_OG_m: number | null; Z_required_m: number | null
  enhancement_E: number; target_removal_pct: number
  removal_capped: boolean; H_pa_at_T: number | null
}

interface ExitGasRow {
  name: string; formula: string
  inlet_mol_pct: number; outlet_mol_pct: number; removal_pct: number
  absorbed_mol_s: number
}

interface ScrubberResult {
  solvent: string; packing: string; T_celsius: number; P_bar: number
  removal_target_pct: number; mixture_MW: number
  rho_G_kgm3: number; rho_L_kgm3: number
  G_mol_per_s: number; L_mol_per_s: number
  D_column_m: number; D_column_mm: number; A_column_m2: number
  Z_design_m: number; Z_hetp_m: number; dominant_component: string | null
  u_flood_ms: number; u_design_ms: number; flooding_fraction: number
  dP_per_m_Pa: number; dP_total_Pa: number; dP_total_mbar: number
  wetting_adequate: boolean
  acid_gas_analysis: AcidGasResult[]
  exit_gas: ExitGasRow[]
  total_absorbed_mol_s: number
  lines: { x_eq: number[]; y_eq: number[]; x_op: number[]; y_op: number[] } | null
}

const SOLVENT_DENSITY: Record<string, number> = {
  Water: 998, Methanol: 791, Monoethanolamine: 1012, Methyldiethanolamine: 1038,
}

const ENGINE_URL = 'http://127.0.0.1:8742'

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

function ResultCard({ label, value, unit, highlight, warn }: {
  label: string; value: string; unit?: string; highlight?: boolean; warn?: boolean
}) {
  return (
    <div className="panel p-3">
      <p className="text-slate-500 text-xs mb-1">{label}</p>
      <p className={`text-lg font-mono font-medium ${warn ? 'text-amber-400' : highlight ? 'text-primary-400' : 'text-slate-100'}`}>
        {value}{unit && <span className="text-xs text-slate-500 ml-1">{unit}</span>}
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

export function PackedColumnPage() {
  // ── Compound registry
  const [allGases, setAllGases] = useState<CompactCompound[]>([])
  const [allSolvents, setAllSolvents] = useState<CompactCompound[]>([])
  const engine = useEngine<{ categories: Record<string, { label: string; compounds: any[] }> }>()

  useEffect(() => {
    async function load() {
      const data = await engine.call('/api/compounds')
      if (!data) return
      const gas: CompactCompound[] = []
      const solv: CompactCompound[] = []
      for (const [catKey, group] of Object.entries(data.categories)) {
        for (const c of group.compounds) {
          const comp: CompactCompound = { key: c.key, name: c.name, formula: c.formula, mw: c.mw, category: catKey }
          if (catKey === 'acid_gas' || catKey === 'carrier_gas') gas.push(comp)
          else if (catKey === 'amine_solvent' || catKey === 'physical_solvent') solv.push(comp)
        }
      }
      setAllGases(gas); setAllSolvents(solv)
    }
    load()
  }, [])

  // ── Gas mixture
  const [mixture, setMixture] = useState<MixtureRow[]>([])
  const totalMol = mixture.reduce((s, r) => s + (parseFloat(r.molPercent) || 0), 0)
  const molValid = Math.abs(totalMol - 100) < 0.5
  const availableGases = allGases.filter(g => !mixture.some(r => r.compound.key === g.key))

  // ── Operating conditions
  const [gasTotalFlow, setGasTotalFlow] = useState('1.0')
  const [gasTemp, setGasTemp] = useState('40')
  const [gasPressure, setGasPressure] = useState('1.01325')

  // ── Solvent
  const [selectedSolvent, setSelectedSolvent] = useState('')
  const [solventFlow, setSolventFlow] = useState('20.0')
  const [solventMuL, setSolventMuL] = useState('1.5')
  const [solventSigma, setSolventSigma] = useState('0.072')

  // ── Packing
  const [packings, setPackings] = useState<Packing[]>([])
  const [packingsLoading, setPackingsLoading] = useState(true)
  const [filterType, setFilterType] = useState<'all' | 'random' | 'structured'>('all')
  const [selectedPacking, setSelectedPacking] = useState<Packing | null>(null)

  // ── Design
  const [removalTarget, setRemovalTarget] = useState('90')
  const [floodFrac, setFloodFrac] = useState('70')

  // ── Results
  const [result, setResult] = useState<ScrubberResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch packings
  useEffect(() => {
    async function fetchPackings() {
      setPackingsLoading(true)
      try {
        const res = await fetch(`${ENGINE_URL}/api/packings`)
        if (res.ok) {
          const data = await res.json()
          setPackings(data.packings)
          if (data.packings.length > 0) setSelectedPacking(data.packings[0])
        }
      } catch {}
      setPackingsLoading(false)
    }
    fetchPackings()
  }, [])

  // Computed
  const mixtureMW = useMemo(() =>
    mixture.reduce((s, r) => s + (parseFloat(r.molPercent) || 0) / 100 * r.compound.mw, 0)
  , [mixture])

  const rhoG = useMemo(() => {
    const T = parseFloat(gasTemp) || 40; const P = parseFloat(gasPressure) || 1.01325
    return mixtureMW > 0 ? (P * 1e5 * mixtureMW / 1000) / (8.314 * (T + 273.15)) : 1.2
  }, [mixtureMW, gasTemp, gasPressure])

  const rhoL = SOLVENT_DENSITY[selectedSolvent] ?? 998
  const solventObj = allSolvents.find(s => s.name === selectedSolvent)
  const filteredPackings = filterType === 'all' ? packings : packings.filter(p => p.type === filterType)

  // Mixture helpers
  function addGas(key: string) {
    const comp = allGases.find(g => g.key === key)
    if (!comp || mixture.some(r => r.compound.key === key)) return
    setMixture(prev => [...prev, { compound: comp, molPercent: '' }])
  }

  // Run calculation
  async function runDesign() {
    if (!selectedPacking || !selectedSolvent || mixture.length === 0 || !molValid) return
    setLoading(true); setError(null); setResult(null)
    try {
      const res = await fetch(`${ENGINE_URL}/api/column/scrubber-design`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          gas_mixture: mixture.map(r => ({ name: r.compound.name, mol_percent: parseFloat(r.molPercent) || 0 })),
          solvent_name: selectedSolvent,
          packing_name: selectedPacking.name,
          removal_target_pct: parseFloat(removalTarget),
          G_mass_kgs: parseFloat(gasTotalFlow),
          L_mass_kgs: parseFloat(solventFlow),
          T_celsius: parseFloat(gasTemp),
          P_bar: parseFloat(gasPressure),
          flooding_fraction: parseFloat(floodFrac) / 100,
          mu_L_Pas: parseFloat(solventMuL) * 1e-3,
          sigma_Nm: parseFloat(solventSigma),
          rho_L_kgm3: rhoL,
        }),
      })
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || `HTTP ${res.status}`) }
      setResult(await res.json())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Calculation failed')
    } finally { setLoading(false) }
  }

  // Chart data
  const chartData = result?.lines ? result.lines.x_eq.map((x, i) => ({
    x, y_eq: result.lines!.y_eq[i],
    y_op: i < result.lines!.x_op.length ? result.lines!.y_op[i] : null,
  })) : null

  return (
    <div className="flex flex-col h-full p-4 gap-3 overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary-600/20 rounded-lg">
          <Columns size={20} className="text-primary-400" />
        </div>
        <div>
          <h1 className="text-slate-100 font-semibold text-base">Packed Column Scrubber Design</h1>
          <p className="text-slate-500 text-xs">Define gas + solvent → get column dimensions + exit compositions</p>
        </div>
      </div>

      {/* Main layout: Left inputs, Right packing + results */}
      <div className="flex gap-4 flex-1 min-h-0">

        {/* ═══ LEFT PANEL: System Definition ═══ */}
        <div className="w-[420px] flex-shrink-0 flex flex-col gap-3 min-h-0 overflow-y-auto">

          {/* Gas Mixture */}
          <div className="panel p-3 space-y-2">
            <p className="label text-xs flex items-center gap-1.5"><Wind size={12} className="text-slate-500" /> Gas Mixture</p>
            {mixture.map(r => (
              <div key={r.compound.key} className="flex items-center gap-1.5">
                <span className={`text-xs w-36 truncate ${r.compound.category === 'acid_gas' ? 'text-red-400' : 'text-slate-300'}`}>
                  {r.compound.name} <span className="text-slate-600">({r.compound.mw})</span>
                </span>
                <input type="number" value={r.molPercent}
                  onChange={e => setMixture(prev => prev.map(x => x.compound.key === r.compound.key ? { ...x, molPercent: e.target.value } : x))}
                  placeholder="%" className="input-field py-1 text-xs w-16 text-center" min="0" max="100" step="0.1" />
                <span className="text-slate-600 text-[10px]">mol%</span>
                <button onClick={() => { setMixture(prev => prev.filter(x => x.compound.key !== r.compound.key)) }}
                  className="text-slate-600 hover:text-red-400 transition-colors"><X size={11} /></button>
              </div>
            ))}
            {mixture.length > 0 && (
              <p className={`text-[10px] ${molValid ? 'text-emerald-500' : 'text-amber-400'}`}>
                Total: {totalMol.toFixed(1)}%{!molValid && ' — must be 100%'}
              </p>
            )}
            <select value="" onChange={e => addGas(e.target.value)} className="input-field py-1 text-xs w-full">
              <option value="">+ Add component…</option>
              {availableGases.map(g => (
                <option key={g.key} value={g.key}>{g.name} ({g.formula}, {g.mw}) — {g.category === 'acid_gas' ? 'acid gas' : 'carrier'}</option>
              ))}
            </select>
            {mixtureMW > 0 && (
              <p className="text-[10px] text-slate-600">MW<sub>mix</sub>={mixtureMW.toFixed(2)} · ρ<sub>G</sub>≈{rhoG.toFixed(3)} kg/m³</p>
            )}
          </div>

          {/* Solvent */}
          <div className="panel p-3 space-y-2">
            <p className="label text-xs flex items-center gap-1.5"><Droplets size={12} className="text-slate-500" /> Solvent</p>
            <select value={selectedSolvent} onChange={e => setSelectedSolvent(e.target.value)} className="input-field py-1.5 text-xs w-full">
              <option value="">Select solvent…</option>
              {allSolvents.map(s => (
                <option key={s.key} value={s.name}>{s.name} ({s.formula}, MW={s.mw})</option>
              ))}
            </select>
            {selectedSolvent && (
              <div className="grid grid-cols-3 gap-2">
                <Field label="L flow" hint="kg/s">
                  <input type="number" value={solventFlow} onChange={e => setSolventFlow(e.target.value)} className="input-field w-full py-1 text-xs" step="0.5" />
                </Field>
                <Field label="μ_L" hint="mPa·s">
                  <input type="number" value={solventMuL} onChange={e => setSolventMuL(e.target.value)} className="input-field w-full py-1 text-xs" step="0.1" />
                </Field>
                <Field label="σ" hint="N/m">
                  <input type="number" value={solventSigma} onChange={e => setSolventSigma(e.target.value)} className="input-field w-full py-1 text-xs" step="0.001" />
                </Field>
              </div>
            )}
          </div>

          {/* Packing selector */}
          <div className="panel p-3">
            <div className="flex items-center gap-2 mb-2">
              <p className="label text-xs">Packing</p>
              <div className="flex gap-1 ml-auto">
                {(['all', 'random', 'structured'] as const).map(t => (
                  <button key={t} onClick={() => setFilterType(t)}
                    className={`px-2 py-1 rounded text-[10px] font-medium ${filterType === t ? 'bg-primary-600/20 text-primary-400' : 'text-slate-500 hover:text-slate-300'}`}>
                    {t === 'all' ? 'All' : t.charAt(0).toUpperCase() + t.slice(1)}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex gap-2 overflow-x-auto pb-1">
              {packingsLoading ? (
                <div className="text-slate-500 text-xs py-2"><Loader2 size={12} className="animate-spin inline mr-1" />Loading…</div>
              ) : filteredPackings.map(p => (
                <button key={p.name} onClick={() => setSelectedPacking(p)}
                  className={`flex-shrink-0 px-3 py-2 rounded-lg border text-left transition-colors ${
                    selectedPacking?.name === p.name
                      ? 'border-primary-500 bg-primary-600/10'
                      : 'border-surface-600 hover:border-surface-500 bg-surface-800/50'
                  }`}>
                  <p className={`text-xs font-medium ${selectedPacking?.name === p.name ? 'text-primary-400' : 'text-slate-200'}`}>{p.name}</p>
                  <p className="text-[10px] text-slate-500">{p.type} · F<sub>p</sub>={p.packing_factor} · HETP={p.hetp}m</p>
                </button>
              ))}
            </div>
          </div>

          {/* Operating Conditions */}
          <div className="panel p-3 space-y-2">
            <p className="label text-xs flex items-center gap-1.5"><Info size={12} className="text-slate-500" /> Operating Conditions</p>
            <div className="grid grid-cols-3 gap-2">
              <Field label="G flow" hint="kg/s">
                <input type="number" value={gasTotalFlow} onChange={e => setGasTotalFlow(e.target.value)} className="input-field w-full py-1 text-xs" step="0.1" />
              </Field>
              <Field label="T" hint="°C">
                <input type="number" value={gasTemp} onChange={e => setGasTemp(e.target.value)} className="input-field w-full py-1 text-xs" />
              </Field>
              <Field label="P" hint="bar">
                <input type="number" value={gasPressure} onChange={e => setGasPressure(e.target.value)} className="input-field w-full py-1 text-xs" step="0.01" />
              </Field>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Field label="Removal target" hint="%">
                <input type="number" value={removalTarget} onChange={e => setRemovalTarget(e.target.value)} className="input-field w-full py-1 text-xs" min="10" max="99.9" step="5" />
              </Field>
              <Field label="Flooding frac." hint="%">
                <input type="number" value={floodFrac} onChange={e => setFloodFrac(e.target.value)} className="input-field w-full py-1 text-xs" min="30" max="95" step="5" />
              </Field>
            </div>
          </div>

          {/* Calculate */}
          <button className="btn-primary w-full flex items-center justify-center gap-2 py-2"
            onClick={runDesign}
            disabled={loading || !selectedPacking || !selectedSolvent || mixture.length === 0 || !molValid}>
            {loading ? <><Loader2 size={14} className="animate-spin" /> Calculating…</> : <><Play size={14} /> Design Scrubber</>}
          </button>

          {error && (
            <div className="flex items-start gap-2 text-red-400 text-xs bg-red-500/10 p-2 rounded">
              <AlertCircle size={14} className="mt-0.5 flex-shrink-0" />{error}
            </div>
          )}
        </div>

        {/* ═══ RIGHT PANEL: Results ═══ */}
        <div className="flex-1 flex flex-col gap-3 min-w-0 min-h-0 overflow-y-auto">

          {/* ── Results ── */}
          {result ? (
            <div className="space-y-3">
              {/* Headline cards */}
              <div className="grid grid-cols-5 gap-2">
                <ResultCard label="Diameter" value={result.D_column_m >= 1 ? result.D_column_m.toFixed(2) : result.D_column_mm.toFixed(0)} unit={result.D_column_m >= 1 ? 'm' : 'mm'} highlight />
                <ResultCard label="Packed Height" value={result.Z_design_m.toFixed(2)} unit="m" highlight />
                <ResultCard label="Height (HETP)" value={result.Z_hetp_m.toFixed(2)} unit="m" />
                <ResultCard label="Total ΔP" value={result.dP_total_mbar.toFixed(1)} unit="mbar" />
                <ResultCard label="Absorbed" value={result.total_absorbed_mol_s.toFixed(3)} unit="mol/s" />
              </div>

              {/* Exit gas composition table */}
              <div className="panel p-4">
                <p className="label text-xs mb-2">Exit Gas Composition</p>
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-surface-700">
                      <th className="text-left text-slate-500 py-1.5 font-medium">Component</th>
                      <th className="text-right text-slate-500 py-1.5 font-medium">Inlet (mol%)</th>
                      <th className="text-right text-slate-500 py-1.5 font-medium">Outlet (mol%)</th>
                      <th className="text-right text-slate-500 py-1.5 font-medium">Removal</th>
                      <th className="text-right text-slate-500 py-1.5 font-medium">Absorbed (mol/s)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.exit_gas.map(g => (
                      <tr key={g.name} className="border-b border-surface-700/50">
                        <td className="py-1.5 text-slate-200">{g.name} <span className="text-slate-600">{g.formula}</span></td>
                        <td className="text-right font-mono text-slate-300">{g.inlet_mol_pct.toFixed(2)}</td>
                        <td className="text-right font-mono text-slate-100">{g.outlet_mol_pct.toFixed(3)}</td>
                        <td className={`text-right font-mono ${g.removal_pct > 50 ? 'text-emerald-400' : g.removal_pct > 0 ? 'text-amber-400' : 'text-slate-500'}`}>
                          {g.removal_pct > 0 ? `${g.removal_pct.toFixed(1)}%` : '—'}
                        </td>
                        <td className="text-right font-mono text-slate-400">
                          {g.absorbed_mol_s > 0 ? g.absorbed_mol_s.toFixed(4) : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Per-acid-gas analysis + Column details side by side */}
              <div className="grid grid-cols-2 gap-3">
                {/* Acid gas analysis */}
                <div className="panel p-4 space-y-2">
                  <p className="label text-xs mb-2">Acid Gas Analysis</p>
                  {result.acid_gas_analysis.filter(a => a.status === 'calculated').map(a => (
                    <div key={a.name} className="pb-2 border-b border-surface-700/50 last:border-0 last:pb-0">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-red-400 font-medium">{a.name}</span>
                        {a.removal_capped && (
                          <span className="text-[9px] px-1.5 py-0.5 bg-amber-500/10 text-amber-400 rounded">A&lt;1 — removal capped</span>
                        )}
                      </div>
                      <div className="grid grid-cols-2 gap-x-4 text-[11px]">
                        <PropRow label="m (equil.)" value={a.m_eq?.toFixed(4) ?? '—'} />
                        <PropRow label="A (absorption)" value={a.A_factor?.toFixed(3) ?? '—'} />
                        <PropRow label="Enhancement E" value={a.enhancement_E.toString()} />
                        <PropRow label="N_OG" value={a.NTU?.toFixed(3) ?? '—'} />
                        <PropRow label="H_OG" value={a.H_OG_m ? `${a.H_OG_m.toFixed(3)} m` : '—'} />
                        <PropRow label="Z required" value={a.Z_required_m ? `${a.Z_required_m.toFixed(3)} m` : '—'} />
                      </div>
                    </div>
                  ))}
                  {result.dominant_component && (
                    <p className="text-[10px] text-primary-400 mt-1">
                      Controlling component: {result.dominant_component}
                    </p>
                  )}
                </div>

                {/* Column details */}
                <div className="panel p-4 space-y-2">
                  <p className="label text-xs mb-2">Column Details</p>
                  <PropRow label="Packing" value={result.packing} />
                  <PropRow label="Diameter" value={`${result.D_column_m.toFixed(3)} m (${result.D_column_mm.toFixed(0)} mm)`} />
                  <PropRow label="Packed height" value={`${result.Z_design_m.toFixed(3)} m`} />
                  <PropRow label="H/D ratio" value={result.D_column_m > 0 ? (result.Z_design_m / result.D_column_m).toFixed(1) : '—'} />
                  <PropRow label="u_flood" value={`${result.u_flood_ms.toFixed(3)} m/s`} />
                  <PropRow label="u_design" value={`${result.u_design_ms.toFixed(3)} m/s`} />
                  <PropRow label="ΔP/Z" value={`${result.dP_per_m_Pa.toFixed(1)} Pa/m`} />
                  <PropRow label="Total ΔP" value={`${result.dP_total_mbar.toFixed(2)} mbar`} />
                  <div className="mt-2 pt-2 border-t border-surface-700/50">
                    <div className={`flex items-center gap-2 text-xs ${result.wetting_adequate ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {result.wetting_adequate ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
                      <span>{result.wetting_adequate ? 'Wetting adequate' : 'Below min. wetting rate'}</span>
                    </div>
                  </div>
                  <div className="text-[10px] text-slate-600 mt-1">
                    <p>MW<sub>mix</sub>={result.mixture_MW.toFixed(2)} · ρ<sub>G</sub>={result.rho_G_kgm3.toFixed(3)} kg/m³</p>
                    <p>G={result.G_mol_per_s.toFixed(1)} mol/s · L={result.L_mol_per_s.toFixed(1)} mol/s</p>
                  </div>
                </div>
              </div>

              {/* Operating/equilibrium line chart */}
              {chartData && (
                <div className="panel p-4">
                  <p className="label text-xs mb-2">
                    Operating & Equilibrium Lines
                    {result.dominant_component && <span className="text-slate-600 ml-1">({result.dominant_component})</span>}
                  </p>
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="x" type="number"
                        label={{ value: 'x (liquid)', position: 'bottom', offset: -2, fill: '#94a3b8', fontSize: 11 }}
                        tick={{ fill: '#94a3b8', fontSize: 10 }} stroke="#475569"
                        tickFormatter={(v: number) => v.toFixed(3)} />
                      <YAxis
                        label={{ value: 'y (gas)', angle: -90, position: 'insideLeft', offset: 10, fill: '#94a3b8', fontSize: 11 }}
                        tick={{ fill: '#94a3b8', fontSize: 10 }} stroke="#475569"
                        tickFormatter={(v: number) => v.toFixed(3)} />
                      <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 6, fontSize: 11 }}
                        labelFormatter={(v: number) => `x = ${v.toFixed(4)}`}
                        formatter={(v: number, name: string) => [v.toFixed(4), name]} />
                      <Legend wrapperStyle={{ fontSize: 11 }} />
                      <Line name="Equilibrium (y*=mx)" dataKey="y_eq" stroke="#f59e0b" dot={false} strokeWidth={2} />
                      <Line name="Operating line" dataKey="y_op" stroke="#3b82f6" dot={false} strokeWidth={2} connectNulls />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          ) : !loading && !error ? (
            <div className="flex-1 flex items-center justify-center panel">
              <div className="text-center text-slate-500 py-16">
                <Columns size={36} className="mx-auto mb-3 opacity-30" />
                <p className="text-sm">Define your gas mixture and solvent</p>
                <p className="text-xs mt-1">Then select a packing and click Design Scrubber</p>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
