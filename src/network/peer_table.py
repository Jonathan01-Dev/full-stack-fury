import time

class PeerTable:
    def __init__(self):
        self.peers = {} # {node_id: {"ip": str, "last_seen": float}}

    def update(self, node_id, ip):
        if node_id not in self.peers:
            print(f"\n[+] Nouveau voisin : {node_id[:10]}... @ {ip}")
        self.peers[node_id] = {"ip": ip, "last_seen": time.time()}

    def clean(self):
        """Supprime les pairs inactifs (90s)."""
        now = time.time()
        expired = [nid for nid, info in self.peers.items() if now - info["last_seen"] > 90]
        for nid in expired:
            print(f"\n[-] Pair perdu : {nid[:10]}...")
            del self.peers[nid]

    def display(self):
        if not self.peers:
            print("Recherche de voisins en cours...", end='\r')
        else:
            print("\n--- TABLE DES PAIRS ---")
            for nid, info in self.peers.items():
                print(f"ID: {nid[:10]}... | IP: {info['ip']}")