import os

from nacl.encoding import HexEncoder
from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

KEY_PATH = "data/keys/private.key"


def get_signing_key():
    if not os.path.exists(KEY_PATH):
        os.makedirs(os.path.dirname(KEY_PATH), exist_ok=True)
        signing_key = SigningKey.generate()
        with open(KEY_PATH, "wb") as f:
            f.write(bytes(signing_key))
        return signing_key

    with open(KEY_PATH, "rb") as f:
        return SigningKey(f.read())


def get_node_id():
    signing_key = get_signing_key()
    verify_key = signing_key.verify_key
    return verify_key.encode(encoder=HexEncoder).decode("utf-8")


def sign_file(file_data):
    signing_key = get_signing_key()
    signature = signing_key.sign(file_data).signature
    return signature.hex()


def verify_file(file_data, signature_hex, sender_public_key_hex):
    try:
        verify_key = VerifyKey(sender_public_key_hex, encoder=HexEncoder)
        verify_key.verify(file_data, bytes.fromhex(signature_hex))
        return True
    except (BadSignatureError, Exception):
        return False


if __name__ == "__main__":
    print(f"Mon identifiant Archipel est : {get_node_id()}")
