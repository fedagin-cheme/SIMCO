import { useState } from 'react'
import {
  FlaskConical,
  Play,
  AlertCircle,
  AlertTriangle,
  Loader2,
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

type Mode = 'pure' | 'binary'

// ─── Compound Data ──────────────────────────────────────────────────────────────

const COMPOUNDS = [
  { value: 'water',      label: 'Water (H₂O)' },
  { value: 'methanol',   label: 'Methanol (CH₃OH)' },
  { value: 'ethanol',    label: 'Ethanol (C₂H₅OH)' },
  { value: 'benzene',    label: 'Benzene (C₆H₆)' },
  { value: 'toluene',    label: 'Toluene (C₇H₈)' },
  { value: 'acetone',    label: 'Acetone (C₃H₆O)' },
  { value: 'n_hexane',   label: 'n-Hexane (C₆H₁₄)' },
  { value: 'n_heptane',  label: 'n-Heptane (C₇H₁₆)' },
  { value: 'chloroform', label: 'Chloroform (CHCl₃)' },
  { value: 'CO2',        label: 'Carbon Dioxide (CO₂)' },
  { value: 'H2S',        label: 'Hydrogen Sulfide (H₂S)' },
  { value: 'MEA',        label: 'MEA (Monoethanolamine)' },
  { value: 'MDEA',       label: 'MDEA' },
  { value: 'nitrogen',   label: 'Nitrogen (N₂)' },
  { value: 'oxygen',     label: 'Oxygen (O₂)' },
  { value: 'methane',    label: 'Methane (CH₄)' },
  { value: 'SO2',        label: 'Sulfur Dioxide (SO₂)' },
]

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
  const [component, setComponent] = useState('water')
  const [temperature, setTemperature] = useState('25')
  const [pressure, setPressure] = useState('1.01325')
  const [result, setResult] = useState<BubbleDewResult | null>(null)

  const { loading, error, call } = useEngine<BubbleDewResult>()

  async function handleCalculate() {
    const data = await call('/api/vle/bubble-dew', {
      component,
      temperature_c: parseFloat(temperature),
      pressure_bar: parseFloat(pressure),
    })
    if (data) setResult(data)
  }

  return (
    <div className="flex gap-4 flex-1 min-h-0">
      {/* Inputs */}
      <div className="w-72 flex-shrink-0 space-y-4">
        <div className="panel p-4 space-y-4">
          <p className="label">Inputs</p>

          <Field label="Component">
            <select
              value={component}
              onChange={(e) => setComponent(e.target.value)}
              className="input-field w-full"
            >
              {COMPOUNDS.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </Field>

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

        {/* Results */}
        {result && (
          <div className="panel p-4 space-y-3">
            <p className="label">Results</p>
            <ResultRow label="Component" value={result.component} />
            <ResultRow
              label="Bubble Point"
              value={`${result.bubble_temperature_c.toFixed(2)} °C`}
            />
            <ResultRow
              label="Dew Point"
              value={`${result.dew_temperature_c.toFixed(2)} °C`}
            />
            <ResultRow
              label="Sat. Pressure"
              value={`${result.saturation_pressure_bar.toFixed(4)} bar`}
            />
            {result.warning && <WarningMessage message={result.warning} />}
          </div>
        )}
      </div>

      {/* Right panel — info */}
      <div className="flex-1 panel p-4 flex flex-col min-w-0">
        <p className="label mb-4">Component Info</p>
        {result ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-4 max-w-xs">
              <div className="p-3 bg-primary-600/10 rounded-full w-14 h-14 flex items-center justify-center mx-auto">
                <FlaskConical size={24} className="text-primary-500" />
              </div>
              <div className="space-y-2">
                <p className="text-slate-200 font-medium">
                  {COMPOUNDS.find((c) => c.value === result.component)?.label ??
                    result.component}
                </p>
                <div className="space-y-1 text-sm">
                  <p className="text-slate-400">
                    At{' '}
                    <span className="value-display">
                      {result.temperature_c} °C
                    </span>{' '}
                    &{' '}
                    <span className="value-display">
                      {result.pressure_bar} bar
                    </span>
                  </p>
                  <p className="text-slate-400">
                    Boiling point:{' '}
                    <span className="value-display">
                      {result.bubble_temperature_c.toFixed(2)} °C
                    </span>
                  </p>
                  <p className="text-slate-400">
                    Vapor pressure:{' '}
                    <span className="value-display">
                      {result.saturation_pressure_bar.toFixed(4)} bar
                    </span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <EmptyState message="Select a component and run a calculation" />
        )}
      </div>
    </div>
  )
}

// ─── Binary Mixture View ────────────────────────────────────────────────────────

function BinaryMixtureView() {
  const [pairIndex, setPairIndex] = useState(0)
  const [pressure, setPressure] = useState('1.01325')
  const [txyData, setTxyData] = useState<TxyResult | null>(null)

  const { loading, error, call } = useEngine<TxyResult>()

  const pair = BINARY_PAIRS[pairIndex]

  async function handleGenerate() {
    const data = await call('/api/vle/binary/txy', {
      comp1: pair.comp1,
      comp2: pair.comp2,
      pressure_bar: parseFloat(pressure),
      n_points: 51,
    })
    if (data) setTxyData(data)
  }

  // Transform API arrays into recharts-friendly data
  const chartData =
    txyData
      ? txyData.x1.map((x, i) => ({
          x: parseFloat(x.toFixed(4)),
          'Bubble (T-x)': parseFloat(txyData.T_celsius[i].toFixed(2)),
          'Dew (T-y)': parseFloat(
            // Dew line: plot T vs y1 — we need to find T at each y value.
            // Since we have y1 array, we plot the same T values against y1 for the dew curve.
            // For a proper Txy, bubble = T vs x1, dew = T vs y1. We store both for the chart.
            txyData.T_celsius[i].toFixed(2)
          ),
          y: parseFloat(txyData.y1[i].toFixed(4)),
        }))
      : []

  // For the Txy diagram we need two datasets:
  // Bubble curve: T vs x1 (liquid composition)
  // Dew curve: T vs y1 (vapor composition)
  const bubbleCurve = txyData
    ? txyData.x1.map((x, i) => ({
        composition: parseFloat(x.toFixed(4)),
        T: parseFloat(txyData.T_celsius[i].toFixed(2)),
      }))
    : []

  const dewCurve = txyData
    ? txyData.y1.map((y, i) => ({
        composition: parseFloat((y as number).toFixed(4)),
        T: parseFloat(txyData.T_celsius[i].toFixed(2)),
      }))
    : []

  // Merge into a single dataset keyed by composition for recharts
  const txyChartData = (() => {
    if (!txyData) return []

    // Collect all unique composition values, sorted
    const compositionSet = new Set<number>()
    bubbleCurve.forEach((p) => compositionSet.add(p.composition))
    dewCurve.forEach((p) => compositionSet.add(p.composition))
    const allComps = Array.from(compositionSet).sort((a, b) => a - b)

    // Build lookup maps
    const bubbleMap = new Map(bubbleCurve.map((p) => [p.composition, p.T]))
    const dewMap = new Map(dewCurve.map((p) => [p.composition, p.T]))

    return allComps.map((z) => ({
      z,
      Bubble: bubbleMap.get(z) ?? null,
      Dew: dewMap.get(z) ?? null,
    }))
  })()

  // xy diagram data
  const xyChartData = txyData
    ? txyData.x1.map((x, i) => ({
        x: parseFloat(x.toFixed(4)),
        y: parseFloat(txyData.y1[i].toFixed(4)),
        diagonal: parseFloat(x.toFixed(4)),
      }))
    : []

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

        {/* Key values */}
        {txyData && (
          <div className="panel p-4 space-y-3">
            <p className="label">System Summary</p>
            <ResultRow label="Component 1" value={txyData.comp1} />
            <ResultRow label="Component 2" value={txyData.comp2} />
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
          </div>
        )}
      </div>

      {/* Charts */}
      <div className="flex-1 flex flex-col gap-4 min-w-0">
        {/* Txy Diagram */}
        <div className="flex-1 panel p-4 flex flex-col min-h-0">
          <p className="label mb-3">Txy Diagram</p>
          {txyChartData.length > 0 ? (
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
                    value: `Mole fraction ${txyData?.comp1 ?? ''}`,
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
                    value: `x₁ (${txyData?.comp1 ?? ''})`,
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
                    value: `y₁ (${txyData?.comp1 ?? ''})`,
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
            <EmptyState message="Generate a Txy diagram to see the xy curve" />
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
