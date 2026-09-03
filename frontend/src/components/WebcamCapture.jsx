import { useEffect, useRef, useState, useCallback } from 'react'

export default function WebcamCapture({
  onCapture,
  captureLabel = 'Capture Photo',
  verifyLabel = 'Verify & Continue',
  onVerify,
  verifyDisabled = false,
  statusMessage,
  showSkip = false,
  onSkip,
}) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const [captured, setCaptured] = useState(null) // dataURL
  const [cameraError, setCameraError] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function start() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 480, height: 480 },
          audio: false,
        })
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop())
          return
        }
        streamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
        }
      } catch (err) {
        setCameraError(
          'Camera access denied or unavailable. Please allow camera permissions and try again.',
        )
      }
    }
    start()
    return () => {
      cancelled = true
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop())
      }
    }
  }, [])

  const handleCapture = useCallback(() => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return
    const w = video.videoWidth || 480
    const h = video.videoHeight || 480
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, w, h)
    const dataUrl = canvas.toDataURL('image/png')
    setCaptured(dataUrl)
    if (onCapture) onCapture(dataUrl)
  }, [onCapture])

  const handleRetake = useCallback(() => {
    setCaptured(null)
    if (onCapture) onCapture(null)
  }, [onCapture])

  const handleVerify = useCallback(() => {
    if (!captured || verifyDisabled) return
    if (onVerify) onVerify(captured)
  }, [captured, verifyDisabled, onVerify])

  return (
    <div>
      <div className="camera-box">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={captured ? 'hidden' : ''}
        />
        {captured && (
          <img
            src={captured}
            alt="Captured"
            className="captured-image visible"
          />
        )}
        <canvas ref={canvasRef} style={{ display: 'none' }} />
      </div>

      {cameraError && <div className="status status-error">{cameraError}</div>}

      {statusMessage && (
        <div className={`status status-${statusMessage.type || 'pending'}`}>
          {statusMessage.text}
        </div>
      )}

      <div className="btn-row">
        {!captured && (
          <button
            type="button"
            className="btn btn-success"
            onClick={handleCapture}
            disabled={!!cameraError}
          >
            {captureLabel}
          </button>
        )}
        {captured && (
          <>
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleVerify}
              disabled={verifyDisabled}
            >
              {verifyLabel}
            </button>
            <button
              type="button"
              className="btn btn-neutral"
              onClick={handleRetake}
            >
              Retake
            </button>
          </>
        )}
      </div>

      {showSkip && onSkip && (
        <a
          href="#"
          className="back-link"
          onClick={(e) => {
            e.preventDefault()
            onSkip()
          }}
        >
          Skip for now — Login
        </a>
      )}
    </div>
  )
}