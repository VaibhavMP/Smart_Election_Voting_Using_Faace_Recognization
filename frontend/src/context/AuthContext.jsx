import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { authService } from '../services'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [faceVerified, setFaceVerified] = useState(false)
  const [justRegistered, setJustRegistered] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const data = await authService.me()
      setUser(data.user || null)
      setFaceVerified(Boolean(data.face_verified))
      setJustRegistered(Boolean(data.just_registered))
    } catch (err) {
      setUser(null)
      setFaceVerified(false)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const login = useCallback(
    async (creds) => {
      const data = await authService.login(creds)
      setUser(data.user)
      setFaceVerified(false)
      setJustRegistered(false)
      return data
    },
    [],
  )

  const register = useCallback(async (payload) => {
    const data = await authService.register(payload)
    setUser(data.user)
    setFaceVerified(false)
    setJustRegistered(true)
    return data
  }, [])

  const logout = useCallback(async () => {
    try {
      await authService.logout()
    } finally {
      setUser(null)
      setFaceVerified(false)
      setJustRegistered(false)
    }
  }, [])

  const markFaceVerified = useCallback(() => setFaceVerified(true), [])
  const clearJustRegistered = useCallback(() => setJustRegistered(false), [])

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        faceVerified,
        justRegistered,
        login,
        register,
        logout,
        refresh,
        markFaceVerified,
        clearJustRegistered,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}