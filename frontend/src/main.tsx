import React    from 'react'
import ReactDOM from 'react-dom/client'

import './index.css'
import App from './App'

// ── Pre-render theme init ─────────────────────────────────────────────────────
// Sincronizza data-theme con lo store Zustand all'avvio, dopo che React monta.
// Il blocco inline in index.html gestisce il pre-render (no FOUC);
// questo blocco garantisce coerenza con uiStore.theme.

function initTheme(): void {
  const saved = (() => {
    try { return localStorage.getItem('dareeda-theme') } catch { return null }
  })()

  const resolved =
    saved === 'light' || saved === 'dark'
      ? saved
      : window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'

  document.documentElement.setAttribute('data-theme', resolved)
}

initTheme()

// ── Mount ─────────────────────────────────────────────────────────────────────

const root = document.getElementById('root')

if (!root) {
  throw new Error(
    '[dareeda] Elemento #root non trovato nel DOM. ' +
    'Verifica che index.html contenga <div id="root"></div>.',
  )
}

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
