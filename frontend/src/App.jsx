import { useEffect, useMemo, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import api from './api/client'
import Layout from './components/Layout'
import { useAuth } from './context/AuthContext'
import AnalysisPage from './pages/AnalysisPage'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'

export default function App() {
  const { token } = useAuth()
  const [metrics, setMetrics] = useState({ breakdown: {}, equity_curve: [] })
  const [trades, setTrades] = useState([])
  const [filters, setFilters] = useState({ start: '', end: '', symbol: '', trade_type: '' })

  const query = useMemo(() => Object.fromEntries(Object.entries(filters).filter(([, v]) => v)), [filters])

  const fetchData = async () => {
    if (!token) return
    const [{ data: m }, { data: t }] = await Promise.all([
      api.get('/api/trades/metrics', { params: query }),
      api.get('/api/trades', { params: query }),
    ])
    setMetrics(m)
    setTrades(t)
  }

  const sync = async () => {
    await api.post('/api/trades/sync')
    await fetchData()
  }

  useEffect(() => { fetchData() }, [token, query])

  if (!token) {
    return (
      <Routes>
        <Route path="*" element={<LoginPage />} />
      </Routes>
    )
  }

  return (
    <Layout>
      <Routes>
        <Route path="/dashboard" element={<DashboardPage metrics={metrics} />} />
        <Route path="/analysis" element={<AnalysisPage metrics={metrics} trades={trades} filters={filters} setFilters={setFilters} onSync={sync} />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Layout>
  )
}
