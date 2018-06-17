import base64
from Crypto.Cipher import AES
from Crypto import Random


class AESCipher(object):
    def __init__(self, key, block_size=128):
        if len(key) >= len(str(block_size)):
            self.key = key[:block_size]
        else:
            self.key = self._pad(key, block_size)

    def encrypt(self, raw, mode=AES.MODE_CBC):
        raw = self._pad(raw, 128)

        # Pycrypto's documentation is wrong. It says an initialization vector (IV) is not required for encryption/decryption... but it is.
        # See: https://stackoverflow.com/questions/14389336/why-does-pycrypto-not-use-the-default-iv
        # To initialize the cipher with a null value, the iv must be a 16 byte sized array of all 0's
        iv = 16 * '\x00'
        cipher = AES.new(self.key, mode, iv)
        return base64.b64encode(cipher.encrypt(raw)).decode('utf-8')

    def decrypt(self, enc, mode=AES.MODE_CBC):
        enc = base64.b64decode(enc)
        iv = 16 * '\x00'
        cipher = AES.new(self.key, mode, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, data, block_size):
        """
        Pad the input data to be a multiple of the cipher block size using PKCS7
        :param data:
        :param block_size:
        :return:
        """
        return data + (block_size - len(data) % block_size) * chr(block_size - len(data) % block_size)


    def _unpad(self, data):
        return data[:-ord(data[len(data) - 1:])]