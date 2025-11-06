import pytest
from iso_logic import ISOCore
import os
import struct
from unittest.mock import patch, MagicMock

@pytest.fixture
def iso_core():
    """Provides a fresh ISOCore instance for each test."""
    return ISOCore()

@patch('iso_logic.pycdlib.PyCdlib')
def test_create_hybrid_iso_calls_add_isohybrid(MockPyCdlib, iso_core, tmp_path):
    """Test that add_isohybrid is called when saving a bootable ISO."""
    # Create a mock instance of the pycdlib object
    mock_iso = MagicMock()
    MockPyCdlib.return_value = mock_iso

    # 1. Create a dummy boot image
    boot_img_path = tmp_path / "boot.img"
    boot_img_path.write_bytes(b'\x00' * 2048)
    iso_core.boot_image_path = str(boot_img_path)

    # 2. Save the ISO.
    output_iso_path = tmp_path / "hybrid.iso"
    iso_core.save_iso(str(output_iso_path), use_joliet=True, use_rock_ridge=True, make_hybrid=True)

    # 3. Assert that the add_isohybrid method was called.
    mock_iso.add_isohybrid.assert_called_once()
