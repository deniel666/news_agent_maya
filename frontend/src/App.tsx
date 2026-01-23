import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Briefings from './pages/Briefings'
import BriefingDetail from './pages/BriefingDetail'
import Approvals from './pages/Approvals'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/briefings" element={<Briefings />} />
        <Route path="/briefings/:threadId" element={<BriefingDetail />} />
        <Route path="/approvals" element={<Approvals />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App
