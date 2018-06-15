from hashlib import sha256

# 66 extra bytes to pad a SHA1 encoded string to be
def generate_secret_key(passphrase, algorithm_func=sha256):
    return algorithm_func(passphrase.encode('utf-8')).digest()