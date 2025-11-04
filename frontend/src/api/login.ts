import { request } from '@/utils/request'
import RSAEncrypt from '@/utils/encrypt'

export const AuthApi = {
  login: async (credentials: { username: string; password: string }) => {
    // 使用 RSA 加密密码
    const encryptedPassword = await RSAEncrypt.encryptPassword(credentials.password)
    
    // FastAPI expects form data format
    const formData = new FormData()
    formData.append('username', credentials.username)
    formData.append('password', encryptedPassword)
    
    return request.post<{
      access_token: string
      token_type: string
    }>('/login/access-token', formData)
  },
  logout: () => request.post('/auth/logout'),
  info: () => request.get('/user/info'),
}
