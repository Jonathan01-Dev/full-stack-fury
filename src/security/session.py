import hashlib
import hmac
import os

from nacl.bindings import crypto_scalarmult
from nacl.public import PrivateKey
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import HKDF
from Crypto.Hash import SHA256


def generate_ephemeral_keypair():
    priv = PrivateKey.generate()
    return bytes(priv), bytes(priv.public_key)


def derive_session_keys(local_private_key, remote_public_key, transcript):
    """
    Derive 2 keys from X25519 shared secret:
    - enc_key (AES-256-GCM)
    - mac_key (HMAC-SHA256)
    """
    shared_secret = crypto_scalarmult(local_private_key, remote_public_key)
    okm = HKDF(
        master=shared_secret,
        key_len=64,
        salt=hashlib.sha256(transcript).digest(),
        hashmod=SHA256,
        context=b"archipel-session-v1",
    )
    return okm[:32], okm[32:]


def encrypt_payload(enc_key, mac_key, plaintext):
    nonce = os.urandom(12)
    cipher = AES.new(enc_key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    mac = hmac.new(mac_key, nonce + ciphertext + tag, hashlib.sha256).digest()
    return nonce, ciphertext, tag, mac


def decrypt_payload(enc_key, mac_key, nonce, ciphertext, tag, mac):
    expected = hmac.new(mac_key, nonce + ciphertext + tag, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, mac):
        raise ValueError("HMAC invalide")
    cipher = AES.new(enc_key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)
