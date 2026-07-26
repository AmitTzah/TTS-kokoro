"""Tests for tts_studio.__main__ — startup helpers."""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


class TestPurgeStaleTempFiles:
    def test_deletes_stale_files_with_matching_prefixes(self) -> None:
        """Stale tts_gen_ and tts_speed_ files older than 1 day are deleted."""
        from tts_studio.__main__ import _purge_stale_temp_files

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("tempfile.gettempdir", return_value=tmpdir):
                # Create stale files (mtime = 2 days ago)
                stale_time = time.time() - 172800
                gen_stale = Path(tmpdir) / "tts_gen_abc123.wav"
                speed_stale = Path(tmpdir) / "tts_speed_xyz789.wav"
                for f in (gen_stale, speed_stale):
                    f.write_bytes(b"fake wav")
                    f.touch()
                    f.chmod(0o644)
                    # patch mtime after creation
                    _set_mtime(f, stale_time)

                # Create fresh files (just created)
                gen_fresh = Path(tmpdir) / "tts_gen_fresh.wav"
                speed_fresh = Path(tmpdir) / "tts_speed_recent.wav"
                for f in (gen_fresh, speed_fresh):
                    f.write_bytes(b"fresh")

                _purge_stale_temp_files()

                assert not gen_stale.exists(), "stale tts_gen_ file should be deleted"
                assert not speed_stale.exists(), "stale tts_speed_ file should be deleted"
                assert gen_fresh.exists(), "fresh tts_gen_ file should remain"
                assert speed_fresh.exists(), "fresh tts_speed_ file should remain"

    def test_ignores_non_matching_prefixes(self) -> None:
        """Files without tts_gen_ or tts_speed_ prefix are untouched."""
        from tts_studio.__main__ import _purge_stale_temp_files

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("tempfile.gettempdir", return_value=tmpdir):
                stale_time = time.time() - 172800
                other_file = Path(tmpdir) / "tmpABC123.wav"
                other_file.write_bytes(b"other")
                _set_mtime(other_file, stale_time)

                _purge_stale_temp_files()

                assert other_file.exists(), "non-matching prefix file should remain"

    def test_handles_oserror_gracefully(self) -> None:
        """OSError during unlink is caught and does not propagate."""
        from tts_studio.__main__ import _purge_stale_temp_files

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("tempfile.gettempdir", return_value=tmpdir):
                stale_time = time.time() - 172800
                gen_file = Path(tmpdir) / "tts_gen_test.wav"
                gen_file.write_bytes(b"data")
                _set_mtime(gen_file, stale_time)

                with patch("pathlib.Path.unlink", side_effect=OSError("permission denied")):
                    # Should not raise
                    _purge_stale_temp_files()


def _set_mtime(path: Path, timestamp: float) -> None:
    """Set file modification time, falling back gracefully on Windows."""
    try:
        os_stat = path.stat()
        os.utime(str(path), (os_stat.st_atime, timestamp))
    except (PermissionError, OSError):
        pass
