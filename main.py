import argparse
import os
import sys
from dotenv import load_dotenv

from src.node import ArchipelNode
from src.ui.web_server import start_web_server

load_dotenv()

def _print_help():
    print("\nCommandes Archipel CLI :")
    print("  help                       Affiche l'aide")
    print("  peers                      Liste les pairs découverts")
    print("  msg <node_id> <texte>      Envoie un message chiffré")
    print("  send <node_id> <path>      Propose un fichier à un pair")
    print("  receive                    Liste les offres de fichiers reçues")
    print("  download <offer_id>        Télécharge un fichier offert")
    print("  status                     État du nœud + stats réseau")
    print("  trust <node_id>            Approuve un pair (Web of Trust)")
    print("  untrust <node_id>          Retire la confiance explicite")
    print("  ping <ip>                  Bootstrap direct vers une IP")
    print("  /ask <question>            Interroge l'IA Gemini (@archipel-ai aussi)")
    print("  quit                       Arrête le nœud")

def main():
    parser = argparse.ArgumentParser(description="Archipel P2P Node")
    parser.add_argument("--port", type=int, default=6000, help="Port de base pour le nœud")
    parser.add_argument("--web-port", type=int, default=5000, help="Port pour l'interface Web")
    parser.add_argument("--no-ai", action="store_true", help="Désactive l'intégration Gemini AI")
    args = parser.parse_args()

    node = ArchipelNode(port=args.port, no_ai=args.no_ai)
    
    print(f"Démarrage Archipel\nMon ID : {node.my_id}\n" + "-" * 30)
    
    # Lancement du moteur P2P
    node.start()
    
    # Lancement de l'interface Web (en arrière-plan)
    start_web_server(node, port=args.web_port)

    _print_help()
    
    try:
        while True:
            raw = input(f"\narchipel[{node.my_id[:8]}]> ").strip()
            if not raw: continue
            
            # Gemini triggers
            if raw.startswith("@archipel-ai") or raw.startswith("/ask"):
                query = raw.replace("@archipel-ai", "").replace("/ask", "").strip()
                if not query:
                    print("Usage: /ask <question>")
                    continue
                print("[IA] Réflexion...")
                print(f"[IA] Gemini: {node.gemini.query(query)}")
                continue

            if raw == "help":
                _print_help()
            elif raw == "status":
                s = node.get_status()
                print("\n--- ÉTAT DU NŒUD ---")
                print(f"ID : {s['id']}")
                print(f"Port Discovery : {s['port_disco']}")
                print(f"Port Sécurisé  : {s['port_secure']}")
                print(f"Pairs Actifs   : {s['peers_count']}")
                print(f"Confiance      : {s['trusted_count']} pairs")
                print(f"IA Gemini      : {'ON' if s['ai_enabled'] else 'OFF'}")
            elif raw == "peers":
                node.table.display()
            elif raw.startswith("ping "):
                ip = raw.split(" ", 1)[1].strip()
                try:
                    node.disco.ping(ip)
                    print(f"HELLO unicast envoyé vers {ip}")
                except Exception as e: print(f"Erreur: {e}")
            elif raw == "quit":
                break
            elif raw.startswith("msg "):
                parts = raw.split(" ", 2)
                if len(parts) < 3: continue
                try:
                    peer_id = node.table.find_by_prefix(parts[1])
                    if peer_id:
                        node.secure.send_secure_message(peer_id, parts[2])
                        print("Message envoyé.")
                    else: print("Pair introuvable.")
                except Exception as e: print(f"Erreur: {e}")
            elif raw.startswith("trust "):
                pid = raw.split(" ", 1)[1].strip()
                try:
                    peer_id = node.table.find_by_prefix(pid)
                    if peer_id:
                        node.trust_store.set_trusted(peer_id, True)
                        print(f"Pair {peer_id[:10]}... marqué fiable.")
                except Exception as e: print(f"Erreur: {e}")
            elif raw.startswith("send "):
                parts = raw.split(" ", 2)
                if len(parts) < 3: continue
                try:
                    peer_id = node.table.find_by_prefix(parts[1])
                    if peer_id:
                        node.transfer.offer_file(peer_id, parts[2])
                    else: print("Pair introuvable.")
                except Exception as e: print(f"Erreur: {e}")
            elif raw == "receive":
                offers = node.transfer.list_remote_offers()
                if not offers: print("Aucune offre.")
                else:
                    for o in offers:
                        print(f"{o['offer_id']} | {o['file_name']} | {o['file_size']} o | from {o['owner'][:10]}...")
            elif raw.startswith("download "):
                oid = raw.split(" ", 1)[1].strip()
                try:
                    node.transfer.request_download(oid)
                    print(f"Téléchargement lancé pour {oid}")
                except Exception as e: print(f"Erreur: {e}")
            else:
                print("Commande inconnue. Tape 'help'.")
                
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        print("\nArrêt.")

if __name__ == "__main__":
    main()
