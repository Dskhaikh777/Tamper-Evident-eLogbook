import axios from "axios"

export const axiosClient = axios.create({
  baseURL: "http://localhost:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
})

// Inject JWT token into every request if authenticated
axiosClient.interceptors.request.use(
  (config) => {
    try {
      const storedAuth = localStorage.getItem("elogbook_auth")
      if (storedAuth) {
        const authState = JSON.parse(storedAuth)
        if (authState?.accessToken) {
          config.headers.Authorization = `Bearer ${authState.accessToken}`
        }
      }
    } catch (err) {
      // Ignore parsing errors
    }
    return config
  },
  (error) => Promise.reject(error)
)

axiosClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Centralized error handling
    if (error.response?.status === 401 || error.response?.status === 403) {
      // Potentially dispatch a logout action or redirect to login here
    }
    return Promise.reject(error)
  }
)
