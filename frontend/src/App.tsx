import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'
import { ThemeProvider } from '@/context/ThemeContext'
import { RequireAuth, RequireOnboarding, RedirectIfAuthed } from '@/components/RouteGuards'
import { AppLayout } from '@/components/AppLayout'

import Landing from '@/pages/Landing'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import Onboarding from '@/pages/Onboarding'
import Dashboard from '@/pages/Dashboard'
import RobotPage from '@/pages/robot/RobotPage'
import MonitoringPage from '@/pages/monitoring/MonitoringPage'
import Irrigation from '@/pages/Irrigation'
import RainwaterHarvesting from '@/pages/RainwaterHarvesting'
import CropRecommendation from '@/pages/CropRecommendation'
import FertilizerRecommendation from '@/pages/FertilizerRecommendation'
import SoilHealth from '@/pages/SoilHealth'
import YieldPrediction from '@/pages/YieldPrediction'
import AIAssistant from '@/pages/AIAssistant'
import Alerts from '@/pages/Alerts'
import Settings from '@/pages/Settings'
import BeamsBackgroundDemo from '@/pages/BeamsBackgroundDemo'

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<RedirectIfAuthed><Login /></RedirectIfAuthed>} />
            <Route path="/register" element={<RedirectIfAuthed><Register /></RedirectIfAuthed>} />
            <Route path="/onboarding" element={<RequireOnboarding><Onboarding /></RequireOnboarding>} />
            <Route path="/showcase/beams-background" element={<BeamsBackgroundDemo />} />

            <Route element={<RequireAuth><AppLayout /></RequireAuth>}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/robot" element={<RobotPage />} />
              <Route path="/monitoring" element={<MonitoringPage />} />
              <Route path="/irrigation" element={<Irrigation />} />
              <Route path="/rainwater" element={<RainwaterHarvesting />} />
              <Route path="/crop-recommendation" element={<CropRecommendation />} />
              <Route path="/fertilizer" element={<FertilizerRecommendation />} />
              <Route path="/soil-health" element={<SoilHealth />} />
              <Route path="/yield-prediction" element={<YieldPrediction />} />
              <Route path="/assistant" element={<AIAssistant />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
          </Routes>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}
