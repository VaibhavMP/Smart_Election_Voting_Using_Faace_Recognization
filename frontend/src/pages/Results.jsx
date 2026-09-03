import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { voteService } from '../services'
import Alert from '../components/Alert'

export default function Results() {
  const [results, setResults] = useState([])
  const [total, setTotal] = useState(0)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const data = await voteService.results()
        if (!cancelled) {
          setResults(data.results || [])
          setTotal(data.total_votes || 0)
        }
      } catch (err) {
        if (!cancelled) setError(err.message || 'Failed to load results')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="page-center">
      <div className="glass-card" style={{ maxWidth: 620 }}>
        <h1>Voting Results</h1>

        <Alert type="error">{error}</Alert>

        {loading ? (
          <div className="status status-pending">Loading results...</div>
        ) : (
          <div>
            {results.map((r, i) => {
              const pct = total > 0 ? (r.votes / total) * 100 : 0
              return (
                <div className="result-row" key={r.party || i}>
                  <div style={{ flex: 1 }}>
                    <div className="candidate-name">
                      {r.name} ({r.party})
                    </div>
                    <div className="bar-container">
                      <div className="bar" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                  <div className="result-votes">{r.votes}</div>
                </div>
              )
            })}
            <div className="total-votes">Total Votes: {total}</div>
          </div>
        )}

        <div className="action-row">
          <Link to="/dashboard" className="btn btn-primary">
            Back to Dashboard
          </Link>
        </div>
      </div>
    </div>
  )
}