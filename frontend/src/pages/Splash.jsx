import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Splash() {
  const navigate = useNavigate()

  useEffect(() => {
    const t = setTimeout(() => navigate('/home', { replace: true }), 3000)
    return () => clearTimeout(t)
  }, [navigate])

  return (
    <div className="splash">
      <div className="logo-circle">
        <img
          src="/static/images/logo%20for%20indian%20voting%20system.jpg"
          alt="Logo"
        />
      </div>
      <h1>Smart Election Voting</h1>
      <p>Secure • Transparent • Digital</p>
    </div>
  )
}