import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div className="page-center">
      <div className="glass-card home-card">
        <h1>Welcome Smart India</h1>
        <div className="btn-pair">
          <Link to="/signup" className="btn btn-success">
            Sign Up
          </Link>
          <Link to="/login" className="btn btn-primary">
            Login
          </Link>
        </div>
      </div>
    </div>
  )
}