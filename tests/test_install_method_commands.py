"""Offline tests for install detection and copy-pasteable command rendering."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock


# Verifies the packaged entry point renders the public command name
def test_pypi_command_uses_console_entry_point(gm_module):
    context = gm_module.InstallContext("pip", "Linux", ("github_monitor",))
    assert gm_module.render_install_command(["--set-github-token"], context) == "github_monitor --set-github-token"


# Verifies manual detection keeps the active interpreter and absolute script path
def test_manual_detection_uses_active_interpreter(gm_module):
    script_path = "/opt/GitHub Monitor/github_monitor.py"
    context = gm_module.detect_install_context(argv0=script_path, module_path=script_path, operating_system="Linux")
    assert context.install_method == "manual"
    assert context.command_prefix == (sys.executable, str(Path(script_path).resolve()))
    assert gm_module.render_install_command(["octocat", "--env-file", "/tmp/private settings.env"], context, exact=True) == f"{sys.executable} '/opt/GitHub Monitor/github_monitor.py' octocat --env-file '/tmp/private settings.env'"


# Verifies Windows command rendering follows the platform quoting contract
def test_windows_command_uses_windows_quoting(gm_module):
    context = gm_module.InstallContext("manual", "Windows", (r"C:\Python\python.exe", r"C:\GitHub Monitor\github_monitor.py"))
    parts = [*context.command_prefix, "--config-file", r"C:\Users\Example User\github_monitor.conf"]
    assert gm_module.render_install_command(parts[2:], context, exact=True) == subprocess.list2cmdline(parts)


# Verifies non-script invocations are recognized as the PyPI install
def test_console_invocation_is_detected_as_pip(gm_module):
    context = gm_module.detect_install_context(argv0="/usr/local/bin/github_monitor", module_path="/site-packages/github_monitor.py", operating_system="Darwin")
    assert context == gm_module.InstallContext("pip", "Darwin", ("github_monitor",))


# Verifies printed commands use portable names by default and the exact form only when asked
def test_manual_command_supports_portable_and_exact_forms(gm_module):
    context = gm_module.InstallContext("manual", "Linux", ("/usr/bin/python3", "/opt/GitHub Monitor/github_monitor.py"))
    assert gm_module.render_install_command(["--setup"], context) == "python3 github_monitor.py --setup"
    assert gm_module.render_install_command(["octocat"], context, exact=True) == "/usr/bin/python3 '/opt/GitHub Monitor/github_monitor.py' octocat"


# Verifies Windows welcome commands use the sibling tool's portable command names
def test_windows_manual_command_uses_portable_names(gm_module):
    context = gm_module.InstallContext("manual", "Windows", (r"C:\Python\python.exe", r"C:\GitHub Monitor\github_monitor.py"))
    assert gm_module.render_install_command(["<github_target>"], context, exact=False) == 'python github_monitor.py <github_target>'


# Verifies secret setup prints a command for the detected install instead of a hard-coded entry point
def test_token_setup_uses_install_aware_next_command(gm_module, monkeypatch, capsys):
    context = gm_module.InstallContext("manual", "Linux", ("/usr/bin/python", "/opt/GitHub Monitor/github_monitor.py"))
    destination = Path("/opt/private settings.env")
    monkeypatch.setattr(gm_module, "resolve_secret_env_path", Mock(return_value=destination))
    monkeypatch.setattr(gm_module, "dotenv_contains_key", Mock(return_value=False))
    monkeypatch.setattr(gm_module, "validate_github_token", Mock(return_value="octocat"))
    update = Mock()
    monkeypatch.setattr(gm_module, "update_dotenv_value", update)

    result = gm_module.run_set_github_token(interactive=True, getpass_func=lambda prompt: "private-value", install_context=context)

    assert result == str(destination)
    assert "After Doctor passes, start monitoring:\n    python3 github_monitor.py GITHUB_USERNAME --env-file '/opt/private settings.env'" in capsys.readouterr().out
    update.assert_called_once_with(destination, "GITHUB_TOKEN", "private-value")


# Verifies recovery fix commands use the same install-aware renderer
def test_recovery_fix_uses_install_aware_command(gm_module):
    context = gm_module.InstallContext("manual", "Linux", ("/usr/bin/python", "/opt/GitHub Monitor/github_monitor.py"))
    advice = gm_module.classify_recovery_error(ValueError("invalid"), "webhook", context)
    assert advice.code == "webhook.invalid"
    assert advice.fix == "Check the HTTPS destination then run: python3 github_monitor.py --set-webhook-url"


# Verifies a printed command carries the files this run was given, so the retest reads the settings that failed
def test_printed_commands_carry_the_files_this_run_was_given(gm_module, monkeypatch):
    context = gm_module.InstallContext("manual", "Linux", ("/usr/bin/python3", "/opt/GitHub Monitor/github_monitor.py"))
    monkeypatch.setattr(gm_module, "CLI_CONFIG_PATH", "/etc/github.conf")
    monkeypatch.setattr(gm_module, "DOTENV_FILE", "/etc/github.env")

    assert gm_module.render_install_command(["--set-github-token"], context) == "python3 github_monitor.py --set-github-token --config-file /etc/github.conf --env-file /etc/github.env"
    assert gm_module.render_install_command(["--generate-config", "github_monitor.conf"], context, include_paths=False) == "python3 github_monitor.py --generate-config github_monitor.conf"
    assert gm_module.render_install_command(["--doctor", "--config-file", "/tmp/other.conf"], context) == "python3 github_monitor.py --doctor --config-file /tmp/other.conf --env-file /etc/github.env"
