import struct

MAGIC = b"ARCH"
VERSION = 1

TYPE_HELLO = 0x01
TYPE_HANDSHAKE_INIT = 0x02
TYPE_HANDSHAKE_RESP = 0x03
TYPE_SECURE_MSG = 0x04


def pack_hello(node_id):
    """Prepare un paquet binaire HELLO."""
    payload = node_id.encode("utf-8")
    return pack_packet(TYPE_HELLO, payload)


def pack_packet(packet_type, payload):
    """Construit un paquet Archipel generique."""
    header = struct.pack("!4s B B H", MAGIC, VERSION, packet_type, len(payload))
    return header + payload


def unpack_packet(data):
    """Decode un paquet recu."""
    header_size = struct.calcsize("!4s B B H")
    if len(data) < header_size:
        return None

    magic, ver, m_type, p_len = struct.unpack("!4s B B H", data[:header_size])
    if magic != MAGIC or ver != VERSION:
        return None

    payload = data[header_size : header_size + p_len]
    if len(payload) != p_len:
        return None
    return {"type": m_type, "payload": payload}
