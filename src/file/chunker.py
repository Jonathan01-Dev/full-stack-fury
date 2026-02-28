import hashlib
import os


DEFAULT_CHUNK_SIZE = 8192


def build_manifest(file_path, chunk_size=DEFAULT_CHUNK_SIZE):
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)
    if chunk_size <= 0:
        raise ValueError("chunk_size doit etre > 0")

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    chunk_hashes = []
    file_hasher = hashlib.sha256()

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            chunk_hashes.append(hashlib.sha256(chunk).hexdigest())
            file_hasher.update(chunk)

    total_chunks = len(chunk_hashes)
    file_hash = file_hasher.hexdigest()
    offer_id = hashlib.sha256(
        f"{file_name}:{file_size}:{file_hash}".encode("utf-8")
    ).hexdigest()[:16]

    return {
        "offer_id": offer_id,
        "file_name": file_name,
        "file_size": file_size,
        "chunk_size": chunk_size,
        "total_chunks": total_chunks,
        "file_hash": file_hash,
        "chunk_hashes": chunk_hashes,
    }


def read_chunk_at(file_path, index, chunk_size):
    if index < 0:
        raise ValueError("index negatif")
    with open(file_path, "rb") as f:
        f.seek(index * chunk_size)
        return f.read(chunk_size)


def assemble_file(manifest, chunks_by_index, output_path):
    expected = manifest["total_chunks"]
    missing = [idx for idx in range(expected) if idx not in chunks_by_index]
    if missing:
        raise ValueError(f"Chunks manquants: {len(missing)}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    hasher = hashlib.sha256()
    with open(output_path, "wb") as out:
        for idx in range(expected):
            data = chunks_by_index[idx]
            hasher.update(data)
            out.write(data)
    rebuilt_hash = hasher.hexdigest()
    if rebuilt_hash != manifest["file_hash"]:
        raise ValueError("Hash global invalide apres assemblage")
    return output_path
