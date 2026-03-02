import { createContext, useContext, useMemo, useState } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('token'))

  const login = async (username, password) => {
    const payload = new URLSearchParams({ username, password })
    const { data } = await api.post('/api/auth/login', payload)
    localStorage.setItem('token', data.access_token)
    setToken(data.access_token)
  }

  const register = async (username, password) => {
    const { data } = await api.post('/api/auth/register', { username, password })
    localStorage.setItem('token', data.access_token)
    setToken(data.access_token)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
  }

  const value = useMemo(() => ({ token, login, register, logout }), [token])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
