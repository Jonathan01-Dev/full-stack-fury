import threading
import time
from src.crypto.keys import get_node_id
from src.network.discovery import Discovery
from src.network.peer_table import PeerTable
from src.network.secure_channel import SecureChannel
from src.security.trust_store import TrustStore
from src.network.file_transfer import FileTransfer
from src.security.gemini_client import GeminiClient

class ArchipelNode:
    def __init__(self, port=6000, no_ai=False):
        self.my_id = get_node_id()
        self.mcast_port = port
        self.secure_port = port + 1
        
        self.table = PeerTable()
        self.trust_store = TrustStore()
        self.disco = Discovery(self.my_id, self.table, mcast_port=self.mcast_port)
        self.secure = SecureChannel(self.my_id, self.table, self.trust_store, secure_port=self.secure_port)
        self.transfer = FileTransfer(self.my_id, self.secure)
        self.gemini = GeminiClient(enabled=not no_ai)
        
        self.running = {"run": True}
        self.threads = []
        self.messages = [] 
        self.logs = []
        self.start_time = time.time()

        # Enregistrement des handlers
        self.secure.register_handler("chat", self._on_message)
        self.log(f"Nœud initialisé. ID: {self.my_id[:10]}...")

    def log(self, text):
        entry = {"time": time.time(), "text": text}
        self.logs.append(entry)
        if len(self.logs) > 100: self.logs.pop(0)
        print(f"[*] {text}")

    def add_message(self, sender, text, target="Global"):
        msg = {
            "from": sender, 
            "to": target,
            "text": text, 
            "time": time.time()
        }
        self.messages.append(msg)
        if len(self.messages) > 200: self.messages.pop(0)

    def _on_message(self, peer_id, obj):
        text = obj.get("text", "")
        self.add_message(peer_id, text, target=self.my_id)
        self.log(f"Message reçu de {peer_id[:8]}")

    def start(self):
        self.threads = [
            threading.Thread(target=self.disco.broadcast, daemon=True),
            threading.Thread(target=self.disco.listen, daemon=True),
            threading.Thread(target=self.secure.listen, daemon=True),
            threading.Thread(target=self._maintenance_loop, daemon=True),
        ]
        for t in self.threads: t.start()
        self.log("Services réseau démarrés.")

    def _maintenance_loop(self):
        while self.running["run"]:
            self.table.clean()
            time.sleep(5)

    def stop(self):
        self.running["run"] = False
        self.disco.stop()
        self.secure.stop()
        self.log("Arrêt du nœud.")

    def get_status(self):
        uptime = int(time.time() - self.start_time)
        return {
            "id": self.my_id,
            "port_disco": self.mcast_port,
            "port_secure": self.secure_port,
            "peers_count": len(self.table.list_peers()),
            "trusted_count": len([p for p in self.table.list_peers() if self.trust_store.is_trusted(p['id'])]),
            "ai_enabled": self.gemini.is_available(),
            "uptime": uptime,
            "transfers_active": len(self.transfer.downloads)
        }
