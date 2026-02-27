import struct

MAGIC = b'ARCH'
VERSION = 1
TYPE_HELLO = 0x01

def pack_hello(node_id):
    """Prépare un paquet binaire HELLO."""
    payload = node_id.encode('utf-8')
    # Header: Magic(4s), Version(B), Type(B), Length(H)
    header = struct.pack('!4s B B H', MAGIC, VERSION, TYPE_HELLO, len(payload))
    return header + payload

def unpack_packet(data):
    """Décode un paquet reçu."""
    header_size = struct.calcsize('!4s B B H')
    if len(data) < header_size: return None
    
    magic, ver, m_type, p_len = struct.unpack('!4s B B H', data[:header_size])
    if magic != MAGIC: return None
    
    payload = data[header_size:header_size + p_len].decode('utf-8')
    return {"type": m_type, "payload": payload}