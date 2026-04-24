import time

# Internal store: { "key": {"payload": dict, "response": dict, "expires_at": float} }
_data_store = {}

def get_transaction(key: str):
    """Retrieves a transaction if it exists and is not expired."""
    entry = _data_store.get(key)
    if entry:
        # If the record is older than 24 hours, clear it
        if time.time() > entry["expires_at"]:
            del _data_store[key]
            return None
        return entry
    return None

def save_transaction(key: str, payload: dict, response_data: dict):
    """Saves transaction with a 24-hour expiration window."""
    _data_store[key] = {
        "payload": payload,
        "response": response_data,
        "expires_at": time.time() + 86400  # 24 hours in seconds
    }