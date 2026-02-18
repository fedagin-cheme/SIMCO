import { useState, useCallback } from 'react'

const ENGINE_URL = 'http://127.0.0.1:8742'

interface UseEngineResult<T> {
  data: T | null
  loading: boolean
  error: string | null
  call: (path: string, body?: Record<string, unknown>) => Promise<T | null>
}

export function useEngine<T = unknown>(): UseEngineResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const call = useCallback(async (
    path: string,
    body?: Record<string, unknown>
  ): Promise<T | null> => {
    setLoading(true)
    setError(null)

    try {
      const res = await fetch(`${ENGINE_URL}${path}`, {
        method: body ? 'POST' : 'GET',
        headers: body ? { 'Content-Type': 'application/json' } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }

      const result: T = await res.json()
      setData(result)
      return result
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Unknown error'
      setError(msg)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  return { data, loading, error, call }
}

// Typed helpers for specific endpoints
export async function checkEngineHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${ENGINE_URL}/health`, { signal: AbortSignal.timeout(2000) })
    return res.ok
  } catch {
    return false
  }
}
