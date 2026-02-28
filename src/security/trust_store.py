import json
import os
import time


TRUST_PATH = "data/trust/trust_store.json"


class TrustStore:
    def __init__(self, path=TRUST_PATH):
        self.path = path
        self._data = {"peers": {}}
        self._load()

    def _load(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {"peers": {}}
        else:
            self._save()

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def check_or_trust_first_use(self, node_id):
        peers = self._data.setdefault("peers", {})
        if node_id in peers:
            return True, "known"
        peers[node_id] = {
            "trusted": False,
            "first_seen": int(time.time()),
            "last_seen": int(time.time()),
        }
        self._save()
        return True, "first_seen"

    def mark_seen(self, node_id):
        peers = self._data.setdefault("peers", {})
        if node_id in peers:
            peers[node_id]["last_seen"] = int(time.time())
            self._save()

    def set_trusted(self, node_id, trusted=True):
        peers = self._data.setdefault("peers", {})
        if node_id not in peers:
            peers[node_id] = {}
        peers[node_id]["trusted"] = bool(trusted)
        peers[node_id]["last_seen"] = int(time.time())
        self._save()

    def is_trusted(self, node_id):
        return bool(self._data.get("peers", {}).get(node_id, {}).get("trusted", False))
