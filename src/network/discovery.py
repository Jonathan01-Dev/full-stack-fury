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
    def __init__(self, node_id, peer_table):
        self.node_id = node_id
        self.peer_table = peer_table
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
                packet = pack_hello(self.node_id)
                sock.sendto(packet, (MCAST_GRP, MCAST_PORT))
                sock.sendto(packet, ("255.255.255.255", MCAST_PORT))
                time.sleep(2)
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
            sock.sendto(pack_hello(self.node_id), (ip, MCAST_PORT))
        finally:
            sock.close()

    def listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", MCAST_PORT))

        local_ip = get_local_ip()
        mreq = struct.pack("4s4s", socket.inet_aton(MCAST_GRP), socket.inet_aton(local_ip))
        try:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except Exception as e:
            print(f"Multicast indisponible, mode UDP simple: {e}")

        print(f"Ecoute discovery active sur {MCAST_PORT}...")
        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                info = unpack_packet(data)
                if info and info["type"] == TYPE_HELLO:
                    remote_id = info["payload"].decode("utf-8")
                    if remote_id == self.node_id:
                        # Typical when two machines share the same private.key.
                        if (
                            addr[0] not in ("127.0.0.1", "0.0.0.0")
                            and addr[0] not in self._dup_warned_ips
                        ):
                            print(
                                "\n[WARN] HELLO ignore: meme node_id detecte depuis "
                                f"{addr[0]}. Verifie data/keys/private.key sur chaque PC."
                            )
                            self._dup_warned_ips.add(addr[0])
                        continue

                    now = time.time()
                    prev = self._last_reply.get(addr[0], 0)
                    self.peer_table.update(remote_id, addr[0])
                    # Ack unicast de courtoisie pour bootstrap bilateral sans serveur central.
                    if now - prev > 10:
                        sock.sendto(pack_hello(self.node_id), (addr[0], MCAST_PORT))
                        self._last_reply[addr[0]] = now
            except Exception as e:
                if self.running:
                    print(f"Erreur reception HELLO: {e}")

    def stop(self):
        self.running = False
