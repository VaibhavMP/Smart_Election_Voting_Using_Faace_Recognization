import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { voteService } from '../services'
import { useAuth } from '../context/AuthContext'
import Alert from '../components/Alert'

export default function Vote() {
  const navigate = useNavigate()
  const { faceVerified, refresh } = useAuth()
  const [candidates, setCandidates] = useState([])
  const [error, setError] = useState(null)
  const [info, setInfo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        await refresh()
        const data = await voteService.candidates()
        if (!cancelled) setCandidates(data.candidates || [])
      } catch (err) {
        if (!cancelled) {
          if (err.status === 403) {
            setError('Please verify your face before voting.')
            setTimeout(() => navigate('/face-verify', { replace: true }), 1500)
          } else if (err.status === 401) {
            navigate('/login', { replace: true })
          } else {
            setError(err.message || 'Failed to load candidates')
          }
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [navigate, refresh])

  const castVote = async (party) => {
    setError(null)
    setInfo(null)
    setSubmitting(party)
    try {
      const res = await voteService.cast(party)
      setInfo(`You voted for ${res.candidate_name || party}. Redirecting...`)
      setTimeout(() => navigate('/vote-success'), 1200)
    } catch (err) {
      if (err.status === 409) {
        setError('You have already voted.')
      } else if (err.status === 403) {
        setError('Please verify your face first.')
      } else if (err.status === 404) {
        setError('Selected candidate does not exist.')
      } else {
        setError(err.message || 'Failed to record vote')
      }
    } finally {
      setSubmitting(null)
    }
  }

  return (
    <div className="page-center">
      <div className="glass-card" style={{ maxWidth: 560 }}>
        <h1>Select Candidate</h1>
        <p className="subtitle">
          {faceVerified
            ? 'Face verified — you may cast your vote'
            : 'Face verification required to vote'}
        </p>

        <Alert type="error">{error}</Alert>
        <Alert type="success">{info}</Alert>

        {loading ? (
          <div className="status status-pending">Loading candidates...</div>
        ) : (
          <div className="candidate-list">
            {candidates.length === 0 && (
              <div className="status status-pending">
                No candidates available right now.
              </div>
            )}
            {candidates.map((c) => (
              <div className="candidate-row" key={c.id}>
                <div>
                  <div className="candidate-name">{c.name}</div>
                  <div className="muted" style={{ color: '#555' }}>
                    {c.party} {c.symbol && `• ${c.symbol}`}
                  </div>
                </div>
                <button
                  type="button"
                  className="btn btn-success"
                  disabled={!!submitting || !faceVerified}
                  onClick={() => castVote(c.party)}
                >
                  {submitting === c.party ? 'Voting...' : 'Vote'}
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="action-row">
          <Link to="/dashboard" className="btn btn-neutral">
            ← Dashboard
          </Link>
        </div>
      </div>
    </div>
  )
}