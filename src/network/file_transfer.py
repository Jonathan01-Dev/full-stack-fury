import hashlib
import os
import threading
import time

from src.file.chunker import assemble_file, build_manifest, read_chunk_at


class FileTransfer:
    def __init__(self, node_id, secure_channel):
        self.node_id = node_id
        self.secure = secure_channel

        self.share_dir = "data/share"
        self.download_dir = "data/downloads"
        os.makedirs(self.share_dir, exist_ok=True)
        os.makedirs(self.download_dir, exist_ok=True)

        self._lock = threading.Lock()
        self.local_offers = {}  # offer_id -> {"manifest": dict, "file_path": str}
        self.remote_offers = {}  # offer_id -> {"manifest": dict, "owner": str, "seen_at": int}
        self.downloads = {}  # offer_id -> {"manifest": dict, "owner": str, "chunks": dict}

        self.secure.register_handler("file_offer", self._on_file_offer)
        self.secure.register_handler("file_get", self._on_file_get)
        self.secure.register_handler("file_chunk", self._on_file_chunk)

    def offer_file(self, peer_id, file_path):
        abs_path = os.path.abspath(file_path)
        manifest = build_manifest(abs_path)
        offer_id = manifest["offer_id"]
        with self._lock:
            self.local_offers[offer_id] = {"manifest": manifest, "file_path": abs_path}

        self.secure.send_secure_object(
            peer_id,
            {
                "kind": "file_offer",
                "manifest": manifest,
            },
        )
        return manifest

    def list_remote_offers(self):
        with self._lock:
            return [
                {
                    "offer_id": oid,
                    "owner": info["owner"],
                    "file_name": info["manifest"]["file_name"],
                    "file_size": info["manifest"]["file_size"],
                    "total_chunks": info["manifest"]["total_chunks"],
                }
                for oid, info in self.remote_offers.items()
            ]

    def request_download(self, offer_id):
        with self._lock:
            info = self.remote_offers.get(offer_id)
            if not info:
                raise ValueError("offer_id inconnu")
            owner = info["owner"]
            manifest = info["manifest"]
            self.downloads[offer_id] = {
                "manifest": manifest,
                "owner": owner,
                "chunks": {},
                "started_at": int(time.time()),
            }

        self.secure.send_secure_object(
            owner,
            {
                "kind": "file_get",
                "offer_id": offer_id,
            },
        )

    def _on_file_offer(self, peer_id, obj):
        manifest = obj.get("manifest", {})
        offer_id = manifest.get("offer_id")
        if not offer_id:
            return
        required = [
            "file_name",
            "file_size",
            "chunk_size",
            "total_chunks",
            "file_hash",
            "chunk_hashes",
        ]
        for key in required:
            if key not in manifest:
                return
        if len(manifest["chunk_hashes"]) != manifest["total_chunks"]:
            return

        with self._lock:
            self.remote_offers[offer_id] = {
                "manifest": manifest,
                "owner": peer_id,
                "seen_at": int(time.time()),
            }
        print(
            f"\n[FILE] Offre recu {offer_id}: {manifest['file_name']} "
            f"({manifest['file_size']} octets) de {peer_id[:10]}..."
        )

    def _on_file_get(self, peer_id, obj):
        offer_id = obj.get("offer_id")
        if not offer_id:
            return
        with self._lock:
            local = self.local_offers.get(offer_id)
        if not local:
            return

        manifest = local["manifest"]
        file_path = local["file_path"]
        total = manifest["total_chunks"]
        chunk_size = manifest["chunk_size"]
        for idx in range(total):
            chunk = read_chunk_at(file_path, idx, chunk_size)
            self.secure.send_secure_file_chunk(
                peer_id=peer_id,
                offer_id=offer_id,
                index=idx,
                total_chunks=total,
                chunk_hash_hex=manifest["chunk_hashes"][idx],
                chunk_bytes=chunk,
            )
        print(f"\n[FILE] Envoi termine pour {offer_id} vers {peer_id[:10]}...")

    def _on_file_chunk(self, peer_id, obj):
        offer_id = obj.get("offer_id")
        if not offer_id:
            return

        with self._lock:
            dl = self.downloads.get(offer_id)
        if not dl:
            return
        if dl["owner"] != peer_id:
            return

        idx = obj.get("index")
        expected_hash = obj.get("chunk_hash")
        chunk = obj.get("data")
        if idx is None or chunk is None or expected_hash is None:
            return
        if idx < 0 or idx >= dl["manifest"]["total_chunks"]:
            return
        manifest_hash = dl["manifest"]["chunk_hashes"][idx]
        if expected_hash != manifest_hash:
            return
        got_hash = hashlib.sha256(chunk).hexdigest()
        if got_hash != expected_hash:
            print(f"\n[FILE] Chunk corrompu {idx} sur {offer_id}, ignore.")
            return

        with self._lock:
            chunks = dl["chunks"]
            if idx in chunks:
                return
            chunks[idx] = chunk
            have = len(chunks)
            total = dl["manifest"]["total_chunks"]

        if have % 25 == 0 or have == total:
            print(f"\n[FILE] Progression {offer_id}: {have}/{total} chunks")

        if have == total:
            self._finalize_download(offer_id)

    def _finalize_download(self, offer_id):
        with self._lock:
            dl = self.downloads.get(offer_id)
            if not dl:
                return
            manifest = dl["manifest"]
            chunks = dict(dl["chunks"])

        out_name = manifest["file_name"]
        out_path = os.path.join(self.download_dir, out_name)
        if os.path.exists(out_path):
            stamp = int(time.time())
            out_path = os.path.join(self.download_dir, f"{stamp}_{out_name}")
        try:
            assemble_file(manifest, chunks, out_path)
            print(f"\n[FILE] Telechargement complete: {out_path}")
        except Exception as e:
            print(f"\n[FILE] Echec assemblage {offer_id}: {e}")
