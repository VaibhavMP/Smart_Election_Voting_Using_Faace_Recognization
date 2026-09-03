import { useState } from 'react'

export function useMessage() {
  const [message, setMessage] = useState(null)

  const show = (type, text, ttl = 4500) => {
    setMessage({ type, text })
    if (ttl) setTimeout(() => setMessage(null), ttl)
  }

  const clear = () => setMessage(null)

  return { message, show, clear }
}