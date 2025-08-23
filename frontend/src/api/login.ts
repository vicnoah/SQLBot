import { request } from '@/utils/request'
export const AuthApi = {
  login: (credentials: { username: string; password: string }) => {
    // License functionality removed - use plain credentials
    // FastAPI expects form data format
    const formData = new FormData()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)
    
    return request.post<{
      access_token: string
      token_type: string
    }>('/login/access-token', formData)
  },
  logout: () => request.post('/auth/logout'),
  info: () => request.get('/user/info'),
}
