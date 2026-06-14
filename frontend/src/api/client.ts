/// <reference types="vite/client" />

import axios, {
  type AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from 'axios'

// ── Config ────────────────────────────────────────────────────────────────────

export const BASE_URL   = import.meta.env.VITE_API_URL  ?? 'http://localhost:8000'
export const API_PREFIX = import.meta.env.VITE_API_PATH ?? '/api'

// ── Axios instance ────────────────────────────────────────────────────────────

export const http: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}${API_PREFIX}`,
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
})

http.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => config,
)

http.interceptors.response.use(
  (res) => res,
  (err: AxiosError) => Promise.reject(normalizeError(err)),
)

// ── Error handling ────────────────────────────────────────────────────────────

export interface ApiError {
  message: string
  status:  number | null
  detail:  unknown
}

export function normalizeError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as Record<string, unknown> | undefined
    const message =
      (data?.detail as string | undefined) ??
      (data?.message as string | undefined) ??
      error.message
    return { message, status: error.response?.status ?? null, detail: data ?? null }
  }
  if (error instanceof Error) {
    return { message: error.message, status: null, detail: null }
  }
  return { message: 'Errore sconosciuto', status: null, detail: null }
}

export function isApiError(value: unknown): value is ApiError {
  return (
    typeof value === 'object' &&
    value !== null &&
    'message' in value &&
    'status' in value
  )
}

// ── SSE (GET via EventSource) ────────────────────────────────────────────────

export interface SSEHandle {
  close: () => void
}

export interface SSEOptions<T> {
  path:         string
  queryParams?: Record<string, string>
  onMessage?:   (event: T) => void
  events?:      Record<string, (rawData: string) => void>
  onError:      (err: Event) => void
  onOpen?:      () => void
}

export function connectSSE<T = unknown>(opts: SSEOptions<T>): SSEHandle {
  const url = new URL(`${BASE_URL}${API_PREFIX}${opts.path}`)

  if (opts.queryParams) {
    for (const [k, v] of Object.entries(opts.queryParams)) {
      url.searchParams.set(k, v)
    }
  }

  const es = new EventSource(url.toString())
  let closed = false

  es.onopen = () => opts.onOpen?.()

  if (opts.onMessage) {
    es.onmessage = (e: MessageEvent<string>) => {
      if (!e.data || e.data === ':') return
      try {
        opts.onMessage!(JSON.parse(e.data) as T)
      } catch { /* ignore */ }
    }
  }

  if (opts.events) {
    for (const [name, handler] of Object.entries(opts.events)) {
      es.addEventListener(name, (e) => {
        handler((e as MessageEvent<string>).data ?? '')
      })
    }
  }

  es.onerror = (e: Event) => {
    if (closed) return
    if (!(e instanceof MessageEvent)) {
      closed = true
      opts.onError(e)
      es.close()
    }
  }

  return {
    close: () => {
      closed = true
      es.close()
    },
  }
}

// ── SSE via POST (fetch + ReadableStream) ────────────────────────────────────

export interface SSEPostOptions<T> {
  path:    string
  body:    Record<string, unknown>
  events?: Record<string, (rawData: string) => void>
  onError: (err: Error) => void
  onOpen?: () => void
}

export function connectSSEPost<T = unknown>(opts: SSEPostOptions<T>): SSEHandle {
  const controller = new AbortController()
  let closed = false

  const url = `${BASE_URL}${API_PREFIX}${opts.path}`

  fetch(url, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
    body:    JSON.stringify(opts.body),
    signal:  controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const text = await response.text().catch(() => '')
        let detail = text
        try { detail = JSON.parse(text).detail ?? text } catch { /* keep raw */ }
        throw new Error(`HTTP ${response.status}: ${detail}`)
      }

      opts.onOpen?.()

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No readable stream')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        const parts = buffer.split('\n\n')
        buffer = parts.pop() ?? ''

        for (const part of parts) {
          if (!part.trim()) continue

          let eventName = ''
          let eventData = ''

          for (const line of part.split('\n')) {
            if (line.startsWith('event:')) {
              eventName = line.slice(6).trim()
            } else if (line.startsWith('data:')) {
              eventData = line.slice(5).trim()
            }
          }

          if (eventName && opts.events?.[eventName]) {
            opts.events[eventName](eventData)
          }
        }
      }
    })
    .catch((err: unknown) => {
      if (closed) return
      if (err instanceof DOMException && err.name === 'AbortError') return
      opts.onError(err instanceof Error ? err : new Error(String(err)))
    })

  return {
    close: () => {
      closed = true
      controller.abort()
    },
  }
}

// ── Utility ───────────────────────────────────────────────────────────────────

export function apiUrl(path: string): string {
  return `${BASE_URL}${API_PREFIX}${path}`
}