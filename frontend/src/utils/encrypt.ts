/**
 * RSA 加密工具类
 * 使用 Web Crypto API 实现 RSAOAEP 加密
 * 用于登录密码加密传输
 */
import { request } from '@/utils/request'

/**
 * RSA 加密工具
 */
class RSAEncrypt {
  private static publicKey: CryptoKey | null = null
  private static publicKeyPEM: string | null = null

  /**
   * 获取公钥 PEM 字符串
   */
  private static async getPublicKeyPEM(): Promise<string> {
    if (!this.publicKeyPEM) {
      try {
        const response = await request.get<{ public_key: string }>('/login/public-key')
        this.publicKeyPEM = response.public_key
      } catch (error) {
        console.error('获取公钥失败:', error)
        throw new Error('获取公钥失败')
      }
    }
    return this.publicKeyPEM
  }

  /**
   * 从 PEM 格式导入公钥
   */
  private static async importPublicKey(): Promise<CryptoKey> {
    if (!this.publicKey) {
      try {
        const pem = await this.getPublicKeyPEM()
        
        // 移除 PEM 头尾和换行符
        const pemContents = pem
          .replace(/-----BEGIN PUBLIC KEY-----/, '')
          .replace(/-----END PUBLIC KEY-----/, '')
          .replace(/\s/g, '')

        // Base64 解码
        const binaryDer = Uint8Array.from(atob(pemContents), c => c.charCodeAt(0))
        
        // 导入公钥
        this.publicKey = await window.crypto.subtle.importKey(
          'spki',
          binaryDer,
          {
            name: 'RSA-OAEP',
            hash: 'SHA-256'
          },
          true,
          ['encrypt']
        )
      } catch (err) {
        console.error('公钥导入失败:', err)
        throw new Error(`公钥导入失败: ${err}`)
      }
    }
    return this.publicKey
  }

  /**
   * 加密字符串
   * @param plainText 明文
   * @returns 加密后的密文（Base64 编码）
   */
  static async encrypt(plainText: string): Promise<string> {
    try {
      const publicKey = await this.importPublicKey()
      
      // 将字符串转换为 Uint8Array
      const encoder = new TextEncoder()
      const dataBuffer = encoder.encode(plainText)

      // 使用 RSA-OAEP 加密
      const encryptedBuffer = await window.crypto.subtle.encrypt(
        { 
            name: 'RSA-OAEP'
        },
        publicKey,
        dataBuffer
      )

      // 转换为 Base64
      const encryptedBase64 = btoa(String.fromCharCode(...new Uint8Array(encryptedBuffer)))
      
      return encryptedBase64
    } catch (error) {
      console.error('加密失败:', error)
      throw error
    }
  }

  /**
   * 加密密码
   * @param password 密码明文
   * @returns 加密后的密码
   */
  static async encryptPassword(password: string): Promise<string> {
    return this.encrypt(password)
  }

  /**
   * 清除缓存的公钥（用于测试或重新初始化）
   */
  static clearCache(): void {
    this.publicKey = null
    this.publicKeyPEM = null
  }
}

export default RSAEncrypt
