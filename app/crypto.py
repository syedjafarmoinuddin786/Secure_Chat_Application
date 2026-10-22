# app/crypto.py
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken
from app.config import CONFIG


def derive_key(passphrase: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=CONFIG.SALT,
        iterations=CONFIG.KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


def fernet(passphrase: str) -> Fernet:
    return Fernet(derive_key(passphrase))


def encrypt(fernet_obj: Fernet, msg: str) -> bytes:
    return fernet_obj.encrypt(msg.encode())


def decrypt(fernet_obj: Fernet, data: bytes):
    try:
        return fernet_obj.decrypt(data).decode()
    except InvalidToken:
        return None
