import threading
import time
from src.crypto.keys import get_node_id
from src.network.peer_table import PeerTable
from src.network.discovery import Discovery

def main():
    # 1. Obtenir l'identité
    my_id = get_node_id()
    print(f"Démarrage Archipel\nMon ID : {my_id}\n" + "-"*30)

    # 2. Initialiser les modules
    table = PeerTable()
    disco = Discovery(my_id, table)

    # 3. Lancer les threads réseau
    threading.Thread(target=disco.broadcast, daemon=True).start()
    threading.Thread(target=disco.listen, daemon=True).start()

    # 4. Boucle d'affichage
    try:
        while True:
            table.clean()
            table.display()
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nArrêt du nœud.")

if __name__ == "__main__":
    main()