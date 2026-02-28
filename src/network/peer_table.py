import threading
import time


class PeerTable:
    def __init__(self):
        self.peers = {}  # {node_id: {"ip": str, "port": int, "last_seen": float}}
        self._lock = threading.Lock()

    def update(self, node_id, ip, port=6001):
        with self._lock:
            if node_id not in self.peers:
                print(f"\n[+] Nouveau voisin : {node_id[:10]}... @ {ip}:{port}")
            self.peers[node_id] = {"ip": ip, "port": port, "last_seen": time.time()}

    def clean(self):
        now = time.time()
        with self._lock:
            expired = [
                nid
                for nid, info in self.peers.items()
                if now - info["last_seen"] > 90
            ]
            for nid in expired:
                print(f"\n[-] Pair perdu : {nid[:10]}...")
                del self.peers[nid]

    def display(self):
        with self._lock:
            if not self.peers:
                print("Recherche de voisins en cours...", end="\r")
                return
            print("\n--- TABLE DES PAIRS ---")
            for nid, info in self.peers.items():
                print(f"ID: {nid[:10]}... | IP: {info['ip']}:{info['port']}")

    def list_peers(self):
        """Retourne la liste des pairs sous forme de dictionnaires pour l'UI."""
        with self._lock:
            return [
                {"id": nid, "ip": info["ip"], "port": info.get("port", 6001), "last_seen": info["last_seen"]}
                for nid, info in self.peers.items()
            ]

    def find_by_prefix(self, prefix):
        with self._lock:
            matches = [nid for nid in self.peers.keys() if nid.startswith(prefix)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ValueError("Prefixe ambigu, sois plus specifique.")
        return None

    def get_peer(self, node_id):
        with self._lock:
            peer = self.peers.get(node_id)
            if not peer:
                return None
            return dict(peer)
