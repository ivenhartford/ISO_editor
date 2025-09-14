import pytest
from iso_logic import ISOCore
import os

@pytest.fixture
def iso_core():
    """Provides a fresh ISOCore instance for each test."""
    return ISOCore()

def create_dummy_cue_sheet(tmp_path):
    """Creates a dummy CUE sheet and a corresponding BIN file."""
    cue_content = """FILE "IMAGE.BIN" BINARY
  TRACK 01 AUDIO
    TITLE "Track 1"
    INDEX 01 00:00:00
  TRACK 02 AUDIO
    TITLE "Track 2"
    INDEX 01 00:02:00
"""
    # 2 seconds * 75 frames/sec * 2352 bytes/frame = 352800 bytes
    offset_track2 = 2 * 75 * 2352

    # Make the BIN file large enough for both tracks
    bin_content = b'\x11' * (offset_track2 + 100000) # Track 1 data
    bin_content += b'\x22' * 200000 # Track 2 data

    cue_path = tmp_path / "IMAGE.CUE"
    bin_path = tmp_path / "IMAGE.BIN"

    cue_path.write_text(cue_content)
    bin_path.write_bytes(bin_content)

    return cue_path

def test_load_cue_sheet(iso_core, tmp_path):
    """Test that a CUE sheet can be loaded and parsed correctly."""
    cue_path = create_dummy_cue_sheet(tmp_path)

    iso_core.load_iso(str(cue_path))

    assert iso_core.directory_tree is not None
    assert len(iso_core.directory_tree['children']) == 2

    track1 = iso_core.directory_tree['children'][0]
    track2 = iso_core.directory_tree['children'][1]

    assert track1['name'] == 'Track 1'
    assert track2['name'] == 'Track 2'
    assert track1['is_cue_track'] is True
    assert track2['is_cue_track'] is True

    # Check offsets. CueParser provides offset in bytes.
    # 1 frame = 2352 bytes for CD-DA
    # INDEX 01 00:02:00 means 2 seconds * 75 frames/sec = 150 frames
    # 150 frames * 2352 bytes/frame = 352800 bytes
    assert track1['cue_offset'] == 0
    assert track2['cue_offset'] == 352800

    # Check size calculation
    assert track1['size'] == 352800

    bin_size = os.path.getsize(tmp_path / "IMAGE.BIN")
    assert track2['size'] == bin_size - 352800

    # Test that we can get the file data
    track1_data = iso_core.get_file_data(track1)
    track2_data = iso_core.get_file_data(track2)

    assert len(track1_data) == track1['size']
    assert len(track2_data) == track2['size']

    # Check the content of the extracted data
    assert track1_data[0] == 0x11
    assert track2_data[0] == 0x11 # The first part of track 2 is from the first block
    assert track2_data[-1] == 0x22
