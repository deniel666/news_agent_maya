import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Briefings from './pages/Briefings'
import BriefingDetail from './pages/BriefingDetail'
import Approvals from './pages/Approvals'
import Analytics from './pages/Analytics'
import Sources from './pages/Sources'
import Schedule from './pages/Schedule'
import OnDemand from './pages/OnDemand'
import OnDemandDetail from './pages/OnDemandDetail'
import ContentLibrary from './pages/ContentLibrary'
import StoryDetail from './pages/StoryDetail'
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
        <Route path="/sources" element={<Sources />} />
        <Route path="/schedule" element={<Schedule />} />
        <Route path="/on-demand" element={<OnDemand />} />
        <Route path="/on-demand/:jobId" element={<OnDemandDetail />} />
        <Route path="/content" element={<ContentLibrary />} />
        <Route path="/content/:storyId" element={<StoryDetail />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App
