import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Sidebar } from './components/layout/Sidebar'
import { Header } from './components/layout/Header'
import { Dashboard } from './pages/Dashboard'
import { IntelligenceBrief } from './pages/IntelligenceBrief'
import { WolfConfiguration } from './pages/WolfConfiguration'
import { History } from './pages/History'
import { RiskManagement } from './pages/RiskManagement'
import { Alerts } from './pages/Alerts'
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
                <Route path="/intelligence" element={<IntelligenceBrief />} />
                <Route path="/configuration" element={<WolfConfiguration />} />
                <Route path="/trading" element={<WolfConfiguration />} />
                <Route path="/strategy" element={<WolfConfiguration />} />
                <Route path="/history" element={<History />} />
                <Route path="/risk" element={<RiskManagement />} />
                <Route path="/alerts" element={<Alerts />} />
              </Routes>
            </main>
          </div>
        </div>
      </div>
    </Router>
  )
}

export default App