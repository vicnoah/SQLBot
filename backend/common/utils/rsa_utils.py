""" 
RSA 加密解密工具类
用于前后端密码传输加密
"""
import base64
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class RSAUtil:
    """RSA 加密解密工具"""
    
    # 密钥存储路径
    KEYS_DIR = Path(__file__).parent.parent.parent / "keys"
    PRIVATE_KEY_FILE = KEYS_DIR / "private_key.pem"
    PUBLIC_KEY_FILE = KEYS_DIR / "public_key.pem"
    
    _private_key: RSAPrivateKey | None = None
    _public_key: RSAPublicKey | None = None
    
    @classmethod
    def _ensure_keys_exist(cls):
        """确保密钥文件存在，如果不存在则生成"""
        cls.KEYS_DIR.mkdir(parents=True, exist_ok=True)
        
        if not cls.PRIVATE_KEY_FILE.exists() or not cls.PUBLIC_KEY_FILE.exists():
            cls._generate_keys()
    
    @classmethod
    def _generate_keys(cls):
        """生成 RSA 密钥对"""
        # 生成私钥
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # 生成公钥
        public_key = private_key.public_key()
        
        # 保存私钥
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        cls.PRIVATE_KEY_FILE.write_bytes(private_pem)
        
        # 保存公钥
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        cls.PUBLIC_KEY_FILE.write_bytes(public_pem)
    
    @classmethod
    def _load_private_key(cls) -> RSAPrivateKey:
        """加载私钥"""
        if cls._private_key is None:
            cls._ensure_keys_exist()
            private_pem = cls.PRIVATE_KEY_FILE.read_bytes()
            loaded_key = serialization.load_pem_private_key(
                private_pem,
                password=None,
                backend=default_backend()
            )
            if not isinstance(loaded_key, RSAPrivateKey):
                raise ValueError("加载的不是 RSA 私钥")
            cls._private_key = loaded_key
        return cls._private_key
    
    @classmethod
    def _load_public_key(cls) -> RSAPublicKey:
        """加载公钥"""
        if cls._public_key is None:
            cls._ensure_keys_exist()
            public_pem = cls.PUBLIC_KEY_FILE.read_bytes()
            loaded_key = serialization.load_pem_public_key(
                public_pem,
                backend=default_backend()
            )
            if not isinstance(loaded_key, RSAPublicKey):
                raise ValueError("加载的不是 RSA 公钥")
            cls._public_key = loaded_key
        return cls._public_key
    
    @classmethod
    def get_public_key_string(cls) -> str:
        """获取公钥字符串（PEM 格式）"""
        cls._ensure_keys_exist()
        return cls.PUBLIC_KEY_FILE.read_text()
    
    @classmethod
    def decrypt(cls, encrypted_text: str) -> str:
        """
        使用私钥解密
        
        Args:
            encrypted_text: Base64 编码的加密文本
            
        Returns:
            解密后的明文
        """
        try:
            private_key = cls._load_private_key()
            encrypted_data = base64.b64decode(encrypted_text)
            
            decrypted_data = private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return decrypted_data.decode('utf-8')
        except Exception as e:
            raise ValueError(f"解密失败: {str(e)}")
    
    @classmethod
    def encrypt(cls, plain_text: str) -> str:
        """
        使用公钥加密（主要用于测试）
        
        Args:
            plain_text: 明文
            
        Returns:
            Base64 编码的加密文本
        """
        try:
            public_key = cls._load_public_key()
            encrypted_data = public_key.encrypt(
                plain_text.encode('utf-8'),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            raise ValueError(f"加密失败: {str(e)}")
