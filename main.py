import threading
import time

from src.crypto.keys import get_node_id
from src.network.discovery import Discovery
from src.network.file_transfer import FileTransfer
from src.network.peer_table import PeerTable
from src.network.secure_channel import SecureChannel
from src.security.trust_store import TrustStore


def _maintenance_loop(table, trust_store, running_flag):
    while running_flag["run"]:
        table.clean()
        # Keep trust store hot for future enrichment
        time.sleep(5)


def _print_help():
    print("\nCommandes:")
    print("  help                       Affiche l'aide")
    print("  peers                      Liste les pairs actifs")
    print("  ping <ip>                  Bootstrap direct vers une IP (sans multicast)")
    print("  msg <id_prefix> <texte>    Envoie un message chiffre")
    print("  offer <id_prefix> <path>   Propose un fichier a un pair")
    print("  offers                     Liste les offres de fichiers recues")
    print("  get <offer_id>             Telecharge un fichier offert")
    print("  trust <id_prefix>          Marque un pair comme fiable")
    print("  untrust <id_prefix>        Retire la confiance explicite")
    print("  quit                       Arrete le noeud")


def main():
    my_id = get_node_id()
    print(f"Demarrage Archipel\nMon ID : {my_id}\n" + "-" * 30)

    table = PeerTable()
    trust_store = TrustStore()
    disco = Discovery(my_id, table)
    secure = SecureChannel(my_id, table, trust_store)
    transfer = FileTransfer(my_id, secure)

    running = {"run": True}
    threads = [
        threading.Thread(target=disco.broadcast, daemon=True),
        threading.Thread(target=disco.listen, daemon=True),
        threading.Thread(target=secure.listen, daemon=True),
        threading.Thread(
            target=_maintenance_loop, args=(table, trust_store, running), daemon=True
        ),
    ]
    for t in threads:
        t.start()

    _print_help()
    try:
        while True:
            raw = input("\narchipel> ").strip()
            if not raw:
                continue
            if raw == "help":
                _print_help()
                continue
            if raw == "peers":
                table.display()
                continue
            if raw.startswith("ping "):
                parts = raw.split(" ", 1)
                ip = parts[1].strip()
                try:
                    disco.ping(ip)
                    print(f"HELLO unicast envoye vers {ip}.")
                except Exception as e:
                    print(f"Echec ping: {e}")
                continue
            if raw == "quit":
                break
            if raw.startswith("msg "):
                parts = raw.split(" ", 2)
                if len(parts) < 3:
                    print("Usage: msg <id_prefix> <texte>")
                    continue
                try:
                    peer_id = table.find_by_prefix(parts[1])
                except ValueError as e:
                    print(e)
                    continue
                if not peer_id:
                    print("Pair introuvable.")
                    continue
                try:
                    secure.send_secure_message(peer_id, parts[2])
                    print("Message envoye.")
                except Exception as e:
                    print(f"Echec envoi: {e}")
                continue
            if raw.startswith("trust "):
                parts = raw.split(" ", 1)
                try:
                    peer_id = table.find_by_prefix(parts[1])
                except ValueError as e:
                    print(e)
                    continue
                if not peer_id:
                    print("Pair introuvable.")
                    continue
                trust_store.set_trusted(peer_id, True)
                print(f"Pair {peer_id[:10]}... marque fiable.")
                continue
            if raw.startswith("untrust "):
                parts = raw.split(" ", 1)
                try:
                    peer_id = table.find_by_prefix(parts[1])
                except ValueError as e:
                    print(e)
                    continue
                if not peer_id:
                    print("Pair introuvable.")
                    continue
                trust_store.set_trusted(peer_id, False)
                print(f"Pair {peer_id[:10]}... marque non fiable.")
                continue
            if raw.startswith("offer "):
                parts = raw.split(" ", 2)
                if len(parts) < 3:
                    print("Usage: offer <id_prefix> <path>")
                    continue
                try:
                    peer_id = table.find_by_prefix(parts[1])
                except ValueError as e:
                    print(e)
                    continue
                if not peer_id:
                    print("Pair introuvable.")
                    continue
                try:
                    manifest = transfer.offer_file(peer_id, parts[2])
                    print(
                        f"Offre envoyee: {manifest['offer_id']} "
                        f"({manifest['file_name']}, {manifest['total_chunks']} chunks)"
                    )
                except Exception as e:
                    print(f"Echec offer: {e}")
                continue
            if raw == "offers":
                offers = transfer.list_remote_offers()
                if not offers:
                    print("Aucune offre recue.")
                    continue
                print("\n--- OFFRES DISTANTES ---")
                for o in offers:
                    print(
                        f"{o['offer_id']} | {o['file_name']} | {o['file_size']} o | "
                        f"{o['total_chunks']} chunks | from {o['owner'][:10]}..."
                    )
                continue
            if raw.startswith("get "):
                parts = raw.split(" ", 1)
                offer_id = parts[1].strip()
                try:
                    transfer.request_download(offer_id)
                    print(f"Demande de telechargement envoyee pour {offer_id}.")
                except Exception as e:
                    print(f"Echec get: {e}")
                continue
            print("Commande inconnue. Tape 'help'.")
    except KeyboardInterrupt:
        pass
    finally:
        running["run"] = False
        disco.stop()
        secure.stop()
        print("\nArret du noeud.")


if __name__ == "__main__":
    main()
