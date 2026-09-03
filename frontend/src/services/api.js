import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      return Promise.reject({
        status: error.response.status,
        message:
          error.response.data?.message ||
          error.response.data?.error ||
          'Request failed',
        data: error.response.data,
      })
    }
    return Promise.reject({
      status: 0,
      message: 'Network error. Please check your connection.',
    })
  }
)

export default api