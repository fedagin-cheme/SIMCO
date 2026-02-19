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

type Mode = 'pure' | 'binary'
type BinarySpec = 'pressure' | 'temperature'

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

const BINARY_PAIRS = [
  { comp1: 'methanol',   comp2: 'water',    label: 'Methanol / Water' },
  { comp1: 'ethanol',    comp2: 'water',    label: 'Ethanol / Water' },
  { comp1: 'acetone',    comp2: 'water',    label: 'Acetone / Water' },
  { comp1: 'acetone',    comp2: 'methanol', label: 'Acetone / Methanol' },
  { comp1: 'benzene',    comp2: 'toluene',  label: 'Benzene / Toluene' },
  { comp1: 'methanol',   comp2: 'benzene',  label: 'Methanol / Benzene' },
  { comp1: 'ethanol',    comp2: 'benzene',  label: 'Ethanol / Benzene' },
  { comp1: 'chloroform', comp2: 'methanol', label: 'Chloroform / Methanol' },
]

// ─── Main Component ─────────────────────────────────────────────────────────────

export function VLECalculatorPage() {
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
        </div>
      </div>

      {/* Body */}
      {mode === 'pure' ? <PureComponentView /> : <BinaryMixtureView />}
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
  const [spec, setSpec] = useState<BinarySpec>('pressure')
  const [pressure, setPressure] = useState('1.01325')
  const [temperature, setTemperature] = useState('80')
  const [txyData, setTxyData] = useState<TxyResult | null>(null)
  const [pxyData, setPxyData] = useState<PxyResult | null>(null)

  const { loading, error, call } = useEngine<TxyResult | PxyResult>()

  const pair = BINARY_PAIRS[pairIndex]

  async function handleGenerate() {
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

  const comp1Label = activeData?.comp1 ?? pair.comp1

  return (
    <div className="flex gap-4 flex-1 min-h-0">
      {/* Inputs */}
      <div className="w-72 flex-shrink-0 space-y-4">
        <div className="panel p-4 space-y-4">
          <p className="label">Binary System</p>

          <Field label="Component Pair">
            <select
              value={pairIndex}
              onChange={(e) => setPairIndex(Number(e.target.value))}
              className="input-field w-full"
            >
              {BINARY_PAIRS.map((p, i) => (
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
