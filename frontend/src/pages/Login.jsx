import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Alert from '../components/Alert'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/dashboard'

  const [form, setForm] = useState({ voterid: '', password: '' })
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const update = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(form)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err.message || 'Invalid credentials')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page-center">
      <div className="glass-card">
        <h2>Login</h2>
        <p className="subtitle">Access your voting account</p>

        <Alert type="error">{error}</Alert>

        <form className="form" onSubmit={submit}>
          <label>Voter ID or Aadhaar</label>
          <input
            type="text"
            value={form.voterid}
            onChange={update('voterid')}
            required
            placeholder="Enter Voter ID or Aadhaar"
          />

          <label>Password</label>
          <input
            type="password"
            value={form.password}
            onChange={update('password')}
            required
            placeholder="Enter Password"
          />

          <button
            type="submit"
            className="btn btn-block"
            disabled={submitting}
          >
            {submitting ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="toggle-text">
          New User? <Link to="/signup">Register Here</Link>
        </div>
        <span className="muted">Smart Voting System</span>
      </div>
    </div>
  )
}