import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

const AppShell = ({ title }) => (
  <div style={{
    display: 'flex',
    minHeight: '100vh',
    background: '#1a2234',
    color: '#ffffff',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  }}>
    <Sidebar />
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
      <Topbar title={title} />
      <main style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
        <Outlet />
      </main>
    </div>
  </div>
)

export default AppShell
