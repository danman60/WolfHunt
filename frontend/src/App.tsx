import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Sidebar } from './components/layout/Sidebar'
import { Header } from './components/layout/Header'
import { Dashboard } from './pages/Dashboard'
import { cn } from './utils/cn'
import './App.css'

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <Router>
      <div className="min-h-screen bg-gray-950">
        <Sidebar
          isCollapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
        
        {/* Main content */}
        <div className={cn(
          'transition-all duration-300',
          sidebarCollapsed ? 'lg:pl-16' : 'lg:pl-64'
        )}>
          <div className="flex flex-col">
            <Header
              user={{
                name: 'Trading User',
                email: 'user@wolfhunt.trading'
              }}
              notifications={3}
              tradingMode="paper"
              onLogout={() => console.log('Logout')}
              onSettings={() => console.log('Settings')}
            />
            
            <main className="flex-1">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/trading" element={<div className="p-6"><h1 className="text-2xl font-bold text-white">Trading</h1></div>} />
                <Route path="/history" element={<div className="p-6"><h1 className="text-2xl font-bold text-white">History</h1></div>} />
                <Route path="/strategy" element={<div className="p-6"><h1 className="text-2xl font-bold text-white">Strategy</h1></div>} />
                <Route path="/risk" element={<div className="p-6"><h1 className="text-2xl font-bold text-white">Risk Management</h1></div>} />
                <Route path="/alerts" element={<div className="p-6"><h1 className="text-2xl font-bold text-white">Alerts</h1></div>} />
              </Routes>
            </main>
          </div>
        </div>
      </div>
    </Router>
  )
}

export default App