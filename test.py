import socket
import struct

# Configuration
MCAST_GRP = '239.255.42.99'
MCAST_PORT = 6000

# Création du socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', MCAST_PORT))

# Rejoindre le groupe multicast
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# Boucle pour recevoir les "HELLO" des autres
while True:
    data, addr = sock.recvfrom(1024)
    print(f"Nouveau pair détecté à l'adresse {addr}: {data}")