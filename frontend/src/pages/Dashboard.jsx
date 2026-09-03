import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Dashboard() {
  const { user } = useAuth()
  return (
    <div className="page-stack">
      <div className="logo-center">
        <img
          src="/static/images/logo%20for%20indian%20voting%20system.jpg"
          alt="Logo"
        />
      </div>

      <h1 className="dash-title">Smart Voting System</h1>
      <p className="dash-subtitle">Secure • Transparent • Digital</p>

      <div className="dash-welcome">
        Welcome{user?.name ? `, ${user.name}` : ' to your voting dashboard'}
      </div>

      <div className="menu-grid">
        <Link to="/face-verify" className="menu-card">
          <span className="icon">📷</span>
          <span className="title-card">Face Verification</span>
          <span className="description">Verify your identity</span>
        </Link>

        <Link to="/vote" className="menu-card">
          <span className="icon">🗳️</span>
          <span className="title-card">Vote Now</span>
          <span className="description">Cast your vote</span>
        </Link>

        <Link to="/results" className="menu-card">
          <span className="icon">📊</span>
          <span className="title-card">View Results</span>
          <span className="description">See live results</span>
        </Link>

        <Link to="/profile" className="menu-card">
          <span className="icon">👤</span>
          <span className="title-card">My Profile</span>
          <span className="description">View your info</span>
        </Link>
      </div>

      <div className="footer-note">
        <p>India Smart Voting System © 2026</p>
      </div>
    </div>
  )
}