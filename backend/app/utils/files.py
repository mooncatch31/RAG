from pathlib import Path
import hashlib

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256(); h.update(b); return h.hexdigest()
