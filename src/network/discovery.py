import socket
import struct
import threading
import time
from src.protocol.packet import pack_hello, unpack_packet

# Configuration officielle du projet
MCAST_GRP = '239.255.42.99'
MCAST_PORT = 6000

class Discovery:
    def __init__(self, node_id, peer_table):
        self.node_id = node_id
        self.peer_table = peer_table
        self.running = True

    def broadcast(self):
        """Envoie un signal HELLO toutes les 2 secondes (plus rapide pour vos tests)."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        
        # TTL à 2 pour passer les petits routeurs/hotspots
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        
        # Activer le mode Broadcast (sécurité supplémentaire pour Windows)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while self.running:
            try:
                packet = pack_hello(self.node_id)
                
                # 1. Envoi au groupe Multicast officiel
                sock.sendto(packet, (MCAST_GRP, MCAST_PORT))
                
                # 2. Envoi en Broadcast général (pour forcer la détection si le Multicast est bloqué)
                sock.sendto(packet, ('255.255.255.255', MCAST_PORT))
                
                time.sleep(2) # On envoie souvent pour le test
            except Exception as e:
                print(f"Erreur lors de l'envoi : {e}")

    def listen(self):
        """Écoute les HELLO des autres voisins."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        
        # Permettre de relancer le script sans attendre que le port se libère
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Écouter sur toutes les interfaces réseau
        sock.bind(('', MCAST_PORT))

        # Configuration du groupe Multicast (Version corrigée pour Windows)
        # On utilise "4s4s" pour éviter les bugs de taille de structure
        mreq = struct.pack("4s4s", socket.inet_aton(MCAST_GRP), socket.inet_aton("0.0.0.0"))
        
        try:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except Exception as e:
            print(f"⚠️ Multicast non supporté, passage en mode UDP standard : {e}")

        print(f"👂 Écoute active sur le port {MCAST_PORT}...")

        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                
                # On décode le paquet binaire
                info = unpack_packet(data)
                
                if info and info["type"] == 0x01: # Si c'est un HELLO
                    remote_id = info["payload"]
                    
                    # On ignore notre propre message
                    if remote_id != self.node_id:
                        # On met à jour la table des pairs avec l'IP de l'expéditeur
                        self.peer_table.update(remote_id, addr[0])
                        
            except Exception as e:
                if self.running:
                    print(f"Erreur réception : {e}")

    def stop(self):
        self.running = False