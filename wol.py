"""
NanoWOL - Wake-on-LAN Module
Handles sending WOL magic packets to wake remote machines.
Part of the Nano Product Family.
"""

import re
import socket
import logging

logger = logging.getLogger(__name__)

# MAC address validation pattern
MAC_PATTERN = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')


def validate_mac(mac_address: str) -> bool:
    """
    Validate MAC address format.
    
    Args:
        mac_address: MAC address string (AA:BB:CC:DD:EE:FF or AA-BB-CC-DD-EE-FF)
        
    Returns:
        True if valid format
    """
    return bool(MAC_PATTERN.match(mac_address))


def normalize_mac(mac_address: str) -> str:
    """
    Normalize MAC address to uppercase without separators.
    
    Args:
        mac_address: MAC address in any format
        
    Returns:
        Uppercase MAC without separators (AABBCCDDEEFF)
    """
    return mac_address.replace(":", "").replace("-", "").upper()


def send_wol_packet(mac_address: str, broadcast: str = "255.255.255.255", port: int = 9) -> None:
    """
    Send a Wake-on-LAN magic packet.
    
    The magic packet consists of:
    - 6 bytes of 0xFF
    - MAC address repeated 16 times
    
    Args:
        mac_address: Target MAC address (format: AA:BB:CC:DD:EE:FF)
        broadcast: Broadcast address (default: 255.255.255.255)
        port: UDP port (default: 9, standard WOL port)
        
    Raises:
        ValueError: If MAC address is invalid
    """
    # Clean and validate MAC address
    mac = normalize_mac(mac_address)
    
    if len(mac) != 12:
        raise ValueError(f"Invalid MAC address: {mac_address}")
    
    try:
        mac_bytes = bytes.fromhex(mac)
    except ValueError:
        raise ValueError(f"Invalid MAC address characters: {mac_address}")
    
    # Build magic packet: 6 bytes of 0xFF + MAC repeated 16 times
    magic_packet = b'\xff' * 6 + mac_bytes * 16
    
    # Send via UDP broadcast
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, (broadcast, port))
    
    logger.info(f"WOL packet sent to {mac_address} via {broadcast}:{port}")

