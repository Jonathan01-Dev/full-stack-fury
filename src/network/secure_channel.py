import json
import socket
import struct
import threading
import time

from src.protocol.packet import (
    TYPE_HANDSHAKE_INIT,
    TYPE_HANDSHAKE_RESP,
    TYPE_SECURE_MSG,
    pack_packet,
    unpack_packet,
)
from src.security.session import (
    decrypt_payload,
    derive_session_keys,
    encrypt_payload,
    generate_ephemeral_keypair,
)


SECURE_PORT = 6001
SECURE_HEADER_SIZE = 64 + 12 + 16 + 32
FILE_CHUNK_MAGIC = b"FCH1"
FILE_CHUNK_HEADER = "!4s16sII32sH"
FILE_CHUNK_HEADER_SIZE = struct.calcsize(FILE_CHUNK_HEADER)


class SecureChannel:
    def __init__(self, node_id, peer_table, trust_store):
        self.node_id = node_id
        self.peer_table = peer_table
        self.trust_store = trust_store
        self.running = True

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4 * 1024 * 1024)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
        self._socket.bind(("", SECURE_PORT))

        self._lock = threading.Lock()
        self._handlers = {}
        self._sessions = {}
        self._pending = {}

    def register_handler(self, kind, handler):
        self._handlers[kind] = handler

    def stop(self):
        self.running = False
        try:
            self._socket.close()
        except Exception:
            pass

    def _build_transcript(self, peer_id, local_pub, remote_pub):
        if self.node_id <= peer_id:
            first_id, second_id = self.node_id, peer_id
            first_pub, second_pub = local_pub, remote_pub
        else:
            first_id, second_id = peer_id, self.node_id
            first_pub, second_pub = remote_pub, local_pub
        return (
            first_id.encode("utf-8")
            + second_id.encode("utf-8")
            + first_pub
            + second_pub
        )

    def _peer_entry(self, peer_id):
        return self.peer_table.get_peer(peer_id)

    def _send_handshake_init(self, peer_id, ip):
        eph_priv, eph_pub = generate_ephemeral_keypair()
        payload = json.dumps({"from_id": self.node_id, "eph_pub": eph_pub.hex()}).encode(
            "utf-8"
        )
        with self._lock:
            self._pending[peer_id] = eph_priv
        self._socket.sendto(pack_packet(TYPE_HANDSHAKE_INIT, payload), (ip, SECURE_PORT))

    def _ensure_session(self, peer_id, ip):
        with self._lock:
            has_session = peer_id in self._sessions
        if has_session:
            return
        self._send_handshake_init(peer_id, ip)
        deadline = time.time() + 5
        while time.time() < deadline:
            with self._lock:
                if peer_id in self._sessions:
                    return
            time.sleep(0.02)
        raise TimeoutError("Handshake timeout.")

    def _pack_secure_payload(self, nonce, tag, mac, ciphertext):
        node_id_bytes = self.node_id.encode("ascii")
        if len(node_id_bytes) != 64:
            raise ValueError("Node ID invalide (attendu: 64 chars hex).")
        return node_id_bytes + nonce + tag + mac + ciphertext

    def _unpack_secure_payload(self, payload):
        if len(payload) < SECURE_HEADER_SIZE:
            return None
        peer_id = payload[:64].decode("ascii", errors="ignore")
        nonce = payload[64:76]
        tag = payload[76:92]
        mac = payload[92:124]
        ciphertext = payload[124:]
        return peer_id, nonce, tag, mac, ciphertext

    def _send_encrypted_payload(self, peer_id, ip, plaintext_bytes):
        self._ensure_session(peer_id, ip)
        with self._lock:
            keys = self._sessions[peer_id]
        nonce, ciphertext, tag, mac = encrypt_payload(
            keys["enc_key"], keys["mac_key"], plaintext_bytes
        )
        payload = self._pack_secure_payload(nonce, tag, mac, ciphertext)
        self._socket.sendto(pack_packet(TYPE_SECURE_MSG, payload), (ip, SECURE_PORT))

    def send_secure_object(self, peer_id, obj):
        peer = self._peer_entry(peer_id)
        if not peer:
            raise ValueError("Pair introuvable. Utilise 'peers' d'abord.")
        ip = peer["ip"]

        trusted_ok, _ = self.trust_store.check_or_trust_first_use(peer_id)
        if not trusted_ok:
            raise ValueError("Pair non fiable selon TOFU.")

        plaintext = json.dumps(obj, separators=(",", ":")).encode("utf-8")
        self._send_encrypted_payload(peer_id, ip, plaintext)

    def send_secure_message(self, peer_id, message):
        self.send_secure_object(peer_id, {"kind": "chat", "text": str(message)})

    def send_secure_file_chunk(
        self, peer_id, offer_id, index, total_chunks, chunk_hash_hex, chunk_bytes
    ):
        if len(offer_id) != 16:
            raise ValueError("offer_id doit faire 16 caracteres.")
        if len(chunk_bytes) > 65535:
            raise ValueError("chunk trop grand (max 65535 octets).")
        header = struct.pack(
            FILE_CHUNK_HEADER,
            FILE_CHUNK_MAGIC,
            offer_id.encode("ascii"),
            int(index),
            int(total_chunks),
            bytes.fromhex(chunk_hash_hex),
            len(chunk_bytes),
        )
        self.send_secure_bytes(peer_id, header + chunk_bytes)

    def send_secure_bytes(self, peer_id, payload_bytes):
        peer = self._peer_entry(peer_id)
        if not peer:
            raise ValueError("Pair introuvable. Utilise 'peers' d'abord.")
        ip = peer["ip"]
        trusted_ok, _ = self.trust_store.check_or_trust_first_use(peer_id)
        if not trusted_ok:
            raise ValueError("Pair non fiable selon TOFU.")
        self._send_encrypted_payload(peer_id, ip, payload_bytes)

    def listen(self):
        print(f"Canal securise actif sur le port {SECURE_PORT}...")
        while self.running:
            try:
                data, addr = self._socket.recvfrom(65535)
                packet = unpack_packet(data)
                if not packet:
                    continue
                ptype = packet["type"]
                if ptype == TYPE_HANDSHAKE_INIT:
                    self._on_handshake_init(packet["payload"], addr)
                elif ptype == TYPE_HANDSHAKE_RESP:
                    self._on_handshake_resp(packet["payload"], addr)
                elif ptype == TYPE_SECURE_MSG:
                    self._on_secure_msg(packet["payload"], addr)
            except OSError:
                break
            except Exception as e:
                if self.running:
                    print(f"Erreur secure listen: {e}")

    def _on_handshake_init(self, payload, addr):
        msg = json.loads(payload.decode("utf-8"))
        peer_id = msg["from_id"]
        peer_pub = bytes.fromhex(msg["eph_pub"])

        self.trust_store.check_or_trust_first_use(peer_id)
        self.trust_store.mark_seen(peer_id)
        self.peer_table.update(peer_id, addr[0])

        eph_priv, eph_pub = generate_ephemeral_keypair()
        transcript = self._build_transcript(peer_id, eph_pub, peer_pub)
        enc_key, mac_key = derive_session_keys(eph_priv, peer_pub, transcript)
        with self._lock:
            self._sessions[peer_id] = {"enc_key": enc_key, "mac_key": mac_key}

        resp = json.dumps({"from_id": self.node_id, "eph_pub": eph_pub.hex()}).encode(
            "utf-8"
        )
        self._socket.sendto(pack_packet(TYPE_HANDSHAKE_RESP, resp), addr)

    def _on_handshake_resp(self, payload, addr):
        msg = json.loads(payload.decode("utf-8"))
        peer_id = msg["from_id"]
        peer_pub = bytes.fromhex(msg["eph_pub"])

        self.trust_store.check_or_trust_first_use(peer_id)
        self.trust_store.mark_seen(peer_id)
        self.peer_table.update(peer_id, addr[0])

        with self._lock:
            local_priv = self._pending.pop(peer_id, None)
        if local_priv is None:
            return

        from nacl.public import PrivateKey

        local_pub = bytes(PrivateKey(local_priv).public_key)
        transcript = self._build_transcript(peer_id, local_pub, peer_pub)
        enc_key, mac_key = derive_session_keys(local_priv, peer_pub, transcript)
        with self._lock:
            self._sessions[peer_id] = {"enc_key": enc_key, "mac_key": mac_key}

    def _dispatch_secure_object(self, peer_id, obj):
        kind = obj.get("kind")
        if kind == "chat":
            print(f"\n[MSG securise] {peer_id[:10]}... : {obj.get('text', '')}")
            return
        handler = self._handlers.get(kind)
        if not handler:
            print(f"\n[WARN] Type de message inconnu: {kind}")
            return
        try:
            handler(peer_id, obj)
        except Exception as e:
            print(f"\n[ERROR] Handler '{kind}' en echec: {e}")

    def _try_parse_file_chunk(self, plaintext):
        if len(plaintext) < FILE_CHUNK_HEADER_SIZE:
            return None
        magic = plaintext[:4]
        if magic != FILE_CHUNK_MAGIC:
            return None
        header = plaintext[:FILE_CHUNK_HEADER_SIZE]
        body = plaintext[FILE_CHUNK_HEADER_SIZE:]
        _, offer_id_bytes, idx, total, chunk_hash_raw, data_len = struct.unpack(
            FILE_CHUNK_HEADER, header
        )
        if data_len != len(body):
            return None
        return {
            "kind": "file_chunk",
            "offer_id": offer_id_bytes.decode("ascii"),
            "index": idx,
            "total_chunks": total,
            "chunk_hash": chunk_hash_raw.hex(),
            "data": body,
        }

    def _on_secure_msg(self, payload, addr):
        parsed = self._unpack_secure_payload(payload)
        if not parsed:
            return
        peer_id, nonce, tag, mac, ciphertext = parsed

        self.trust_store.check_or_trust_first_use(peer_id)
        self.trust_store.mark_seen(peer_id)
        self.peer_table.update(peer_id, addr[0])

        with self._lock:
            keys = self._sessions.get(peer_id)
        if not keys:
            return
        try:
            plaintext = decrypt_payload(
                keys["enc_key"], keys["mac_key"], nonce, ciphertext, tag, mac
            )
            chunk_obj = self._try_parse_file_chunk(plaintext)
            if chunk_obj:
                handler = self._handlers.get("file_chunk")
                if handler:
                    handler(peer_id, chunk_obj)
                return
            try:
                obj = json.loads(plaintext.decode("utf-8"))
            except Exception:
                obj = {"kind": "chat", "text": plaintext.decode("utf-8")}
            self._dispatch_secure_object(peer_id, obj)
        except Exception as e:
            print(f"\n[SECURITY] Message invalide de {peer_id[:10]}... : {e}")
