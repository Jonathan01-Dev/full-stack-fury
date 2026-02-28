import socket
import struct
import time

from src.protocol.packet import TYPE_HELLO, pack_hello, unpack_packet

MCAST_GRP = "239.255.42.99"
MCAST_PORT = 6000


def get_local_ip():
    """Try to detect the primary local interface."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("10.255.255.255", 1))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "0.0.0.0"


class Discovery:
    def __init__(self, node_id, peer_table, mcast_port=MCAST_PORT):
        self.node_id = node_id
        self.peer_table = peer_table
        self.mcast_port = mcast_port
        self.running = True
        self._last_reply = {}  # ip -> timestamp
        self._dup_warned_ips = set()

    def broadcast(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        local_ip = get_local_ip()
        if local_ip != "0.0.0.0":
            try:
                sock.setsockopt(
                    socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(local_ip)
                )
            except Exception:
                pass

        while self.running:
            try:
                # On envoie l'ID et le port sécurisé (ID|PORT)
                msg = f"{self.node_id}|{self.mcast_port + 1}"
                packet = pack_hello(msg)
                sock.sendto(packet, (MCAST_GRP, self.mcast_port))
                sock.sendto(packet, ("255.255.255.255", self.mcast_port))
                time.sleep(30)
            except Exception as e:
                print(f"Erreur envoi HELLO: {e}")

    def ping(self, ip):
        """Bootstrap direct P2P sans multicast: envoi un HELLO unicast vers une IP."""
        try:
            socket.inet_aton(ip)
        except OSError:
            raise ValueError("IP invalide")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            msg = f"{self.node_id}|{self.mcast_port + 1}"
            sock.sendto(pack_hello(msg), (ip, self.mcast_port))
        finally:
            sock.close()

    def listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", self.mcast_port))

        local_ip = get_local_ip()
        mreq = struct.pack("4s4s", socket.inet_aton(MCAST_GRP), socket.inet_aton(local_ip))
        try:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except Exception as e:
            print(f"Multicast indisponible, mode UDP simple: {e}")

        print(f"Ecoute discovery active sur {self.mcast_port}...")
        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                info = unpack_packet(data)
                if info and info["type"] == TYPE_HELLO:
                    payload = info["payload"].decode("utf-8")
                    if "|" in payload:
                        remote_id, remote_port = payload.split("|")
                        remote_port = int(remote_port)
                    else:
                        remote_id = payload
                        remote_port = self.mcast_port + 1 # Fallback

                    if remote_id == self.node_id:
                        continue

                    now = time.time()
                    prev = self._last_reply.get(addr[0], 0)
                    self.peer_table.update(remote_id, addr[0], port=remote_port)
                    # Ack unicast de courtoisie pour bootstrap bilateral sans serveur central.
                    if now - prev > 10:
                        msg = f"{self.node_id}|{self.mcast_port + 1}"
                        sock.sendto(pack_hello(msg), (addr[0], self.mcast_port))
                        self._last_reply[addr[0]] = now
            except Exception as e:
                if self.running:
                    print(f"Erreur reception HELLO: {e}")

    def stop(self):
        self.running = False
