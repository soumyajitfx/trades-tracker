import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [error, setError] = useState('')
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      if (isRegister) await register(username, password)
      else await login(username, password)
      navigate('/dashboard')
    } catch {
      setError('Authentication failed.')
    }
  }

  return (
    <section className="card auth">
      <h1>{isRegister ? 'Create account' : 'Sign in'}</h1>
      <form onSubmit={submit}>
        <input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
        <input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <p className="error">{error}</p>}
        <button type="submit">{isRegister ? 'Register' : 'Login'}</button>
      </form>
      <button className="link-btn" onClick={() => setIsRegister(!isRegister)}>
        {isRegister ? 'Already have an account?' : 'Need an account?'}
      </button>
    </section>
  )
}
