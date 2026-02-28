import os

from nacl.encoding import HexEncoder
from nacl.signing import SigningKey

KEY_PATH = "data/keys/private.key"


def get_node_id():
    """
    Genere une identite locale (cle privee) ou recharge celle existante.
    Retourne la cle publique (Node ID) en hexadecimal.
    """
    dir_name = os.path.dirname(KEY_PATH)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    if os.path.exists(KEY_PATH):
        try:
            with open(KEY_PATH, "rb") as f:
                seed = f.read()
            signing_key = SigningKey(seed)
            print("Identite existante chargee.")
        except Exception as e:
            print(f"Erreur lecture cle: {e}. Nouvelle cle creee.")
            signing_key = SigningKey.generate()
            with open(KEY_PATH, "wb") as f:
                f.write(bytes(signing_key))
    else:
        signing_key = SigningKey.generate()
        with open(KEY_PATH, "wb") as f:
            f.write(bytes(signing_key))
        print("Nouvelle identite generee et sauvegardee.")

    verify_key = signing_key.verify_key
    node_id = verify_key.encode(encoder=HexEncoder).decode("utf-8")
    return node_id


if __name__ == "__main__":
    print(f"Mon identifiant Archipel est : {get_node_id()}")
