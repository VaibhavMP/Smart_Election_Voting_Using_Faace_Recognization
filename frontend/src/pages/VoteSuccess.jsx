import { Link, useLocation } from 'react-router-dom'

export default function VoteSuccess() {
  const location = useLocation()
  const party = location.state?.party || 'your candidate'

  return (
    <div className="page-center">
      <div className="glass-card">
        <h1 style={{ color: '#28a745' }}>Congratulations!</h1>
        <p>You have selected</p>
        <div className="party" style={{ fontSize: 22, fontWeight: 600, marginTop: 12, color: '#1e3a8a' }}>
          {party}
        </div>
        <div style={{ color: 'green', marginTop: 20, fontWeight: 'bold' }}>
          Voting Done Successfully!
        </div>
        <Link to="/dashboard" className="btn btn-primary" style={{ marginTop: 20 }}>
          Back to Dashboard
        </Link>
      </div>
    </div>
  )
}