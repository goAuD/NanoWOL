"""
NanoWOL - Crypto Module
RSA key generation, signing, and verification for secure authentication.
Part of the Nano Product Family.
"""

import os
import logging
import functools
import time
from pathlib import Path
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_KEYS_DIR = Path("./keys")
DEFAULT_PRIVATE_KEY = DEFAULT_KEYS_DIR / "private.pem"
DEFAULT_PUBLIC_KEY = DEFAULT_KEYS_DIR / "public.pem"


def trace_execution(func):
    """Decorator that logs function entry/exit with execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"→ Entering {func.__name__}")
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.debug(f"← Exiting {func.__name__} ({elapsed:.3f}s)")
            return result
        except Exception as e:
            logger.error(f"✗ {func.__name__} raised {type(e).__name__}: {e}")
            raise
    return wrapper


@trace_execution
def generate_key_pair(keys_dir: Path = DEFAULT_KEYS_DIR) -> tuple:
    """
    Generate RSA-2048 key pair for signing/verification.
    
    Args:
        keys_dir: Directory to store the keys
        
    Returns:
        Tuple of (private_key_path, public_key_path)
    """
    keys_dir.mkdir(parents=True, exist_ok=True)
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    private_path = keys_dir / "private.pem"
    public_path = keys_dir / "public.pem"
    
    private_path.write_bytes(private_pem)
    public_path.write_bytes(public_pem)
    
    # Restrict private key permissions on Unix
    if os.name != 'nt':
        os.chmod(private_path, 0o600)
    
    logger.info(f"Generated key pair in {keys_dir}")
    return private_path, public_path


def load_private_key(path: Path = DEFAULT_PRIVATE_KEY):
    """Load private key from PEM file."""
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def load_public_key(path: Path = DEFAULT_PUBLIC_KEY):
    """Load public key from PEM file."""
    with open(path, "rb") as f:
        return serialization.load_pem_public_key(f.read())


@trace_execution
def sign_message(message: bytes, private_key) -> str:
    """
    Sign a message with the private key.
    
    Args:
        message: Bytes to sign
        private_key: RSA private key object
        
    Returns:
        Hex-encoded signature string
    """
    signature = private_key.sign(
        message,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return signature.hex()


@trace_execution
def verify_signature(message: bytes, signature_hex: str, public_key) -> bool:
    """
    Verify a signature against a message using the public key.
    
    Args:
        message: Original message bytes
        signature_hex: Hex-encoded signature
        public_key: RSA public key object
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        signature = bytes.fromhex(signature_hex)
        public_key.verify(
            signature,
            message,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception:
        logger.warning("Signature verification failed")
        return False


# =============================================================================
# REPLAY PROTECTION
# =============================================================================

import json
import secrets

def create_signed_payload(action: str, private_key) -> dict:
    """
    Create a signed payload with timestamp and nonce for replay protection.
    
    Args:
        action: Action name (e.g., "shutdown")
        private_key: RSA private key for signing
        
    Returns:
        Dict with payload, signature, timestamp, and nonce
    """
    import time
    
    timestamp = int(time.time())
    nonce = secrets.token_hex(16)
    
    payload = {
        "action": action,
        "timestamp": timestamp,
        "nonce": nonce
    }
    
    # Sign the JSON payload
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    signature = sign_message(payload_bytes, private_key)
    
    return {
        "payload": payload,
        "signature": signature
    }


def verify_signed_payload(
    data: dict, 
    public_key, 
    expected_action: str,
    max_age_seconds: int = 60,
    used_nonces: set = None
) -> tuple:
    """
    Verify a signed payload with replay protection.
    
    Args:
        data: Dict containing 'payload' and 'signature'
        public_key: RSA public key for verification
        expected_action: Expected action in payload
        max_age_seconds: Maximum age of timestamp (default 60s)
        used_nonces: Set of previously used nonces (for replay detection)
        
    Returns:
        Tuple of (is_valid: bool, error_message: str or None)
    """
    import time
    
    try:
        payload = data.get("payload", {})
        signature = data.get("signature", "")
        
        if not payload or not signature:
            return False, "Missing payload or signature"
        
        action = payload.get("action")
        timestamp = payload.get("timestamp", 0)
        nonce = payload.get("nonce", "")
        
        # Verify action
        if action != expected_action:
            return False, f"Invalid action: expected {expected_action}"
        
        # Verify timestamp (not too old)
        current_time = int(time.time())
        if current_time - timestamp > max_age_seconds:
            return False, f"Payload expired (max age: {max_age_seconds}s)"
        
        # Verify timestamp (not in future)
        if timestamp > current_time + 5:  # Allow 5s clock skew
            return False, "Payload timestamp in future"
        
        # Check nonce reuse
        if used_nonces is not None:
            if nonce in used_nonces:
                return False, "Nonce already used (replay attack)"
            used_nonces.add(nonce)
        
        # Verify signature
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        if not verify_signature(payload_bytes, signature, public_key):
            return False, "Invalid signature"
        
        return True, None
        
    except Exception as e:
        logger.error(f"Payload verification error: {e}")
        return False, str(e)


