import hashlib
import json

def generate_hash(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()