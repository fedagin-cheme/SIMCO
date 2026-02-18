import { useState } from 'react'
import { FlaskConical, Play, AlertCircle, Loader2 } from 'lucide-react'
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

// ─── Types ─────────────────────────────────────────────────────────────────────
interface VLEResult {
  component: string
  temperature_c: number
  pressure_bar: number
  liquid_mole_fraction: number[]
  vapor_mole_fraction: number[]
  bubble_point_c: number
  dew_point_c: number
  relative_volatility: number
  model_used: string
}

interface BubbleDewResult {
  component: string
  temperature_c?: number
  pressure_bar?: number
  bubble_temperature_c?: number
  dew_temperature_c?: number
  bubble_pressure_bar?: number
  dew_pressure_bar?: number
}

// ─── Component ─────────────────────────────────────────────────────────────────
export function VLECalculatorPage() {
  const [component, setComponent] = useState('CO2')
  const [temperature, setTemperature] = useState('25')
  const [pressure, setPressure] = useState('1.01325')
  const [result, setResult] = useState<BubbleDewResult | null>(null)

  const { loading, error, call } = useEngine<BubbleDewResult>()

  const COMPONENTS = [
    { value: 'CO2', label: 'Carbon Dioxide (CO₂)' },
    { value: 'H2S', label: 'Hydrogen Sulfide (H₂S)' },
    { value: 'water', label: 'Water (H₂O)' },
    { value: 'MEA', label: 'MEA (Monoethanolamine)' },
    { value: 'MDEA', label: 'MDEA' },
    { value: 'nitrogen', label: 'Nitrogen (N₂)' },
    { value: 'oxygen', label: 'Oxygen (O₂)' },
    { value: 'methane', label: 'Methane (CH₄)' },
    { value: 'SO2', label: 'Sulfur Dioxide (SO₂)' },
  ]

  async function handleCalculate() {
    const data = await call('/api/vle/bubble-dew', {
      component,
      temperature_c: parseFloat(temperature),
      pressure_bar: parseFloat(pressure),
    })
    if (data) setResult(data)
  }

  // Generate Pxy chart data (mocked for now — will call real endpoint)
  const chartData = result
    ? Array.from({ length: 11 }, (_, i) => {
        const x = i / 10
        return {
          x: parseFloat(x.toFixed(2)),
          'Vapor (y)': parseFloat(Math.pow(x, 0.6).toFixed(4)),
          'Liquid (x)': x,
        }
      })
    : []

  return (
    <div className="flex flex-col h-full gap-4 p-4 overflow-auto">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary-600/20 rounded-lg">
          <FlaskConical size={20} className="text-primary-400" />
        </div>
        <div>
          <h1 className="text-slate-100 font-semibold text-base">VLE Calculator</h1>
          <p className="text-slate-500 text-xs">Vapor-Liquid Equilibrium — bubble & dew point calculations</p>
        </div>
      </div>

      <div className="flex gap-4 flex-1 min-h-0">
        {/* ── Inputs ── */}
        <div className="w-72 flex-shrink-0 space-y-4">
          <div className="panel p-4 space-y-4">
            <p className="label">Inputs</p>

            {/* Component */}
            <div className="space-y-1.5">
              <label className="text-slate-300 text-xs font-medium">Component</label>
              <select
                value={component}
                onChange={e => setComponent(e.target.value)}
                className="input-field w-full"
              >
                {COMPONENTS.map(c => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>

            {/* Temperature */}
            <div className="space-y-1.5">
              <label className="text-slate-300 text-xs font-medium">Temperature</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  value={temperature}
                  onChange={e => setTemperature(e.target.value)}
                  className="input-field flex-1"
                  step="1"
                />
                <span className="input-field bg-surface-800 text-slate-500 px-2 flex items-center">°C</span>
              </div>
            </div>

            {/* Pressure */}
            <div className="space-y-1.5">
              <label className="text-slate-300 text-xs font-medium">Pressure</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  value={pressure}
                  onChange={e => setPressure(e.target.value)}
                  className="input-field flex-1"
                  step="0.1"
                />
                <span className="input-field bg-surface-800 text-slate-500 px-2 flex items-center">bar</span>
              </div>
            </div>

            {/* Calculate button */}
            <button
              onClick={handleCalculate}
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {loading
                ? <><Loader2 size={14} className="animate-spin" /> Calculating…</>
                : <><Play size={14} /> Calculate</>
              }
            </button>

            {/* Error */}
            {error && (
              <div className="flex items-start gap-2 p-3 bg-red-900/30 border border-red-800/50 rounded-md">
                <AlertCircle size={14} className="text-red-400 mt-0.5 flex-shrink-0" />
                <p className="text-red-300 text-xs">{error}</p>
              </div>
            )}
          </div>

          {/* Results panel */}
          {result && (
            <div className="panel p-4 space-y-3">
              <p className="label">Results</p>
              <ResultRow label="Component" value={result.component} />
              {result.bubble_temperature_c !== undefined && (
                <ResultRow
                  label="Bubble Point"
                  value={`${result.bubble_temperature_c.toFixed(2)} °C`}
                />
              )}
              {result.dew_temperature_c !== undefined && (
                <ResultRow
                  label="Dew Point"
                  value={`${result.dew_temperature_c.toFixed(2)} °C`}
                />
              )}
              {result.bubble_pressure_bar !== undefined && (
                <ResultRow
                  label="Bubble Pressure"
                  value={`${result.bubble_pressure_bar.toFixed(4)} bar`}
                />
              )}
            </div>
          )}
        </div>

        {/* ── Chart ── */}
        <div className="flex-1 panel p-4 flex flex-col min-w-0">
          <p className="label mb-4">Phase Diagram</p>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                <XAxis
                  dataKey="x"
                  stroke="#484f58"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  label={{ value: 'Liquid mole fraction (x)', position: 'insideBottom', offset: -5, fill: '#64748b', fontSize: 11 }}
                />
                <YAxis
                  stroke="#484f58"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  label={{ value: 'Vapor mole fraction (y)', angle: -90, position: 'insideLeft', offset: 10, fill: '#64748b', fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1c2128', border: '1px solid #30363d', borderRadius: 6 }}
                  labelStyle={{ color: '#94a3b8' }}
                  itemStyle={{ color: '#14b8a6' }}
                />
                <Legend wrapperStyle={{ paddingTop: 12, fontSize: 12, color: '#94a3b8' }} />
                <Line
                  type="monotone"
                  dataKey="Vapor (y)"
                  stroke="#14b8a6"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="Liquid (x)"
                  stroke="#64748b"
                  strokeWidth={1}
                  strokeDasharray="4 4"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-3">
                <FlaskConical size={40} className="text-surface-600 mx-auto" />
                <p className="text-slate-500 text-sm">Run a calculation to see the phase diagram</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
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
