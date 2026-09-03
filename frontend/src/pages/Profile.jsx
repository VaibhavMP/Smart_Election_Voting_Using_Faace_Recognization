import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { profileService } from '../services'
import { useAuth } from '../context/AuthContext'
import { mask } from '../utils/format'
import Alert from '../components/Alert'

export default function Profile() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [profile, setProfile] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const data = await profileService.get()
        if (!cancelled) setProfile(data)
      } catch (err) {
        if (!cancelled) setError(err.message || 'Failed to load profile')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  const handleLogout = async () => {
    await logout()
    navigate('/home', { replace: true })
  }

  return (
    <div className="page-center">
      <div className="glass-card" style={{ maxWidth: 460 }}>
        <Alert type="error">{error}</Alert>

        {loading || !profile ? (
          <div className="status status-pending">Loading profile...</div>
        ) : (
          <>
            <div className="profile-photo">
              {profile.face_exists ? (
                <img
                  src={`/static/data/${profile.user_id}/face.png`}
                  alt="Profile"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none'
                  }}
                />
              ) : (
                <span>👤</span>
              )}
            </div>

            <h2>{profile.user?.name}</h2>
            <p className="muted">Voter ID: {profile.user?.voterid}</p>

            <div className="info-box">
              <div className="info-row">
                <span className="label">Aadhaar</span>
                <span className="value">{mask(profile.user?.aadhaar)}</span>
              </div>
              <div className="info-row">
                <span className="label">Email</span>
                <span className="value">{profile.user?.email}</span>
              </div>
              <div className="info-row">
                <span className="label">Phone</span>
                <span className="value">{profile.user?.mobile}</span>
              </div>
              <div className="info-row">
                <span className="label">Voting Status</span>
                <span className="value">
                  {profile.user?.has_voted === 1 ? (
                    <span className="badge badge-success">Voted ✓</span>
                  ) : (
                    <span className="badge badge-warning">Not Voted</span>
                  )}
                </span>
              </div>
            </div>

            <div className="action-row">
              <button type="button" className="btn btn-danger" onClick={handleLogout}>
                Logout
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}