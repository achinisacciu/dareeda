import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar.jsx'
import useAppStore from '../store/appStore.js'

export default function AppLayout() {
  const sidebarExpanded = useAppStore(s => s.sidebarExpanded)
  const ml = sidebarExpanded ? 'var(--sidebar-width-expanded)' : 'var(--sidebar-width-collapsed)'

  return (
    <div className="app-layout">
      <Sidebar />
      <main 
        className="app-main"
        style={{
          marginLeft: ml,
          transition: 'margin-left 250ms ease',
        }}
      >
        <Outlet />
      </main>
    </div>
  )
}