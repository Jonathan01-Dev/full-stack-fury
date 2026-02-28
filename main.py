import threading
import time
import sys
from src.crypto.keys import get_node_id
from src.network.peer_table import PeerTable
from src.network.discovery import Discovery
from src.network.transfer import FileTransfer 

def main():
    # 1. Obtenir l'identité
    my_id = get_node_id()
    print(f"🚀 Démarrage Archipel")
    print(f"Mon ID : {my_id}")
    print("-" * 35)

    # 2. Initialiser les modules
    table = PeerTable()
    disco = Discovery(my_id, table)
    transfer = FileTransfer() # Nouveau module de transfert

    # 3. Lancer les threads réseau
    # Thread 1 : Envoi des HELLO (UDP)
    threading.Thread(target=disco.broadcast, daemon=True).start()
    
    # Thread 2 : Écoute des HELLO (UDP)
    threading.Thread(target=disco.listen, daemon=True).start()
    
    # Thread 3 : Serveur de fichiers (TCP) - NOUVEAU
    threading.Thread(target=transfer.start_server, daemon=True).start()

    print("✅ Services Discovery et Transfert actifs.")
    print("Tapez 'send <IP> <chemin_fichier>' pour envoyer un fichier.")

    # 4. Boucle d'affichage et interaction
    try:
        while True:
            # On affiche la table de temps en temps
            table.clean()
            table.display()
            
            # Petit menu interactif simple
            print("\nOptions: [1] Actualiser [2] Envoyer fichier [Q] Quitter")
            choix = input("Choix : ").upper()

            if choix == "2":
                target_ip = input("IP du destinataire : ")
                path = input("Chemin du fichier : ")
                transfer.send_file(target_ip, path)
            elif choix == "Q":
                break
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt du nœud.")
        sys.exit()

if __name__ == "__main__":
    main()