import os
from nacl.signing import SigningKey
from nacl.encoding import HexEncoder

# Le chemin où sera stockée votre identité secrète sur votre PC
KEY_PATH = "data/keys/private.key"

def get_node_id():
    """
    Génère une identité (clé privée) ou récupère celle existante.
    Retourne la clé publique (Node ID) sous forme de texte (hexadécimal).
    """
    
    # 1. Créer le dossier 'data/keys' s'il n'existe pas encore
    dir_name = os.path.dirname(KEY_PATH)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    # 2. Si la clé existe déjà, on la charge
    if os.path.exists(KEY_PATH):
        try:
            with open(KEY_PATH, "rb") as f:
                seed = f.read()
            signing_key = SigningKey(seed)
            print("✅ Identité existante chargée.")
        except Exception as e:
            print(f"⚠️ Erreur de lecture : {e}. Création d'une nouvelle clé...")
            signing_key = SigningKey.generate()
            with open(KEY_PATH, "wb") as f:
                f.write(bytes(signing_key)) # Correction : utilisation de bytes()
    
    # 3. Si la clé n'existe pas, on en crée une nouvelle
    else:
        signing_key = SigningKey.generate()
        with open(KEY_PATH, "wb") as f:
            # ICI LA CORRECTION : on utilise bytes(signing_key) 
            # au lieu de signing_key.tobytes()
            f.write(bytes(signing_key))
        print("✨ Nouvelle identité générée et sauvegardée.")

    # 4. On extrait la clé publique (c'est votre identifiant réseau)
    verify_key = signing_key.verify_key
    
    # 5. On transforme la clé en format lisible (hexadécimal)
    node_id = verify_key.encode(encoder=HexEncoder).decode('utf-8')
    
    return node_id

# Petit test si vous lancez ce fichier tout seul
if __name__ == "__main__":
    print(f"Mon identifiant Archipel est : {get_node_id()}")