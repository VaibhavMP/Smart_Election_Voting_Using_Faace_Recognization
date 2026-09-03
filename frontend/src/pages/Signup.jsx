import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Alert from '../components/Alert'

const initial = {
  name: '',
  dob: '',
  gender: '',
  aadhaar: '',
  voterid: '',
  mobile: '',
  email: '',
  address: '',
  country: 'India',
  password: '',
}

export default function Signup() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(initial)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const update = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await register(form)
      navigate('/face-verify')
    } catch (err) {
      setError(err.message || 'Registration failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page-center">
      <div className="glass-card" style={{ maxWidth: 520 }}>
        <h2>Register Now</h2>
        <p className="subtitle">Create your voting account</p>

        <Alert type="error">{error}</Alert>

        <form className="form" onSubmit={submit}>
          <label>Name</label>
          <input
            type="text"
            value={form.name}
            onChange={update('name')}
            required
            placeholder="Full Name"
          />

          <div className="form-grid">
            <div>
              <label>Date of Birth</label>
              <input type="date" value={form.dob} onChange={update('dob')} required />
            </div>
            <div>
              <label>Gender</label>
              <select value={form.gender} onChange={update('gender')} required>
                <option value="">Select</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div>
              <label>Aadhaar (12 digits)</label>
              <input
                type="text"
                value={form.aadhaar}
                onChange={update('aadhaar')}
                required
                maxLength={12}
                pattern="\d{12}"
                placeholder="12-digit Aadhaar"
              />
            </div>
            <div>
              <label>Voter ID</label>
              <input
                type="text"
                value={form.voterid}
                onChange={update('voterid')}
                required
                placeholder="Voter ID"
              />
            </div>

            <div>
              <label>Mobile (10 digits)</label>
              <input
                type="text"
                value={form.mobile}
                onChange={update('mobile')}
                required
                maxLength={10}
                pattern="\d{10}"
                placeholder="10-digit Mobile"
              />
            </div>
            <div>
              <label>Email</label>
              <input
                type="email"
                value={form.email}
                onChange={update('email')}
                required
                placeholder="your@email.com"
              />
            </div>

            <div className="full">
              <label>Address</label>
              <input
                type="text"
                value={form.address}
                onChange={update('address')}
                required
                placeholder="Your Address"
              />
            </div>

            <div>
              <label>Country</label>
              <input
                type="text"
                value={form.country}
                onChange={update('country')}
                required
              />
            </div>
            <div>
              <label>Password (min 6)</label>
              <input
                type="password"
                value={form.password}
                onChange={update('password')}
                required
                minLength={6}
                placeholder="Password"
              />
            </div>
          </div>

          <button type="submit" className="btn btn-block" disabled={submitting}>
            {submitting ? 'Registering...' : 'Register'}
          </button>
        </form>

        <div className="toggle-text">
          Already have an account? <Link to="/login">Login Here</Link>
        </div>
        <span className="muted">Smart Voting System</span>
      </div>
    </div>
  )
}