import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="page-center">
      <div className="glass-card">
        <h1 style={{ color: '#dc3545', fontSize: 48 }}>Oops!</h1>
        <p>Page not found</p>
        <Link to="/home" className="btn btn-primary" style={{ marginTop: 16 }}>
          Go Home
        </Link>
      </div>
    </div>
  )
}