import { useState, useEffect } from 'react'
import {
  FlaskConical,
  Play,
  AlertCircle,
  AlertTriangle,
  Loader2,
  ChevronRight,
  Info,
  Beaker,
  Thermometer,
  Shield,
  Droplets,
  ArrowRight,
  Columns,
  X,
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
  ReferenceDot,
} from 'recharts'
import { useEngine } from '../hooks/useEngine'

// ─── Types ──────────────────────────────────────────────────────────────────────

interface BubbleDewResult {
  component: string
  temperature_c: number
  pressure_bar: number
  bubble_temperature_c: number
  dew_temperature_c: number
  bubble_pressure_bar: number
  saturation_pressure_bar: number
  warning?: string
}

interface TxyResult {
  comp1: string
  comp2: string
  pressure_bar: number
  x1: number[]
  y1: number[]
  T_celsius: number[]
}

interface PxyResult {
  comp1: string
  comp2: string
  T_celsius: number
  x1: number[]
  y1: number[]
  P_bar: number[]
}

type Mode = 'pure' | 'binary' | 'scrubbing'
type BinarySpec = 'pressure' | 'temperature'
type ScrubbingFamily = 'electrolyte' | 'amine'
type ElectrolyteSpec = 'pressure' | 'temperature'

interface ElectrolyteSolute {
  id: string
  name: string
  formula: string
  mw: number
  max_wt_pct: number
}

interface BpeCurveResult {
  solute: string
  solute_name: string
  formula: string
  P_pa: number
  T_water: number
  w_percent: number[]
  T_boil: number[]
  bpe: number[]
  pressure_bar: number
}

interface VpCurveResult {
  solute: string
  solute_name: string
  formula: string
  T_celsius: number
  P_pure_water: number
  w_percent: number[]
  P_water: number[]
  vpd: number[]
}

interface OperatingPointResult {
  solute: string
  solute_name: string
  formula: string
  w_percent: number
  T_boil_celsius: number
  P_water_pa: number
  P_water_kpa: number
  bpe_celsius: number
  water_activity: number
  P_total_pa: number | null
}

// ─── Compound Registry Types ────────────────────────────────────────────────────

interface CompoundInfo {
  key: string
  name: string
  formula: string
  cas: string
  mw: number
  category: string
  description: string
  boiling_point_c: number | null
  antoine: { A: number; B: number; C: number; T_min: number; T_max: number } | null
  critical: { Tc_celsius: number; Pc_bar: number } | null
}

interface CategoryGroup {
  label: string
  order: number
  compounds: CompoundInfo[]
}

// Category colors/icons for visual distinction
const CATEGORY_STYLE: Record<string, { color: string; bg: string }> = {
  acid_gas:         { color: 'text-red-400',    bg: 'bg-red-500/10' },
  amine_solvent:    { color: 'text-blue-400',   bg: 'bg-blue-500/10' },
  physical_solvent: { color: 'text-cyan-400',   bg: 'bg-cyan-500/10' },
  carrier_gas:      { color: 'text-slate-400',  bg: 'bg-slate-500/10' },
  organic:          { color: 'text-amber-400',  bg: 'bg-amber-500/10' },
}

// Binary pairs are now fetched dynamically from /api/vle/binary/pairs

// ─── Main Component ─────────────────────────────────────────────────────────────

interface VLECalculatorPageProps {
  onSendToColumnDesign?: (preset: import('../App').ColumnDesignPreset) => void
}

export function VLECalculatorPage({ onSendToColumnDesign }: VLECalculatorPageProps) {
  const [mode, setMode] = useState<Mode>('pure')

  return (
    <div className="flex flex-col h-full p-4 gap-4 overflow-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary-600/20 rounded-lg">
            <FlaskConical size={20} className="text-primary-400" />
          </div>
          <div>
            <h1 className="text-slate-100 font-semibold text-base">
              VLE Calculator
            </h1>
            <p className="text-slate-500 text-xs">
              Vapor-Liquid Equilibrium — bubble point, dew point & phase diagrams
            </p>
          </div>
        </div>

        {/* Mode Tabs */}
        <div className="flex bg-surface-800 border border-surface-600 rounded-lg p-0.5">
          <button
            onClick={() => setMode('pure')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              mode === 'pure'
                ? 'bg-primary-600/20 text-primary-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Pure Component
          </button>
          <button
            onClick={() => setMode('binary')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              mode === 'binary'
                ? 'bg-primary-600/20 text-primary-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Binary Mixture
          </button>
          <button
            onClick={() => setMode('scrubbing')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              mode === 'scrubbing'
                ? 'bg-primary-600/20 text-primary-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Scrubbing Solvents
          </button>
        </div>
      </div>

      {/* System Builder — send gas + solvent to Column Design */}
      {onSendToColumnDesign && (
        <SystemBuilder onSend={onSendToColumnDesign} />
      )}

      {/* Body */}
      {mode === 'pure' ? (
        <PureComponentView />
      ) : mode === 'binary' ? (
        <BinaryMixtureView />
      ) : (
        <ScrubbingSolventView />
      )}
    </div>
  )
}

// ─── Pure Component View ────────────────────────────────────────────────────────

function PureComponentView() {
  const [categories, setCategories] = useState<Record<string, CategoryGroup>>({})
  const [allCompounds, setAllCompounds] = useState<CompoundInfo[]>([])
  const [selected, setSelected] = useState<CompoundInfo | null>(null)
  const [activeCategory, setActiveCategory] = useState<string>('acid_gas')
  const [temperature, setTemperature] = useState('25')
  const [pressure, setPressure] = useState('1.01325')
  const [result, setResult] = useState<BubbleDewResult | null>(null)
  const [fetchError, setFetchError] = useState<string | null>(null)

  const { loading, error, call } = useEngine<BubbleDewResult>()

  // Fetch compound registry on mount
  useEffect(() => {
    fetch('http://localhost:8742/api/compounds')
      .then((r) => r.json())
      .then((data) => {
        setCategories(data.categories)
        setAllCompounds(data.compounds)
        // Select first acid gas by default
        const firstGas = data.categories?.acid_gas?.compounds?.[0]
        if (firstGas) setSelected(firstGas)
      })
      .catch((e) => setFetchError(e.message))
  }, [])

  async function handleCalculate() {
    if (!selected) return
    const data = await call('/api/vle/bubble-dew', {
      component: selected.key,
      temperature_c: parseFloat(temperature),
      pressure_bar: parseFloat(pressure),
    })
    if (data) setResult(data)
  }

  // Sorted category keys
  const sortedCats = Object.entries(categories)
    .sort(([, a], [, b]) => a.order - b.order)
    .map(([key]) => key)

  const currentCatCompounds = categories[activeCategory]?.compounds ?? []

  if (fetchError) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <ErrorMessage message={`Failed to load compounds: ${fetchError}`} />
      </div>
    )
  }

  return (
    <div className="flex gap-4 flex-1 min-h-0">
      {/* Left: Compound Browser */}
      <div className="w-72 flex-shrink-0 flex flex-col gap-3 min-h-0">
        {/* Category tabs */}
        <div className="panel p-2 flex flex-wrap gap-1">
          {sortedCats.map((catKey) => {
            const cat = categories[catKey]
            const style = CATEGORY_STYLE[catKey] ?? CATEGORY_STYLE.organic
            const isActive = catKey === activeCategory
            return (
              <button
                key={catKey}
                onClick={() => setActiveCategory(catKey)}
                className={`px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
                  isActive
                    ? `${style.bg} ${style.color} ring-1 ring-current/30`
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {cat.label}
              </button>
            )
          })}
        </div>

        {/* Compound list */}
        <div className="panel flex-1 overflow-y-auto min-h-0">
          {currentCatCompounds.map((comp) => {
            const isSelected = selected?.key === comp.key
            return (
              <button
                key={comp.key}
                onClick={() => {
                  setSelected(comp)
                  setResult(null)
                }}
                className={`w-full text-left px-3 py-2.5 border-b border-surface-700/50 transition-colors ${
                  isSelected
                    ? 'bg-primary-600/10 border-l-2 border-l-primary-500'
                    : 'hover:bg-surface-700/30 border-l-2 border-l-transparent'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p
                      className={`text-sm font-medium ${
                        isSelected ? 'text-primary-400' : 'text-slate-200'
                      }`}
                    >
                      {comp.name}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {comp.formula} · MW {comp.mw}
                    </p>
                  </div>
                  {isSelected && (
                    <ChevronRight size={12} className="text-primary-500" />
                  )}
                </div>
              </button>
            )
          })}
        </div>

        {/* Calculator */}
        <div className="panel p-3 space-y-3">
          <p className="label text-xs">Quick Calculate</p>
          <Field label="Temperature">
            <div className="flex gap-2">
              <input
                type="number"
                value={temperature}
                onChange={(e) => setTemperature(e.target.value)}
                className="input-field flex-1"
                step="1"
              />
              <Unit>°C</Unit>
            </div>
          </Field>
          <Field label="Pressure">
            <div className="flex gap-2">
              <input
                type="number"
                value={pressure}
                onChange={(e) => setPressure(e.target.value)}
                className="input-field flex-1"
                step="0.1"
              />
              <Unit>bar</Unit>
            </div>
          </Field>
          <button
            onClick={handleCalculate}
            disabled={loading || !selected}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 size={14} className="animate-spin" /> Calculating…
              </>
            ) : (
              <>
                <Play size={14} /> Calculate
              </>
            )}
          </button>
          <ErrorMessage message={error} />
        </div>
      </div>

      {/* Right: Property Card */}
      <div className="flex-1 panel p-0 flex flex-col min-w-0 min-h-0 overflow-y-auto">
        {selected ? (
          <CompoundPropertyCard
            compound={selected}
            result={result}
          />
        ) : (
          <EmptyState message="Select a component to view properties" />
        )}
      </div>
    </div>
  )
}

// ─── Compound Property Card ────────────────────────────────────────────────────

function CompoundPropertyCard({
  compound,
  result,
}: {
  compound: CompoundInfo
  result: BubbleDewResult | null
}) {
  const style = CATEGORY_STYLE[compound.category] ?? CATEGORY_STYLE.organic

  return (
    <div className="flex flex-col gap-0">
      {/* Header */}
      <div className="px-5 py-4 border-b border-surface-700/50">
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg ${style.bg}`}>
            <FlaskConical size={20} className={style.color} />
          </div>
          <div className="flex-1">
            <h2 className="text-slate-100 font-semibold text-base">
              {compound.name}
            </h2>
            <p className="text-slate-500 text-sm mt-0.5">
              {compound.formula} · CAS {compound.cas}
            </p>
            <p className="text-slate-500 text-xs mt-1 leading-relaxed">
              {compound.description}
            </p>
          </div>
        </div>
      </div>

      {/* Basic Properties */}
      <PropertySection icon={<Info size={14} />} title="Basic Properties">
        <PropGrid>
          <PropCell label="Molecular Weight" value={`${compound.mw} g/mol`} />
          <PropCell label="Formula" value={compound.formula} />
          <PropCell label="CAS Number" value={compound.cas} />
          <PropCell
            label="Normal Boiling Point"
            value={
              compound.boiling_point_c !== null
                ? `${compound.boiling_point_c.toFixed(1)} °C`
                : '—'
            }
          />
          {compound.critical && (
            <>
              <PropCell
                label="Critical Temperature"
                value={`${compound.critical.Tc_celsius.toFixed(1)} °C`}
              />
              <PropCell
                label="Critical Pressure"
                value={`${compound.critical.Pc_bar.toFixed(2)} bar`}
              />
            </>
          )}
        </PropGrid>
      </PropertySection>

      {/* Thermodynamic Data */}
      <PropertySection icon={<Thermometer size={14} />} title="Thermodynamic Data">
        {compound.antoine ? (
          <PropGrid>
            <PropCell label="Antoine A" value={compound.antoine.A.toFixed(4)} />
            <PropCell label="Antoine B" value={compound.antoine.B.toFixed(3)} />
            <PropCell label="Antoine C" value={compound.antoine.C.toFixed(3)} />
            <PropCell
              label="Valid Range"
              value={`${compound.antoine.T_min} to ${compound.antoine.T_max} °C`}
            />
          </PropGrid>
        ) : (
          <p className="text-slate-500 text-xs">No Antoine data available</p>
        )}
      </PropertySection>

      {/* Calculation Results (if available) */}
      {result && (
        <PropertySection icon={<Beaker size={14} />} title="Calculation Results">
          <PropGrid>
            <PropCell
              label={`Boiling Point at ${result.pressure_bar} bar`}
              value={`${result.bubble_temperature_c.toFixed(2)} °C`}
              highlight
            />
            <PropCell
              label={`Saturation Pressure at ${result.temperature_c} °C`}
              value={`${result.saturation_pressure_bar.toFixed(4)} bar`}
              highlight
            />
          </PropGrid>
          {result.warning && <WarningMessage message={result.warning} />}
        </PropertySection>
      )}

      {/* Transport Properties (placeholder) */}
      <PropertySection icon={<Droplets size={14} />} title="Transport Properties">
        <p className="text-slate-600 text-xs italic">
          Density, viscosity, heat capacity, diffusivity — coming in Phase B
        </p>
      </PropertySection>

      {/* Safety (placeholder) */}
      <PropertySection icon={<Shield size={14} />} title="Safety & Regulatory">
        <p className="text-slate-600 text-xs italic">
          NFPA diamond, TLV/TWA, exposure limits — coming in Phase C
        </p>
      </PropertySection>
    </div>
  )
}

function PropertySection({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="px-5 py-3 border-b border-surface-700/50">
      <div className="flex items-center gap-2 mb-2.5">
        <span className="text-slate-400">{icon}</span>
        <p className="text-slate-300 text-sm font-medium">{title}</p>
      </div>
      {children}
    </div>
  )
}

function PropGrid({ children }: { children: React.ReactNode }) {
  return <div className="grid grid-cols-2 gap-x-6 gap-y-2">{children}</div>
}

function PropCell({
  label,
  value,
  highlight = false,
}: {
  label: string
  value: string
  highlight?: boolean
}) {
  return (
    <div>
      <p className="text-slate-500 text-xs">{label}</p>
      <p
        className={`text-sm font-mono mt-0.5 ${
          highlight ? 'text-primary-400 font-medium' : 'text-slate-200'
        }`}
      >
        {value}
      </p>
    </div>
  )
}

// ─── Binary Mixture View ────────────────────────────────────────────────────────

function BinaryMixtureView() {
  const [pairIndex, setPairIndex] = useState(0)
  const [pairs, setPairs] = useState<{ comp1: string; comp2: string; label: string }[]>([])
  const [pairsError, setPairsError] = useState<string | null>(null)
  const [spec, setSpec] = useState<BinarySpec>('pressure')
  const [pressure, setPressure] = useState('1.01325')
  const [temperature, setTemperature] = useState('80')
  const [txyData, setTxyData] = useState<TxyResult | null>(null)
  const [pxyData, setPxyData] = useState<PxyResult | null>(null)

  const { loading, error, call } = useEngine<TxyResult | PxyResult>()

  // Fetch available binary pairs from the engine DB
  useEffect(() => {
    fetch('http://localhost:8742/api/vle/binary/pairs')
      .then((r) => r.json())
      .then((data) => {
        const ps = (data.pairs ?? []).map((p: any) => ({
          comp1: String(p.comp1),
          comp2: String(p.comp2),
          label: `${String(p.comp1)} / ${String(p.comp2)}`,
        }))
        setPairs(ps)
        setPairIndex(0)
      })
      .catch((e) => setPairsError(e.message))
  }, [])

  const pair = pairs[pairIndex]

  async function handleGenerate() {
    if (!pair) return
    if (spec === 'pressure') {
      const data = await call('/api/vle/binary/txy', {
        comp1: pair.comp1,
        comp2: pair.comp2,
        pressure_bar: parseFloat(pressure),
        n_points: 51,
      })
      if (data) {
        setTxyData(data as TxyResult)
        setPxyData(null)
      }
    } else {
      const data = await call('/api/vle/binary/pxy', {
        comp1: pair.comp1,
        comp2: pair.comp2,
        temperature_c: parseFloat(temperature),
        n_points: 51,
      })
      if (data) {
        setPxyData(data as PxyResult)
        setTxyData(null)
      }
    }
  }

  // Active diagram data
  const isTxy = spec === 'pressure' && txyData != null
  const isPxy = spec === 'temperature' && pxyData != null
  const activeData = isTxy ? txyData : isPxy ? pxyData : null

  // ── Txy chart data ──
  const txyChartData = (() => {
    if (!txyData) return []
    const bubbleCurve = txyData.x1.map((x, i) => ({
      composition: parseFloat(x.toFixed(4)),
      T: parseFloat(txyData.T_celsius[i].toFixed(2)),
    }))
    const dewCurve = txyData.y1.map((y, i) => ({
      composition: parseFloat((y as number).toFixed(4)),
      T: parseFloat(txyData.T_celsius[i].toFixed(2)),
    }))
    const compositionSet = new Set<number>()
    bubbleCurve.forEach((p) => compositionSet.add(p.composition))
    dewCurve.forEach((p) => compositionSet.add(p.composition))
    const allComps = Array.from(compositionSet).sort((a, b) => a - b)
    const bubbleMap = new Map(bubbleCurve.map((p) => [p.composition, p.T]))
    const dewMap = new Map(dewCurve.map((p) => [p.composition, p.T]))
    return allComps.map((z) => ({
      z,
      Bubble: bubbleMap.get(z) ?? null,
      Dew: dewMap.get(z) ?? null,
    }))
  })()

  // ── Pxy chart data ──
  const pxyChartData = (() => {
    if (!pxyData) return []
    const bubbleCurve = pxyData.x1.map((x, i) => ({
      composition: parseFloat(x.toFixed(4)),
      P: parseFloat(pxyData.P_bar[i].toFixed(5)),
    }))
    const dewCurve = pxyData.y1.map((y, i) => ({
      composition: parseFloat((y as number).toFixed(4)),
      P: parseFloat(pxyData.P_bar[i].toFixed(5)),
    }))
    const compositionSet = new Set<number>()
    bubbleCurve.forEach((p) => compositionSet.add(p.composition))
    dewCurve.forEach((p) => compositionSet.add(p.composition))
    const allComps = Array.from(compositionSet).sort((a, b) => a - b)
    const bubbleMap = new Map(bubbleCurve.map((p) => [p.composition, p.P]))
    const dewMap = new Map(dewCurve.map((p) => [p.composition, p.P]))
    return allComps.map((z) => ({
      z,
      Bubble: bubbleMap.get(z) ?? null,
      Dew: dewMap.get(z) ?? null,
    }))
  })()

  // ── xy chart data (works for both modes) ──
  const xyChartData = (() => {
    if (!activeData) return []
    return activeData.x1.map((x, i) => ({
      x: parseFloat(x.toFixed(4)),
      y: parseFloat(activeData.y1[i].toFixed(4)),
      diagonal: parseFloat(x.toFixed(4)),
    }))
  })()

  const comp1Label = activeData?.comp1 ?? pair?.comp1 ?? ''

  return (
    <div className="flex gap-4 flex-1 min-h-0">
      {/* Inputs */}
      <div className="w-72 flex-shrink-0 space-y-4">
        <div className="panel p-4 space-y-4">
          <p className="label">Binary System</p>

          {pairsError ? (
            <ErrorMessage message={`Failed to load binary pairs: ${pairsError}`} />
          ) : null}

          <Field label="Component Pair">
            <select
              value={pairIndex}
              onChange={(e) => setPairIndex(Number(e.target.value))}
              className="input-field w-full"
              disabled={pairs.length === 0}
            >
              {pairs.map((p, i) => (
                <option key={i} value={i}>
                  {p.label}
                </option>
              ))}
            </select>
          </Field>

          {/* Spec Toggle */}
          <Field label="Specify">
            <div className="flex bg-surface-700 border border-surface-500 rounded-md p-0.5">
              <button
                onClick={() => setSpec('pressure')}
                className={`flex-1 px-2 py-1.5 rounded text-xs font-medium transition-colors ${
                  spec === 'pressure'
                    ? 'bg-primary-600/20 text-primary-400'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Pressure (Txy)
              </button>
              <button
                onClick={() => setSpec('temperature')}
                className={`flex-1 px-2 py-1.5 rounded text-xs font-medium transition-colors ${
                  spec === 'temperature'
                    ? 'bg-primary-600/20 text-primary-400'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Temperature (Pxy)
              </button>
            </div>
          </Field>

          {/* Conditional Input */}
          {spec === 'pressure' ? (
            <Field label="System Pressure">
              <div className="flex gap-2">
                <input
                  type="number"
                  value={pressure}
                  onChange={(e) => setPressure(e.target.value)}
                  className="input-field flex-1"
                  step="0.1"
                />
                <Unit>bar</Unit>
              </div>
            </Field>
          ) : (
            <Field label="System Temperature">
              <div className="flex gap-2">
                <input
                  type="number"
                  value={temperature}
                  onChange={(e) => setTemperature(e.target.value)}
                  className="input-field flex-1"
                  step="1"
                />
                <Unit>°C</Unit>
              </div>
            </Field>
          )}

          <button
            onClick={handleGenerate}
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 size={14} className="animate-spin" /> Generating…
              </>
            ) : (
              <>
                <Play size={14} /> Generate Diagram
              </>
            )}
          </button>

          <ErrorMessage message={error} />
        </div>

        {/* Summary */}
        {activeData && (
          <div className="panel p-4 space-y-3">
            <p className="label">System Summary</p>
            <ResultRow label="Component 1" value={activeData.comp1} />
            <ResultRow label="Component 2" value={activeData.comp2} />
            {isTxy && txyData && (
              <>
                <ResultRow
                  label="Pressure"
                  value={`${txyData.pressure_bar} bar`}
                />
                <ResultRow
                  label="T at x₁=0 (pure 2)"
                  value={`${txyData.T_celsius[0].toFixed(2)} °C`}
                />
                <ResultRow
                  label="T at x₁=1 (pure 1)"
                  value={`${txyData.T_celsius[txyData.T_celsius.length - 1].toFixed(2)} °C`}
                />
              </>
            )}
            {isPxy && pxyData && (
              <>
                <ResultRow
                  label="Temperature"
                  value={`${pxyData.T_celsius} °C`}
                />
                <ResultRow
                  label="P at x₁=0 (pure 2)"
                  value={`${pxyData.P_bar[0].toFixed(4)} bar`}
                />
                <ResultRow
                  label="P at x₁=1 (pure 1)"
                  value={`${pxyData.P_bar[pxyData.P_bar.length - 1].toFixed(4)} bar`}
                />
              </>
            )}
          </div>
        )}
      </div>

      {/* Charts */}
      <div className="flex-1 flex flex-col gap-4 min-w-0">
        {/* Phase Diagram (Txy or Pxy) */}
        <div className="flex-1 panel p-4 flex flex-col min-h-0">
          <p className="label mb-3">
            {isTxy ? 'Txy Diagram' : isPxy ? 'Pxy Diagram' : 'Phase Diagram'}
          </p>
          {isTxy && txyChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={txyChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                <XAxis
                  dataKey="z"
                  type="number"
                  domain={[0, 1]}
                  stroke="#484f58"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  label={{
                    value: `Mole fraction ${comp1Label}`,
                    position: 'insideBottom',
                    offset: -5,
                    fill: '#64748b',
                    fontSize: 11,
                  }}
                />
                <YAxis
                  stroke="#484f58"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  label={{
                    value: 'Temperature (°C)',
                    angle: -90,
                    position: 'insideLeft',
                    offset: 10,
                    fill: '#64748b',
                    fontSize: 11,
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1c2128',
                    border: '1px solid #30363d',
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                  labelFormatter={(v) => `z = ${v}`}
                />
                <Legend
                  wrapperStyle={{ paddingTop: 8, fontSize: 12, color: '#94a3b8' }}
                />
                <Line
                  type="monotone"
                  dataKey="Bubble"
                  stroke="#14b8a6"
                  strokeWidth={2}
                  dot={false}
                  name="Bubble (liquid)"
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="Dew"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={false}
                  name="Dew (vapor)"
                  connectNulls
                />
              </LineChart>
            </ResponsiveContainer>
          ) : isPxy && pxyChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={pxyChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                <XAxis
                  dataKey="z"
                  type="number"
                  domain={[0, 1]}
                  stroke="#484f58"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  label={{
                    value: `Mole fraction ${comp1Label}`,
                    position: 'insideBottom',
                    offset: -5,
                    fill: '#64748b',
                    fontSize: 11,
                  }}
                />
                <YAxis
                  stroke="#484f58"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  label={{
                    value: 'Pressure (bar)',
                    angle: -90,
                    position: 'insideLeft',
                    offset: 10,
                    fill: '#64748b',
                    fontSize: 11,
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1c2128',
                    border: '1px solid #30363d',
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                  labelFormatter={(v) => `z = ${v}`}
                />
                <Legend
                  wrapperStyle={{ paddingTop: 8, fontSize: 12, color: '#94a3b8' }}
                />
                <Line
                  type="monotone"
                  dataKey="Bubble"
                  stroke="#14b8a6"
                  strokeWidth={2}
                  dot={false}
                  name="Bubble (liquid)"
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="Dew"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={false}
                  name="Dew (vapor)"
                  connectNulls
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState message="Select a binary pair and generate the diagram" />
          )}
        </div>

        {/* xy Diagram */}
        <div className="flex-1 panel p-4 flex flex-col min-h-0">
          <p className="label mb-3">xy Diagram</p>
          {xyChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={xyChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                <XAxis
                  dataKey="x"
                  type="number"
                  domain={[0, 1]}
                  stroke="#484f58"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  label={{
                    value: `x₁ (${comp1Label})`,
                    position: 'insideBottom',
                    offset: -5,
                    fill: '#64748b',
                    fontSize: 11,
                  }}
                />
                <YAxis
                  domain={[0, 1]}
                  stroke="#484f58"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  label={{
                    value: `y₁ (${comp1Label})`,
                    angle: -90,
                    position: 'insideLeft',
                    offset: 10,
                    fill: '#64748b',
                    fontSize: 11,
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1c2128',
                    border: '1px solid #30363d',
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                  labelFormatter={(v) => `x₁ = ${v}`}
                />
                <Legend
                  wrapperStyle={{ paddingTop: 8, fontSize: 12, color: '#94a3b8' }}
                />
                <Line
                  type="monotone"
                  dataKey="y"
                  stroke="#14b8a6"
                  strokeWidth={2}
                  dot={false}
                  name="Equilibrium"
                />
                <Line
                  type="monotone"
                  dataKey="diagonal"
                  stroke="#484f58"
                  strokeWidth={1}
                  strokeDasharray="4 4"
                  dot={false}
                  name="y = x"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState message="Generate a diagram to see the xy curve" />
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Scrubbing Solvent View ─────────────────────────────────────────────────────

function ScrubbingSolventView() {
  const [family, setFamily] = useState<ScrubbingFamily>('electrolyte')

  return (
    <div className="flex flex-col flex-1 min-h-0 gap-4">
      {/* Family Toggle */}
      <div className="flex bg-surface-800 border border-surface-600 rounded-lg p-0.5 self-start">
        <button
          onClick={() => setFamily('electrolyte')}
          className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${
            family === 'electrolyte'
              ? 'bg-amber-600/20 text-amber-400'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Electrolyte Solution
        </button>
        <button
          onClick={() => setFamily('amine')}
          className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${
            family === 'amine'
              ? 'bg-blue-600/20 text-blue-400'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Amine Solution
        </button>
      </div>

      {family === 'electrolyte' ? <ElectrolyteView /> : <AmineSolventView />}
    </div>
  )
}

// ─── Electrolyte Sub-View ───────────────────────────────────────────────────────

function ElectrolyteView() {
  const [solutes, setSolutes] = useState<ElectrolyteSolute[]>([])
  const [soluteId, setSoluteId] = useState('NaOH')
  const [eSpec, setESpec] = useState<ElectrolyteSpec>('pressure')
  const [pressure, setPressure] = useState('1.01325')
  const [temperature, setTemperature] = useState('100')
  const [wPercent, setWPercent] = useState('25')
  const [bpeData, setBpeData] = useState<BpeCurveResult | null>(null)
  const [vpData, setVpData] = useState<VpCurveResult | null>(null)
  const [opPoint, setOpPoint] = useState<OperatingPointResult | null>(null)

  const { loading, error, call } = useEngine()

  // Load solutes on mount
  useEffect(() => {
    async function loadSolutes() {
      const data = await call('/api/vle/electrolyte/solutes')
      if (data) setSolutes((data as any).solutes)
    }
    loadSolutes()
  }, [])

  async function handleGenerate() {
    const w = parseFloat(wPercent)

    if (eSpec === 'pressure') {
      const P = parseFloat(pressure)
      // BPE curve
      const bpe = await call('/api/vle/electrolyte/bpe-curve', {
        solute: soluteId,
        pressure_bar: P,
      })
      if (bpe) setBpeData(bpe as BpeCurveResult)

      // VP curve at T=boiling point of pure water at this P
      const vpTemp = bpe ? (bpe as BpeCurveResult).T_water : 100
      const vp = await call('/api/vle/electrolyte/vp-curve', {
        solute: soluteId,
        temperature_c: vpTemp,
      })
      if (vp) setVpData(vp as VpCurveResult)

      // Operating point
      const op = await call('/api/vle/electrolyte/operating-point', {
        solute: soluteId,
        w_percent: w,
        pressure_bar: P,
      })
      if (op) setOpPoint(op as OperatingPointResult)
    } else {
      const T = parseFloat(temperature)
      // VP curve at specified T
      const vp = await call('/api/vle/electrolyte/vp-curve', {
        solute: soluteId,
        temperature_c: T,
      })
      if (vp) setVpData(vp as VpCurveResult)

      // BPE curve at 1 atm (reference)
      const bpe = await call('/api/vle/electrolyte/bpe-curve', {
        solute: soluteId,
        pressure_bar: 1.01325,
      })
      if (bpe) setBpeData(bpe as BpeCurveResult)

      // Operating point
      const op = await call('/api/vle/electrolyte/operating-point', {
        solute: soluteId,
        w_percent: w,
        temperature_c: T,
      })
      if (op) setOpPoint(op as OperatingPointResult)
    }
  }

  const activeSolute = solutes.find((s) => s.id === soluteId)

  // BPE chart data
  const bpeChartData =
    bpeData?.w_percent.map((w, i) => ({
      w,
      T: bpeData.T_boil[i],
      BPE: bpeData.bpe[i],
    })) ?? []

  // VP chart data
  const vpChartData =
    vpData?.w_percent.map((w, i) => ({
      w,
      P_kPa: vpData.P_water[i] / 1000,
    })) ?? []

  const opW = opPoint?.w_percent ?? null
  const opTBoil = opPoint?.T_boil_celsius ?? null
  const opPKpa = opPoint ? opPoint.P_water_pa / 1000 : null

  return (
    <div className="flex gap-4 flex-1 min-h-0">
      {/* Inputs */}
      <div className="w-72 flex-shrink-0 space-y-4">
        <div className="panel p-4 space-y-4">
          <p className="label">Electrolyte Solution</p>

          <Field label="Solute">
            <select
              value={soluteId}
              onChange={(e) => setSoluteId(e.target.value)}
              className="input-field w-full"
            >
              {solutes.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.formula})
                </option>
              ))}
            </select>
          </Field>

          <Field label={`Concentration (w/w%)${activeSolute ? ` · max ${activeSolute.max_wt_pct}%` : ''}`}>
            <div className="flex gap-2">
              <input
                type="number"
                value={wPercent}
                onChange={(e) => setWPercent(e.target.value)}
                className="input-field flex-1"
                step="1"
                min="0"
                max={activeSolute?.max_wt_pct ?? 50}
              />
              <Unit>w/w%</Unit>
            </div>
          </Field>

          {/* Spec Toggle */}
          <Field label="Specify">
            <div className="flex bg-surface-700 border border-surface-500 rounded-md p-0.5">
              <button
                onClick={() => setESpec('pressure')}
                className={`flex-1 px-2 py-1.5 rounded text-xs font-medium transition-colors ${
                  eSpec === 'pressure'
                    ? 'bg-amber-600/20 text-amber-400'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Pressure → T<sub>boil</sub>
              </button>
              <button
                onClick={() => setESpec('temperature')}
                className={`flex-1 px-2 py-1.5 rounded text-xs font-medium transition-colors ${
                  eSpec === 'temperature'
                    ? 'bg-amber-600/20 text-amber-400'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Temperature → P<sub>water</sub>
              </button>
            </div>
          </Field>

          {eSpec === 'pressure' ? (
            <Field label="System Pressure">
              <div className="flex gap-2">
                <input
                  type="number"
                  value={pressure}
                  onChange={(e) => setPressure(e.target.value)}
                  className="input-field flex-1"
                  step="0.1"
                />
                <Unit>bar</Unit>
              </div>
            </Field>
          ) : (
            <Field label="Temperature">
              <div className="flex gap-2">
                <input
                  type="number"
                  value={temperature}
                  onChange={(e) => setTemperature(e.target.value)}
                  className="input-field flex-1"
                  step="1"
                />
                <Unit>°C</Unit>
              </div>
            </Field>
          )}

          <button
            onClick={handleGenerate}
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 size={14} className="animate-spin" /> Calculating…
              </>
            ) : (
              <>
                <Play size={14} /> Calculate
              </>
            )}
          </button>

          <ErrorMessage message={error} />
        </div>

        {/* Operating Point Summary */}
        {opPoint && (
          <div className="panel p-4 space-y-3">
            <p className="label">Operating Point</p>
            <ResultRow label="Solute" value={`${opPoint.solute_name} (${opPoint.formula})`} />
            <ResultRow label="Concentration" value={`${opPoint.w_percent} w/w%`} />
            <ResultRow label="Boiling Point" value={`${opPoint.T_boil_celsius} °C`} />
            <ResultRow label="BPE" value={`${opPoint.bpe_celsius} °C`} />
            <ResultRow label="P (water vapor)" value={`${opPoint.P_water_kpa} kPa`} />
            <ResultRow label="Water Activity" value={`${opPoint.water_activity}`} />
          </div>
        )}
      </div>

      {/* Dual Charts */}
      <div className="flex-1 flex flex-col gap-4 min-w-0">
        {/* BPE Curve */}
        <div className="flex-1 panel p-4 flex flex-col min-h-0">
          <p className="label mb-3">
            Boiling Point Elevation
            {bpeData ? ` — ${bpeData.solute_name} at ${bpeData.pressure_bar} bar` : ''}
          </p>
          {bpeChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={bpeChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                <XAxis
                  dataKey="w"
                  type="number"
                  domain={[0, 'dataMax']}
                  stroke="#484f58"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  label={{
                    value: 'Concentration (w/w%)',
                    position: 'insideBottom',
                    offset: -5,
                    fill: '#64748b',
                    fontSize: 11,
                  }}
                />
                <YAxis
                  stroke="#484f58"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  domain={['dataMin', 'dataMax']}
                  label={{
                    value: 'Boiling Point (°C)',
                    angle: -90,
                    position: 'insideLeft',
                    offset: 10,
                    fill: '#64748b',
                    fontSize: 11,
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1c2128',
                    border: '1px solid #30363d',
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                  labelFormatter={(v) => `${v} w/w%`}
                  formatter={(value: number) => [`${value.toFixed(1)} °C`, 'T_boil']}
                />
                <Line
                  type="monotone"
                  dataKey="T"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={false}
                  name="T_boil"
                />
                {opW !== null && opTBoil !== null && (
                  <ReferenceDot
                    x={opW}
                    y={opTBoil}
                    r={6}
                    fill="#ef4444"
                    stroke="#fff"
                    strokeWidth={2}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState message="Select a solute and calculate to see the BPE curve" />
          )}
        </div>

        {/* VP Depression Curve */}
        <div className="flex-1 panel p-4 flex flex-col min-h-0">
          <p className="label mb-3">
            Vapor Pressure Depression
            {vpData ? ` — ${vpData.solute_name} at ${vpData.T_celsius.toFixed(1)} °C` : ''}
          </p>
          {vpChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={vpChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                <XAxis
                  dataKey="w"
                  type="number"
                  domain={[0, 'dataMax']}
                  stroke="#484f58"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  label={{
                    value: 'Concentration (w/w%)',
                    position: 'insideBottom',
                    offset: -5,
                    fill: '#64748b',
                    fontSize: 11,
                  }}
                />
                <YAxis
                  stroke="#484f58"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  domain={[0, 'dataMax']}
                  label={{
                    value: 'P_water (kPa)',
                    angle: -90,
                    position: 'insideLeft',
                    offset: 10,
                    fill: '#64748b',
                    fontSize: 11,
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1c2128',
                    border: '1px solid #30363d',
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                  labelFormatter={(v) => `${v} w/w%`}
                  formatter={(value: number) => [`${value.toFixed(2)} kPa`, 'P_water']}
                />
                <Line
                  type="monotone"
                  dataKey="P_kPa"
                  stroke="#14b8a6"
                  strokeWidth={2}
                  dot={false}
                  name="P_water"
                />
                {opW !== null && opPKpa !== null && (
                  <ReferenceDot
                    x={opW}
                    y={opPKpa}
                    r={6}
                    fill="#ef4444"
                    stroke="#fff"
                    strokeWidth={2}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState message="Calculate to see the vapor pressure curve" />
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Amine Solvent Sub-View ─────────────────────────────────────────────────────

function AmineSolventView() {
  const [pairIndex, setPairIndex] = useState(0)
  const [pairs, setPairs] = useState<{ comp1: string; comp2: string; label: string }[]>([])
  const [pairsError, setPairsError] = useState<string | null>(null)
  const [spec, setSpec] = useState<BinarySpec>('pressure')
  const [pressure, setPressure] = useState('1.01325')
  const [temperature, setTemperature] = useState('80')
  const [txyData, setTxyData] = useState<TxyResult | null>(null)
  const [pxyData, setPxyData] = useState<PxyResult | null>(null)

  const { loading, error, call } = useEngine<TxyResult | PxyResult>()

  // Fetch available NRTL pairs and keep only amine-water systems (MEA/MDEA).
  useEffect(() => {
    fetch('http://localhost:8742/api/vle/binary/pairs')
      .then((r) => r.json())
      .then((data) => {
        const raw = (data.pairs ?? []) as any[]
        const filtered = raw.filter((p) => {
          const a = String(p.comp1).toLowerCase()
          const b = String(p.comp2).toLowerCase()
          const hasAmine = a.includes('mea') || a.includes('mdea') || b.includes('mea') || b.includes('mdea')
          const isWaterKey = (s: string) => s.includes('water') || s === 'h2o' || s.includes('h2o')
          const hasWater = isWaterKey(a) || isWaterKey(b)
          return hasAmine && hasWater
        })
        const ps = filtered.map((p) => ({
          comp1: String(p.comp1),
          comp2: String(p.comp2),
          label: `${String(p.comp1)} / ${String(p.comp2)}`,
        }))
        setPairs(ps)
        setPairIndex(0)
      })
      .catch((e) => setPairsError(e.message))
  }, [])

  const pair = pairs[pairIndex]

  async function handleGenerate() {
    if (!pair) return
    if (spec === 'pressure') {
      const data = await call('/api/vle/binary/txy', {
        comp1: pair.comp1,
        comp2: pair.comp2,
        pressure_bar: parseFloat(pressure),
        n_points: 51,
      })
      if (data) {
        setTxyData(data as TxyResult)
        setPxyData(null)
      }
    } else {
      const data = await call('/api/vle/binary/pxy', {
        comp1: pair.comp1,
        comp2: pair.comp2,
        temperature_c: parseFloat(temperature),
        n_points: 51,
      })
      if (data) {
        setPxyData(data as PxyResult)
        setTxyData(null)
      }
    }
  }

  const isTxy = spec === 'pressure' && txyData != null
  const isPxy = spec === 'temperature' && pxyData != null
  const activeData = isTxy ? txyData : isPxy ? pxyData : null

  // Txy chart data
  const txyChartData = (() => {
    if (!txyData) return []
    const bubbleCurve = txyData.x1.map((x, i) => ({
      composition: parseFloat(x.toFixed(4)),
      T: parseFloat(txyData.T_celsius[i].toFixed(2)),
    }))
    const dewCurve = txyData.y1.map((y, i) => ({
      composition: parseFloat((y as number).toFixed(4)),
      T: parseFloat(txyData.T_celsius[i].toFixed(2)),
    }))
    const compositionSet = new Set<number>()
    bubbleCurve.forEach((p) => compositionSet.add(p.composition))
    dewCurve.forEach((p) => compositionSet.add(p.composition))
    const allComps = Array.from(compositionSet).sort((a, b) => a - b)
    const bubbleMap = new Map(bubbleCurve.map((p) => [p.composition, p.T]))
    const dewMap = new Map(dewCurve.map((p) => [p.composition, p.T]))
    return allComps.map((z) => ({
      z,
      Bubble: bubbleMap.get(z) ?? null,
      Dew: dewMap.get(z) ?? null,
    }))
  })()

  // Pxy chart data
  const pxyChartData = (() => {
    if (!pxyData) return []
    const bubbleCurve = pxyData.x1.map((x, i) => ({
      composition: parseFloat(x.toFixed(4)),
      P: parseFloat(pxyData.P_bar[i].toFixed(5)),
    }))
    const dewCurve = pxyData.y1.map((y, i) => ({
      composition: parseFloat((y as number).toFixed(4)),
      P: parseFloat(pxyData.P_bar[i].toFixed(5)),
    }))
    const compositionSet = new Set<number>()
    bubbleCurve.forEach((p) => compositionSet.add(p.composition))
    dewCurve.forEach((p) => compositionSet.add(p.composition))
    const allComps = Array.from(compositionSet).sort((a, b) => a - b)
    const bubbleMap = new Map(bubbleCurve.map((p) => [p.composition, p.P]))
    const dewMap = new Map(dewCurve.map((p) => [p.composition, p.P]))
    return allComps.map((z) => ({
      z,
      Bubble: bubbleMap.get(z) ?? null,
      Dew: dewMap.get(z) ?? null,
    }))
  })()

  const comp1Label = activeData?.comp1 ?? pair?.comp1 ?? ''

  return (
    <div className="flex gap-4 flex-1 min-h-0">
      {/* Inputs */}
      <div className="w-72 flex-shrink-0 space-y-4">
        <div className="panel p-4 space-y-4">
          <p className="label">Amine-Water Binary</p>

          {pairsError ? (
            <ErrorMessage message={`Failed to load amine pairs: ${pairsError}`} />
          ) : null}

          <Field label="Amine Solvent">
            <select
              value={pairIndex}
              onChange={(e) => setPairIndex(Number(e.target.value))}
              className="input-field w-full"
              disabled={pairs.length === 0}
            >
              {pairs.map((p, i) => (
                <option key={i} value={i}>
                  {p.label}
                </option>
              ))}
            </select>
          </Field>

          {/* Spec Toggle */}
          <Field label="Diagram Type">
            <div className="flex bg-surface-700 border border-surface-500 rounded-md p-0.5">
              <button
                onClick={() => setSpec('pressure')}
                className={`flex-1 px-2 py-1.5 rounded text-xs font-medium transition-colors ${
                  spec === 'pressure'
                    ? 'bg-blue-600/20 text-blue-400'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Pressure (Txy)
              </button>
              <button
                onClick={() => setSpec('temperature')}
                className={`flex-1 px-2 py-1.5 rounded text-xs font-medium transition-colors ${
                  spec === 'temperature'
                    ? 'bg-blue-600/20 text-blue-400'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Temperature (Pxy)
              </button>
            </div>
          </Field>

          {spec === 'pressure' ? (
            <Field label="System Pressure">
              <div className="flex gap-2">
                <input
                  type="number"
                  value={pressure}
                  onChange={(e) => setPressure(e.target.value)}
                  className="input-field flex-1"
                  step="0.1"
                />
                <Unit>bar</Unit>
              </div>
            </Field>
          ) : (
            <Field label="System Temperature">
              <div className="flex gap-2">
                <input
                  type="number"
                  value={temperature}
                  onChange={(e) => setTemperature(e.target.value)}
                  className="input-field flex-1"
                  step="1"
                />
                <Unit>°C</Unit>
              </div>
            </Field>
          )}

          <button
            onClick={handleGenerate}
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 size={14} className="animate-spin" /> Generating…
              </>
            ) : (
              <>
                <Play size={14} /> Generate Diagram
              </>
            )}
          </button>

          <ErrorMessage message={error} />
        </div>

        {/* Summary */}
        {activeData && (
          <div className="panel p-4 space-y-3">
            <p className="label">System Summary</p>
            <ResultRow
              label="Amine"
              value={activeData.comp1.toUpperCase()}
            />
            {isTxy && txyData && (
              <>
                <ResultRow
                  label="Pressure"
                  value={`${txyData.pressure_bar} bar`}
                />
                <ResultRow
                  label="T (pure water)"
                  value={`${txyData.T_celsius[0].toFixed(1)} °C`}
                />
                <ResultRow
                  label="T (pure amine)"
                  value={`${txyData.T_celsius[txyData.T_celsius.length - 1].toFixed(1)} °C`}
                />
              </>
            )}
            {isPxy && pxyData && (
              <>
                <ResultRow
                  label="Temperature"
                  value={`${pxyData.T_celsius} °C`}
                />
                <ResultRow
                  label="P (pure water)"
                  value={`${pxyData.P_bar[0].toFixed(4)} bar`}
                />
                <ResultRow
                  label="P (pure amine)"
                  value={`${pxyData.P_bar[pxyData.P_bar.length - 1].toFixed(4)} bar`}
                />
              </>
            )}
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="flex-1 panel p-4 flex flex-col min-h-0">
        <p className="label mb-3">
          {isTxy
            ? `Txy Diagram — ${comp1Label.toUpperCase()} / Water`
            : isPxy
              ? `Pxy Diagram — ${comp1Label.toUpperCase()} / Water`
              : 'Phase Diagram'}
        </p>
        {isTxy && txyChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={txyChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
              <XAxis
                dataKey="z"
                type="number"
                domain={[0, 1]}
                stroke="#484f58"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                label={{
                  value: `Mole fraction ${comp1Label.toUpperCase()}`,
                  position: 'insideBottom',
                  offset: -5,
                  fill: '#64748b',
                  fontSize: 11,
                }}
              />
              <YAxis
                stroke="#484f58"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                label={{
                  value: 'Temperature (°C)',
                  angle: -90,
                  position: 'insideLeft',
                  offset: 10,
                  fill: '#64748b',
                  fontSize: 11,
                }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1c2128',
                  border: '1px solid #30363d',
                  borderRadius: 6,
                  fontSize: 12,
                }}
                labelFormatter={(v) => `z = ${v}`}
              />
              <Legend
                wrapperStyle={{ paddingTop: 8, fontSize: 12, color: '#94a3b8' }}
              />
              <Line
                type="monotone"
                dataKey="Bubble"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                name="Bubble (liquid)"
                connectNulls
              />
              <Line
                type="monotone"
                dataKey="Dew"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
                name="Dew (vapor)"
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        ) : isPxy && pxyChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={pxyChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
              <XAxis
                dataKey="z"
                type="number"
                domain={[0, 1]}
                stroke="#484f58"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                label={{
                  value: `Mole fraction ${comp1Label.toUpperCase()}`,
                  position: 'insideBottom',
                  offset: -5,
                  fill: '#64748b',
                  fontSize: 11,
                }}
              />
              <YAxis
                stroke="#484f58"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                label={{
                  value: 'Pressure (bar)',
                  angle: -90,
                  position: 'insideLeft',
                  offset: 10,
                  fill: '#64748b',
                  fontSize: 11,
                }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1c2128',
                  border: '1px solid #30363d',
                  borderRadius: 6,
                  fontSize: 12,
                }}
                labelFormatter={(v) => `z = ${v}`}
              />
              <Legend
                wrapperStyle={{ paddingTop: 8, fontSize: 12, color: '#94a3b8' }}
              />
              <Line
                type="monotone"
                dataKey="Bubble"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                name="Bubble (liquid)"
                connectNulls
              />
              <Line
                type="monotone"
                dataKey="Dew"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
                name="Dew (vapor)"
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <EmptyState message="Select an amine and generate the diagram" />
        )}
      </div>
    </div>
  )
}


// ─── Shared Components ──────────────────────────────────────────────────────────

function Field({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-slate-300 text-xs font-medium">{label}</label>
      {children}
    </div>
  )
}

function Unit({ children }: { children: string }) {
  return (
    <span className="input-field bg-surface-800 text-slate-500 px-2 flex items-center text-xs">
      {children}
    </span>
  )
}

function ResultRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-slate-400 text-xs">{label}</span>
      <span className="value-display">{value}</span>
    </div>
  )
}

function ErrorMessage({ message }: { message: string | null }) {
  if (!message) return null
  return (
    <div className="flex items-start gap-2 p-3 bg-red-900/30 border border-red-800/50 rounded-md">
      <AlertCircle size={14} className="text-red-400 mt-0.5 flex-shrink-0" />
      <p className="text-red-300 text-xs">{message}</p>
    </div>
  )
}

function WarningMessage({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2 p-3 bg-amber-900/30 border border-amber-800/50 rounded-md">
      <AlertTriangle
        size={14}
        className="text-amber-400 mt-0.5 flex-shrink-0"
      />
      <p className="text-amber-300 text-xs">{message}</p>
    </div>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center space-y-3">
        <FlaskConical size={40} className="text-surface-600 mx-auto" />
        <p className="text-slate-500 text-sm">{message}</p>
      </div>
    </div>
  )
}


// ─── System Builder — gas mixture → target gas → solvent → Column Design ────────

// Known liquid densities for solvents at ~25°C [kg/m³]
const SOLVENT_DENSITY: Record<string, number> = {
  'Water':                 998,
  'Methanol':              791,
  'Monoethanolamine':      1012,
  'Methyldiethanolamine':  1038,
}

interface CompactCompound {
  key: string
  name: string
  mw: number
  category: string
}

interface MixtureRow {
  compound: CompactCompound
  molPercent: string  // string for input binding
}

interface SystemBuilderProps {
  onSend: (preset: import('../App').ColumnDesignPreset) => void
}

function SystemBuilder({ onSend }: SystemBuilderProps) {
  // Available compounds
  const [gasComps, setGasComps] = useState<CompactCompound[]>([])   // carrier + acid
  const [acidGases, setAcidGases] = useState<CompactCompound[]>([])
  const [solvents, setSolvents] = useState<CompactCompound[]>([])

  // Step 1: Gas mixture
  const [mixture, setMixture] = useState<MixtureRow[]>([])

  // Step 2: Target gas
  const [targetGas, setTargetGas] = useState('')

  // Step 3: Solvent
  const [selectedSolvent, setSelectedSolvent] = useState('')

  // Conditions
  const [T_celsius, setT_celsius] = useState('40')
  const [P_bar, setP_bar] = useState('1.01325')

  const [expanded, setExpanded] = useState(false)

  const engine = useEngine<{ categories: Record<string, CategoryGroup> }>()

  // Fetch compound list
  useEffect(() => {
    async function load() {
      const data = await engine.call('/api/compounds')
      if (!data) return
      const gas: CompactCompound[] = []
      const acid: CompactCompound[] = []
      const solv: CompactCompound[] = []
      for (const [catKey, group] of Object.entries(data.categories)) {
        for (const c of group.compounds) {
          const comp = { key: c.key, name: c.name, mw: c.mw, category: catKey }
          if (catKey === 'acid_gas') {
            gas.push(comp)
            acid.push(comp)
          } else if (catKey === 'carrier_gas') {
            gas.push(comp)
          } else if (catKey === 'amine_solvent' || catKey === 'physical_solvent') {
            solv.push(comp)
          }
        }
      }
      setGasComps(gas)
      setAcidGases(acid)
      setSolvents(solv)
      if (solv.length > 0) setSelectedSolvent(solv[0].name)
    }
    load()
  }, [])

  // Acid gases currently in the mixture (for target selection)
  const acidGasesInMixture = mixture.filter(
    r => r.compound.category === 'acid_gas'
  )

  // Total mol%
  const totalMol = mixture.reduce((s, r) => s + (parseFloat(r.molPercent) || 0), 0)

  function removeGas(key: string) {
    setMixture(mixture.filter(r => r.compound.key !== key))
    if (targetGas === mixture.find(r => r.compound.key === key)?.compound.name) {
      setTargetGas('')
    }
  }

  function updateMol(key: string, val: string) {
    setMixture(mixture.map(r =>
      r.compound.key === key ? { ...r, molPercent: val } : r
    ))
  }

  function handleSend() {
    if (mixture.length === 0 || !targetGas || !selectedSolvent) return
    if (Math.abs(totalMol - 100) > 0.5) return

    const solvent = solvents.find(s => s.name === selectedSolvent)
    if (!solvent) return

    const T = parseFloat(T_celsius) || 40
    const P = parseFloat(P_bar) || 1.01325

    // Mixture average MW
    const mixtureMW = mixture.reduce((s, r) => {
      const frac = (parseFloat(r.molPercent) || 0) / 100
      return s + frac * r.compound.mw
    }, 0)

    // Gas density via ideal gas: ρ = P·MW_avg / (R·T)
    const R = 8.314
    const T_K = T + 273.15
    const P_Pa = P * 1e5
    const rho_G = (P_Pa * mixtureMW / 1000) / (R * T_K)
    const rho_L = SOLVENT_DENSITY[solvent.name] ?? 1000

    onSend({
      gasMixture: mixture.map(r => ({
        name: r.compound.name,
        mw: r.compound.mw,
        molPercent: parseFloat(r.molPercent) || 0,
      })),
      targetGas,
      solventName: solvent.name,
      solventMW: solvent.mw,
      T_celsius: T,
      P_bar: P,
      mixtureMW: Math.round(mixtureMW * 100) / 100,
      rho_G: Math.round(rho_G * 100) / 100,
      rho_L,
    })
  }

  if (gasComps.length === 0) return null

  // Available gases not yet in mixture
  const availableGases = gasComps.filter(g => !mixture.some(r => r.compound.key === g.key))

  const isValid = mixture.length > 0 && Math.abs(totalMol - 100) < 0.5 && targetGas && selectedSolvent

  return (
    <div className="panel border-primary-600/20">
      {/* Collapsed bar */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-2.5 flex items-center gap-3 hover:bg-surface-700/30 transition-colors"
      >
        <Columns size={14} className="text-primary-400" />
        <span className="text-xs font-medium text-primary-400">Define System → Column Design</span>
        {mixture.length > 0 && (
          <span className="text-[10px] text-slate-500">
            {mixture.map(r => r.compound.name).join(' + ')}
            {targetGas && ` · Remove: ${targetGas}`}
            {selectedSolvent && ` · Solvent: ${selectedSolvent}`}
          </span>
        )}
        <ChevronRight size={12} className={`ml-auto text-slate-500 transition-transform ${expanded ? 'rotate-90' : ''}`} />
      </button>

      {/* Expanded panel */}
      {expanded && (
        <div className="px-4 pb-4 pt-1 space-y-3 border-t border-surface-700/50">
          {/* Step 1: Gas Mixture */}
          <div>
            <p className="label text-[10px] mb-1.5">① Gas Mixture Composition</p>
            {mixture.length > 0 && (
              <div className="space-y-1 mb-2">
                {mixture.map(r => (
                  <div key={r.compound.key} className="flex items-center gap-2">
                    <span className={`text-xs w-40 truncate ${
                      r.compound.category === 'acid_gas' ? 'text-red-400' : 'text-slate-300'
                    }`}>
                      {r.compound.name}
                      <span className="text-slate-600 ml-1">({r.compound.mw})</span>
                    </span>
                    <input
                      type="number"
                      value={r.molPercent}
                      onChange={e => updateMol(r.compound.key, e.target.value)}
                      placeholder="mol%"
                      className="input-field py-1 text-xs w-20 text-center"
                      min="0"
                      max="100"
                      step="0.1"
                    />
                    <span className="text-slate-600 text-[10px]">mol%</span>
                    <button
                      onClick={() => removeGas(r.compound.key)}
                      className="text-slate-600 hover:text-red-400 transition-colors ml-1"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))}
                <div className={`text-[10px] mt-1 ${
                  Math.abs(totalMol - 100) < 0.5 ? 'text-emerald-500' : 'text-amber-400'
                }`}>
                  Total: {totalMol.toFixed(1)}%
                  {Math.abs(totalMol - 100) >= 0.5 && ' — must equal 100%'}
                </div>
              </div>
            )}
            <div className="flex items-center gap-2">
              <select
                value=""
                onChange={e => {
                  const comp = gasComps.find(g => g.key === e.target.value)
                  if (!comp) return
                  if (mixture.some(r => r.compound.key === comp.key)) return
                  setMixture(prev => [...prev, { compound: comp, molPercent: '' }])
                }}
                className="input-field py-1 text-xs flex-1"
              >
                <option value="">+ Add component…</option>
                {availableGases.map(g => (
                  <option key={g.key} value={g.key}>
                    {g.name} ({g.mw}) — {g.category === 'acid_gas' ? 'acid gas' : 'carrier'}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Step 2 + 3 + Conditions — horizontal row */}
          <div className="flex items-end gap-4">
            {/* Target gas */}
            <div className="flex-1">
              <p className="label text-[10px] mb-1.5">② Target Gas to Remove</p>
              <select
                value={targetGas}
                onChange={e => setTargetGas(e.target.value)}
                className="input-field py-1.5 text-xs w-full"
                disabled={acidGasesInMixture.length === 0}
              >
                <option value="">
                  {acidGasesInMixture.length === 0 ? 'Add an acid gas first…' : 'Select target…'}
                </option>
                {acidGasesInMixture.map(r => (
                  <option key={r.compound.key} value={r.compound.name}>
                    {r.compound.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Solvent */}
            <div className="flex-1">
              <p className="label text-[10px] mb-1.5">③ Solvent</p>
              <select
                value={selectedSolvent}
                onChange={e => setSelectedSolvent(e.target.value)}
                className="input-field py-1.5 text-xs w-full"
              >
                {solvents.map(s => (
                  <option key={s.key} value={s.name}>{s.name} ({s.mw})</option>
                ))}
              </select>
            </div>

            {/* T */}
            <div className="w-20">
              <p className="label text-[10px] mb-1.5">T (°C)</p>
              <input
                type="number"
                value={T_celsius}
                onChange={e => setT_celsius(e.target.value)}
                className="input-field py-1.5 text-xs w-full text-center"
              />
            </div>

            {/* P */}
            <div className="w-24">
              <p className="label text-[10px] mb-1.5">P (bar)</p>
              <input
                type="number"
                value={P_bar}
                onChange={e => setP_bar(e.target.value)}
                className="input-field py-1.5 text-xs w-full text-center"
                step="0.01"
              />
            </div>

            {/* Send button */}
            <button
              onClick={handleSend}
              disabled={!isValid}
              className="btn-primary py-1.5 px-3 text-xs flex items-center gap-1.5 whitespace-nowrap"
            >
              <ArrowRight size={12} />
              Design Column
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
