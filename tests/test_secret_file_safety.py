"""Exercise secret replacement against real files and operating-system write failures."""

import os
from pathlib import Path
import subprocess
import sys

import pytest
from dotenv import dotenv_values

import github_monitor as monitor


# Preserves unrelated content when a shorter secret replaces an existing permissive file
def test_secret_replacement_preserves_content_and_restricts_permissions(tmp_path):
    destination = tmp_path / ".env"
    destination.write_text("# keep this note\nSMTP_PASSWORD=long-old-password\nUNRELATED=keep\n", encoding="utf-8")
    destination.chmod(0o644)

    monitor.update_dotenv_file(destination, {"SMTP_PASSWORD": "new"})

    assert dotenv_values(destination) == {"SMTP_PASSWORD": "new", "UNRELATED": "keep"}
    assert destination.read_text().startswith("# keep this note\n")
    if os.name == "posix":
        assert destination.stat().st_mode & 0o777 == 0o600
    assert list(tmp_path.iterdir()) == [destination]


@pytest.mark.skipif(os.name != "posix", reason="Requires POSIX file-size limits")
# Keeps every original credential when the operating system rejects the replacement write
def test_failed_secret_write_preserves_the_existing_file(tmp_path):
    destination = tmp_path / ".env"
    original = b"SMTP_PASSWORD=old\nGITHUB_TOKEN=other-credential\nUNRELATED=keep\n"
    destination.write_bytes(original)
    program = "\n".join(("import resource, signal, sys", "import github_monitor as monitor", "signal.signal(signal.SIGXFSZ, signal.SIG_IGN)", "resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))", "try:", "    monitor.update_dotenv_file(sys.argv[1], {'SMTP_PASSWORD': 'new'})", "except OSError:", "    print('write rejected')", "else:", "    raise AssertionError('Expected an operating-system write failure')"))

    result = subprocess.run([sys.executable, "-c", program, str(destination)], cwd=Path(monitor.__file__).parent, capture_output=True, text=True, timeout=30)

    assert result.returncode == 0, result.stderr
    assert "write rejected" in result.stdout
    assert destination.read_bytes() == original
    assert list(tmp_path.iterdir()) == [destination]


@pytest.mark.skipif(os.name != "posix", reason="Requires unprivileged symlink creation")
# Updates the destination of an existing dotenv symlink without replacing the link
def test_secret_replacement_preserves_existing_symlinks(tmp_path):
    destination = tmp_path / "secrets.env"
    destination.write_text("SMTP_PASSWORD=old\nUNRELATED=keep\n", encoding="utf-8")
    link = tmp_path / ".env"
    link.symlink_to(destination.name)

    monitor.update_dotenv_file(link, {"SMTP_PASSWORD": "new"})

    assert link.is_symlink()
    assert dotenv_values(destination) == {"SMTP_PASSWORD": "new", "UNRELATED": "keep"}
    assert destination.stat().st_mode & 0o777 == 0o600
