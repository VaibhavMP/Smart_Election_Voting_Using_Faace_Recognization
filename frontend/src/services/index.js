import api from './api'

export const authService = {
  register: (payload) => api.post('/auth/register', payload).then((r) => r.data),
  login: (payload) => api.post('/auth/login', payload).then((r) => r.data),
  logout: () => api.post('/auth/logout').then((r) => r.data),
  me: () => api.get('/auth/me').then((r) => r.data),
}

export const faceService = {
  register: (imageDataUrl) =>
    api.post('/face/register', { image: imageDataUrl }).then((r) => r.data),
  verify: (imageDataUrl) =>
    api.post('/face/verify', { image: imageDataUrl }).then((r) => r.data),
}

export const profileService = {
  get: () => api.get('/profile').then((r) => r.data),
}

export const voteService = {
  candidates: () => api.get('/candidates').then((r) => r.data),
  cast: (party) => api.post('/vote', { candidate: party }).then((r) => r.data),
  results: () => api.get('/results').then((r) => r.data),
}

export const healthService = {
  check: () => api.get('/health').then((r) => r.data),
}