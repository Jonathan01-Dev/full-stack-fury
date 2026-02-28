import os
import sys
import threading
import time

from src.crypto.keys import get_node_id
from src.network.discovery import Discovery
from src.network.peer_table import PeerTable
from src.network.transfer import FileTransfer


def main():
    my_id = get_node_id()

    os.system("cls" if os.name == "nt" else "clear")

    print("SYSTEME ARCHIPEL : ACTIVE")
    print(f"ID Local : {my_id}")
    print("Statut   : Securise (Sprint 3 - Signature numerique)")
    print("-" * 50)

    table = PeerTable()
    disco = Discovery(my_id, table)
    transfer = FileTransfer()

    threading.Thread(target=disco.broadcast, daemon=True).start()
    threading.Thread(target=disco.listen, daemon=True).start()
    threading.Thread(target=transfer.start_server, daemon=True).start()

    print("Services de decouverte et de transfert en ligne.")

    try:
        while True:
            print("\n" + "=" * 20 + " MENU " + "=" * 20)
            print("[1] Afficher la table des pairs")
            print("[2] Envoyer un fichier signe")
            print("[Q] Quitter le reseau")

            choix = input("\nAction > ").upper()

            if choix == "1":
                table.clean()
                table.display()
            elif choix == "2":
                table.clean()
                if not table.peers:
                    print("Aucun voisin detecte.")
                    continue

                print("\nVoisins disponibles :")
                for peer_id, info in table.peers.items():
                    print(f" - {info['ip']} (ID: {peer_id[:10]}...)")

                target_ip = input("\nIP du destinataire : ")
                path = input("Chemin du fichier : ")
                transfer.send_file(target_ip, path, my_id)
            elif choix == "Q":
                print("Deconnexion...")
                break
            else:
                print("Option invalide.")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nArret force par l'utilisateur.")
    finally:
        print("Au revoir !")
        sys.exit()


if __name__ == "__main__":
    main()