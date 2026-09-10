"""Exercise startup validation and partial saves with real filesystem objects."""
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("value", ["'daily'", "None", "True", "-1", "1e309"])
# Rejects malformed liveness values before offline startup can hide the configuration error
def test_startup_names_invalid_liveness_before_network(gm_module, monkeypatch, tmp_path, capsys, restored_globals, value):
    import signal
    import requests
    config = tmp_path / "settings.conf"
    config.write_text(f"CLEAR_SCREEN=False\nLIVENESS_CHECK_INTERVAL={value}\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["github_monitor", "target", "--config-file", str(config), "--env-file", "none", "--no-color"])
    monkeypatch.setattr(sys, "stdout", sys.stdout)
    monkeypatch.setattr(gm_module, "stdout_bck", gm_module.stdout_bck)
    signals = {item: signal.getsignal(item) for item in (signal.SIGINT, signal.SIGTERM)}
    attempts = []

    # Records forbidden early network work while returning the real transport exception
    def send(session, request, **kwargs):
        attempts.append(request.url)
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(requests.Session, "send", send)
    try:
        with pytest.raises(SystemExit) as exc:
            gm_module.main()
        assert exc.value.code == 1
    finally:
        for number, handler in signals.items():
            signal.signal(number, handler)
    output = capsys.readouterr().out
    assert "LIVENESS_CHECK_INTERVAL must be a finite number zero or greater" in output
    assert "0 to disable liveness output" in output
    assert attempts == []


@pytest.mark.parametrize("value", [0, 0.5, 86400])
# Keeps disabled, fractional and ordinary liveness intervals accepted by both consumers
def test_supported_liveness_values_remain_accepted(gm_module, monkeypatch, value):
    monkeypatch.setattr(gm_module, "LIVENESS_CHECK_INTERVAL", value)
    assert gm_module.runtime_liveness_error() is None
    assert not any("LIVENESS_CHECK_INTERVAL" in error for error in gm_module.runtime_configuration_errors())


@pytest.mark.skipif(os.name != "posix", reason="This failure uses POSIX directory permissions")
# Reports a real second-file failure without masking it with a temporary-file cleanup error
def test_partial_setup_save_names_saved_and_pending_files(tmp_path):
    script = '''
import os
from pathlib import Path
import sys
import github_monitor as gm
root = Path(sys.argv[1])
config_dir, env_dir = root / "config", root / "secrets"
config_dir.mkdir()
env_dir.mkdir()
config, env = config_dir / "monitor.conf", env_dir / ".env"
config.write_text("SMTP_HOST='old.example.test'\\n")
env.write_text("SMTP_PASSWORD=synthetic-old\\nKEEP=retained\\n")
state = gm.build_wizard_state(config, env)
state.values["SMTP_HOST"] = "new.example.test"
state.secrets["SMTP_PASSWORD"] = "synthetic-new"
armed = True
# Removes write permission only after every temporary file has been prepared
def fault(event, args):
    global armed
    if armed and event == "os.rename" and Path(args[1]) == config:
        armed = False
        env_dir.chmod(0o500)
sys.addaudithook(fault)
try:
    gm.save_wizard_files(state)
except gm.WizardSaveError as exc:
    print(str(exc))
finally:
    env_dir.chmod(0o700)
print("CONFIG_CHANGED:", "new.example.test" in config.read_text())
print("OLD_SECRET_RETAINED:", "synthetic-old" in env.read_text())
print("UNRELATED_RETAINED:", "KEEP=retained" in env.read_text())
'''
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path)], cwd=ROOT, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert "Saved files:" in result.stdout
    assert "Files not saved:" in result.stdout
    assert "run --setup again" in result.stdout
    assert "Remove these private temporary files" in result.stdout
    assert "CONFIG_CHANGED: True" in result.stdout
    assert "OLD_SECRET_RETAINED: True" in result.stdout
    assert "UNRELATED_RETAINED: True" in result.stdout

@pytest.mark.skipif(os.name != "posix", reason="This check uses a real POSIX terminal")
@pytest.mark.parametrize("configured,disable,expected", [(True, True, False), (True, False, True), (False, False, False)])
# Applies color precedence to the actual Doctor report on an interactive terminal
def test_doctor_terminal_respects_color_precedence(tmp_path, configured, disable, expected):
    import select
    import time
    config = tmp_path / "settings.conf"
    config.write_text(f"CLEAR_SCREEN=False\nLOCAL_TIMEZONE='UTC'\nCOLORED_OUTPUT={configured}\nERROR_NOTIFICATION=False\n", encoding="utf-8")
    script = '''
import socket
import sys
from unittest.mock import patch
import requests
import github_monitor as gm
import os
for key in gm.SECRET_KEYS:
    os.environ.pop(key, None)
# Returns an offline transport failure without replacing any Doctor helper
def offline(*args, **kwargs):
    raise requests.ConnectionError("offline")
sys.argv = ["github_monitor", *sys.argv[1:]]
with patch.object(requests.Session, "send", offline), patch.object(socket.socket, "connect", offline):
    gm.main()
'''
    master, slave = os.openpty()
    arguments = [sys.executable, "-c", script, "--doctor", "--config-file", str(config), "--env-file", "none"]
    if disable:
        arguments.append("--no-color")
    child = subprocess.Popen(arguments, cwd=ROOT, env=dict(os.environ, TERM="xterm-256color", NO_COLOR=""), stdin=slave, stdout=slave, stderr=slave)
    os.close(slave)
    captured = bytearray()
    deadline = time.monotonic() + 20
    try:
        while time.monotonic() < deadline:
            if select.select([master], [], [], 0.1)[0]:
                try:
                    data = os.read(master, 65536)
                except OSError:
                    break
                if not data:
                    break
                captured.extend(data)
            elif child.poll() is not None:
                break
        assert child.wait(timeout=2) == 1
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()
        os.close(master)
    output = captured.decode()
    assert "Doctor" in output and "Summary" in output
    assert ("\x1b[" in output) is expected
