import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { faceService } from '../services'
import WebcamCapture from '../components/WebcamCapture'

export default function FaceVerify() {
  const { user, justRegistered, markFaceVerified, clearJustRegistered, refresh } =
    useAuth()
  const navigate = useNavigate()

  const [image, setImage] = useState(null)
  const [status, setStatus] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const isRegistration = justRegistered

  const handleVerify = async (dataUrl) => {
    setSubmitting(true)
    setStatus({ type: 'pending', text: isRegistration ? 'Saving profile photo...' : 'Verifying face...' })
    try {
      if (isRegistration) {
        await faceService.register(dataUrl)
        clearJustRegistered()
        setStatus({ type: 'success', text: 'Profile photo saved! Redirecting to login...' })
        setTimeout(() => navigate('/login', { replace: true }), 1500)
      } else {
        const res = await faceService.verify(dataUrl)
        if (res.success) {
          markFaceVerified()
          await refresh()
          setStatus({ type: 'success', text: 'Face verified! Redirecting to vote...' })
          setTimeout(() => navigate('/vote', { replace: true }), 1200)
        } else {
          setStatus({ type: 'error', text: res.message || 'Verification failed' })
          setImage(null)
        }
      }
    } catch (err) {
      setStatus({ type: 'error', text: err.message || 'Verification failed' })
      setImage(null)
    } finally {
      setSubmitting(false)
    }
  }

  const handleSkip = () => navigate('/login', { replace: true })

  return (
    <div className="page-center">
      <div className="glass-card">
        <h1>{isRegistration ? 'Profile Photo' : 'Face Verification'}</h1>
        <p className="subtitle">
          {isRegistration
            ? `Capture your profile photo for your account (${user?.name || ''})`
            : 'Align your face inside the circle'}
        </p>

        <WebcamCapture
          onCapture={setImage}
          captureLabel="Capture Photo"
          verifyLabel={
            submitting
              ? 'Please wait...'
              : isRegistration
              ? 'Save Profile Photo'
              : 'Verify & Vote'
          }
          onVerify={handleVerify}
          verifyDisabled={submitting}
          statusMessage={status}
          showSkip={isRegistration}
          onSkip={handleSkip}
        />

        {!isRegistration && (
          <Link to="/dashboard" className="back-link">
            ← Back to Dashboard
          </Link>
        )}
      </div>
    </div>
  )
}