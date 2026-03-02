import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Layout({ children }) {
  const { logout } = useAuth()
  return (
    <div className="app">
      <nav>
        <h2>MT5 Tracker</h2>
        <div className="links">
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/analysis">Analysis</Link>
          <button onClick={logout}>Logout</button>
        </div>
      </nav>
      <main>{children}</main>
    </div>
  )
}
