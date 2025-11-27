/**
 * RSA 加密工具类
 * 使用 node-forge 实现 RSA-OAEP SHA256 加密
 */
import forge from 'node-forge'
import { request } from '@/utils/request'

class RSAEncrypt {
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
   * 使用 RSA-OAEP SHA256 加密
   * @param plainText 要加密的明文字符串
   * @returns 加密后的 Base64 字符串
   */
  static async encrypt(plainText: string): Promise<string> {
    try {
      const publicKeyPEM = await this.getPublicKeyPEM()
      
      // 解析 PEM 格式的公钥
      const publicKey = forge.pki.publicKeyFromPem(publicKeyPEM)
      
      // 执行 RSA-OAEP 加密（使用 SHA256 作为散列函数）
      const encrypted = publicKey.encrypt(plainText, 'RSA-OAEP', {
        md: forge.md.sha256.create(), // OAEP 使用的哈希算法
        mgf1: {
          md: forge.md.sha256.create() // MGF1 使用的哈希算法
        }
      })
      
      // 将加密后的二进制数据转换为 Base64 格式
      return forge.util.encode64(encrypted)
    } catch (error) {
      console.error('加密失败:', error)
      throw error
    }
  }

  /**
   * 加密密码
   */
  static async encryptPassword(password: string): Promise<string> {
    return this.encrypt(password)
  }

  /**
   * 清除缓存
   */
  static clearCache(): void {
    this.publicKeyPEM = null
  }
}

export default RSAEncrypt