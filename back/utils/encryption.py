from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from base64 import b64encode, b64decode


class Encryption:
    def __init__(self, key=None):
        if isinstance(key, str):
            self.key = key.encode("utf-8")  # 将字符串密钥转换为字节
        else:
            self.key = key or get_random_bytes(16)  # 默认生成16字节密钥
        self.block_size = AES.block_size

    def pad(self, data):
        """填充数据到块大小"""
        padding = self.block_size - len(data) % self.block_size
        return data + chr(padding).encode() * padding

    def unpad(self, data):
        """去除填充"""
        return data[:-data[-1]]

    def encrypt(self, plaintext):
        """加密数据"""
        plaintext = self.pad(plaintext.encode())
        iv = get_random_bytes(self.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(plaintext)
        return b64encode(iv + encrypted).decode()

    def decrypt(self, ciphertext):
        """解密数据"""
        ciphertext = b64decode(ciphertext)
        iv = ciphertext[:self.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(ciphertext[self.block_size:])
        return self.unpad(decrypted).decode()
