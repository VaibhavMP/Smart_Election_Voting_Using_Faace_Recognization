import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children, requireFaceVerified = false }) {
  const { user, loading, faceVerified } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="page-center">
        <div className="glass-card">
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  if (requireFaceVerified && !faceVerified) {
    return <Navigate to="/face-verify" replace />
  }

  return children
}