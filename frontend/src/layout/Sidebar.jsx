import { NavLink } from 'react-router-dom'
import useAppStore from '../store/appStore.js'

const NAV = [
  { to: '/projects', icon: '▣', label: 'Progetti' },
  { to: '/upload',   icon: '↑', label: 'Upload'   },
]

export default function Sidebar() {
  const { sidebarExpanded, toggleSidebar } = useAppStore()
  const w = sidebarExpanded ? 'var(--sidebar-width-expanded)' : 'var(--sidebar-width-collapsed)'

  return (
    <aside style={{
      position: 'fixed', top: 0, left: 0, height: '100vh',
      width: w, transition: 'var(--sidebar-transition)',
      background: 'var(--gradient-deep-structure)',
      borderRight: '2px solid #000',
      display: 'flex', flexDirection: 'column',
      overflow: 'hidden', zIndex: 100
    }}>
      {/* Logo */}
      <div style={{ padding: '20px 16px', borderBottom: '2px solid #333' }}>
        {sidebarExpanded
          ? <span style={{ color: '#fff', fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 18, letterSpacing: 4 }}>DAREEDA</span>
          : <span style={{ color: 'var(--color-accent)', fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 18 }}>D</span>
        }
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '16px 0' }}>
        {NAV.map(({ to, icon, label }) => (
          <NavLink key={to} to={to} style={({ isActive }) => ({
            display: 'flex', alignItems: 'center', gap: 12,
            padding: '12px 16px', color: isActive ? 'var(--color-accent)' : '#fff',
            textDecoration: 'none', fontFamily: 'var(--font-mono)', fontSize: 13,
            borderLeft: isActive ? '3px solid var(--color-accent)' : '3px solid transparent',
            transition: 'all 100ms'
          })}>
            <span style={{ fontSize: 16, minWidth: 20, textAlign: 'center' }}>{icon}</span>
            {sidebarExpanded && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Toggle */}
      <button onClick={toggleSidebar} style={{
        margin: '16px', padding: '10px',
        background: 'transparent', border: '2px solid #444',
        color: '#fff', cursor: 'pointer', fontFamily: 'var(--font-mono)',
        fontSize: 12, textAlign: 'center'
      }}>
        {sidebarExpanded ? '◀ Chiudi' : '▶'}
      </button>
    </aside>
  )
}
