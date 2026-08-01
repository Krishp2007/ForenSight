import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

const AppShell = ({ title }) => (
  <div className="flex min-h-screen bg-gray-950 text-white">
    <Sidebar />
    <div className="flex flex-col flex-1 overflow-hidden">
      <Topbar title={title} />
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  </div>
)

export default AppShell
