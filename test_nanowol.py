"""
NanoWOL Unit Tests
Tests for crypto, WOL, service, and utility functions.
Run with: python -m pytest test_nanowol.py -v
Or: python test_nanowol.py
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

from crypto import generate_key_pair, load_private_key, load_public_key, sign_message, verify_signature
from wol import validate_mac, normalize_mac, send_wol_packet
from service import (
    IS_WINDOWS, IS_LINUX, IS_MACOS,
    get_platform_name, get_service_status
)


class TestCrypto(unittest.TestCase):
    """Tests for crypto module."""
    
    def setUp(self):
        """Create temporary directory for keys."""
        self.temp_dir = tempfile.mkdtemp()
        self.keys_dir = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary files."""
        for f in self.keys_dir.glob("*.pem"):
            f.unlink()
        os.rmdir(self.temp_dir)
    
    def test_generate_key_pair(self):
        """Test key pair generation."""
        private_path, public_path = generate_key_pair(self.keys_dir)
        
        self.assertTrue(private_path.exists())
        self.assertTrue(public_path.exists())
        self.assertEqual(private_path.name, "private.pem")
        self.assertEqual(public_path.name, "public.pem")
    
    def test_load_keys(self):
        """Test loading generated keys."""
        generate_key_pair(self.keys_dir)
        
        private_key = load_private_key(self.keys_dir / "private.pem")
        public_key = load_public_key(self.keys_dir / "public.pem")
        
        self.assertIsNotNone(private_key)
        self.assertIsNotNone(public_key)
    
    def test_sign_and_verify(self):
        """Test signing and verifying a message."""
        generate_key_pair(self.keys_dir)
        
        private_key = load_private_key(self.keys_dir / "private.pem")
        public_key = load_public_key(self.keys_dir / "public.pem")
        
        message = b"shutdown"
        signature = sign_message(message, private_key)
        
        self.assertIsInstance(signature, str)
        self.assertTrue(len(signature) > 0)
        
        # Valid signature
        self.assertTrue(verify_signature(message, signature, public_key))
        
        # Invalid signature
        self.assertFalse(verify_signature(b"wrong_message", signature, public_key))
        self.assertFalse(verify_signature(message, "invalid_hex", public_key))


class TestWOL(unittest.TestCase):
    """Tests for WOL module."""
    
    def test_validate_mac_valid(self):
        """Test valid MAC addresses."""
        self.assertTrue(validate_mac("AA:BB:CC:DD:EE:FF"))
        self.assertTrue(validate_mac("aa:bb:cc:dd:ee:ff"))
        self.assertTrue(validate_mac("AA-BB-CC-DD-EE-FF"))
        self.assertTrue(validate_mac("12:34:56:78:9A:BC"))
    
    def test_validate_mac_invalid(self):
        """Test invalid MAC addresses."""
        self.assertFalse(validate_mac("AA:BB:CC:DD:EE"))  # Too short
        self.assertFalse(validate_mac("AA:BB:CC:DD:EE:FF:GG"))  # Too long
        self.assertFalse(validate_mac("AABBCCDDEEFF"))  # No separators
        self.assertFalse(validate_mac("GG:HH:II:JJ:KK:LL"))  # Invalid chars
    
    def test_normalize_mac(self):
        """Test MAC normalization."""
        self.assertEqual(normalize_mac("AA:BB:CC:DD:EE:FF"), "AABBCCDDEEFF")
        self.assertEqual(normalize_mac("aa-bb-cc-dd-ee-ff"), "AABBCCDDEEFF")
        self.assertEqual(normalize_mac("aa:bb:cc:dd:ee:ff"), "AABBCCDDEEFF")
    
    def test_send_wol_invalid_mac(self):
        """Test WOL with invalid MAC raises error."""
        with self.assertRaises(ValueError):
            send_wol_packet("invalid_mac")
        
        with self.assertRaises(ValueError):
            send_wol_packet("AA:BB:CC")  # Too short


class TestService(unittest.TestCase):
    """Tests for service module."""
    
    def test_platform_detection(self):
        """Test that exactly one platform is detected."""
        platforms = [IS_WINDOWS, IS_LINUX, IS_MACOS]
        # Exactly one should be True (or none if unsupported platform)
        self.assertLessEqual(sum(platforms), 1)
    
    def test_get_platform_name(self):
        """Test platform name returns a string."""
        name = get_platform_name()
        self.assertIsInstance(name, str)
        self.assertTrue(len(name) > 0)
        
        if IS_WINDOWS:
            self.assertIn("Windows", name)
        elif IS_LINUX:
            self.assertIn("Linux", name)
        elif IS_MACOS:
            self.assertIn("macOS", name)
    
    def test_get_service_status_returns_dict(self):
        """Test service status returns a dictionary."""
        status = get_service_status()
        self.assertIsInstance(status, dict)
        self.assertIn("installed", status)


class TestTraceDecorator(unittest.TestCase):
    """Tests for trace_execution decorator."""
    
    def test_decorator_preserves_function(self):
        """Test that decorator doesn't break function."""
        from crypto import trace_execution
        
        @trace_execution
        def test_func(x, y):
            return x + y
        
        result = test_func(2, 3)
        self.assertEqual(result, 5)
    
    def test_decorator_preserves_name(self):
        """Test that decorator preserves function name."""
        from crypto import trace_execution
        
        @trace_execution
        def my_function():
            pass
        
        self.assertEqual(my_function.__name__, "my_function")


if __name__ == "__main__":
    unittest.main(verbosity=2)


