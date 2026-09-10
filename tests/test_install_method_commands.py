"""Offline tests for install detection and copy-pasteable command rendering."""

from command_expectations import runtime_command
import shlex
import inspect
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock


# Verifies the packaged entry point renders the public command name
def test_pypi_command_uses_console_entry_point(gm_module):
    context = gm_module.InstallContext("pip", "Linux", ("github_monitor",))
    assert gm_module.render_command(["--set-github-token"], install_context=context) == "github_monitor --set-github-token"


# Verifies a value only shaped like a placeholder is quoted, so pasting the rendered command cannot run a substitution
def test_a_value_shaped_like_a_placeholder_is_quoted(gm_module):
    crafted = "<$(echo>marker)>"

    assert shlex.split(gm_module.quote_command_argument(crafted)) == [crafted]
    assert gm_module.quote_command_argument("<github_target>") == "<github_target>"


# Verifies manual detection keeps the active interpreter and absolute script path
def test_manual_detection_uses_active_interpreter(gm_module):
    script_path = "/opt/GitHub Monitor/github_monitor.py"
    context = gm_module.detect_install_context(argv0=script_path, module_path=script_path, operating_system="Linux")
    assert context.install_method == "manual"
    assert context.command_prefix == (sys.executable, str(Path(script_path).resolve()))
    assert gm_module.render_command(["octocat", "--env-file", "/tmp/private settings.env"], install_context=context) == "python3 github_monitor.py octocat --env-file '/tmp/private settings.env'"


# Verifies Windows command rendering follows the platform quoting contract
def test_windows_command_uses_windows_quoting(gm_module):
    context = gm_module.InstallContext("manual", "Windows", (r"C:\Python\python.exe", r"C:\GitHub Monitor\github_monitor.py"))
    parts = ["python", "github_monitor.py", "--config-file", r"C:\Users\Example User\github_monitor.conf"]
    assert gm_module.render_command(parts[2:], install_context=context) == subprocess.list2cmdline(parts)


# Verifies non-script invocations are recognized as the PyPI install
def test_console_invocation_is_detected_as_pip(gm_module):
    context = gm_module.detect_install_context(argv0="/usr/local/bin/github_monitor", module_path="/site-packages/github_monitor.py", operating_system="Darwin")
    assert context == gm_module.InstallContext("pip", "Darwin", (sys.executable, "-m", "github_monitor"))


# Verifies printed commands keep portable names even when detection stores exact paths
def test_manual_command_displays_portable_names(gm_module):
    context = gm_module.InstallContext("manual", "Linux", ("/usr/bin/python3", "/opt/GitHub Monitor/github_monitor.py"))
    assert gm_module.render_command(["--setup"], install_context=context) == runtime_command("python3 github_monitor.py --setup")
    assert gm_module.render_command(["octocat"], install_context=context) == "python3 github_monitor.py octocat"


# Verifies Windows welcome commands use the sibling tool's portable command names
def test_windows_manual_command_uses_portable_names(gm_module):
    context = gm_module.InstallContext("manual", "Windows", (r"C:\Python\python.exe", r"C:\GitHub Monitor\github_monitor.py"))
    assert gm_module.render_command(["<github_target>"], install_context=context) == 'python github_monitor.py <github_target>'


# Verifies secret setup prints a command for the detected install instead of a hard-coded entry point
def test_token_setup_uses_install_aware_next_command(gm_module, monkeypatch, capsys, tmp_path):
    context = gm_module.InstallContext("manual", "Linux", ("/usr/bin/python", "/opt/GitHub Monitor/github_monitor.py"))
    destination = Path("/opt/private settings.env")
    empty_config = tmp_path / "empty.conf"
    empty_config.write_text('TARGET_GITHUB_USERNAME = ""\n', encoding="utf-8")
    saved_config = tmp_path / "saved.conf"
    saved_config.write_text('TARGET_GITHUB_USERNAME = "octocat"\n', encoding="utf-8")
    monkeypatch.setattr(gm_module, "resolve_secret_env_path", Mock(return_value=destination))
    monkeypatch.setattr(gm_module, "_dotenv_contains_key", Mock(return_value=False))
    monkeypatch.setattr(gm_module, "validate_github_token", Mock(return_value="octocat"))
    update = Mock()
    monkeypatch.setattr(gm_module, "update_dotenv_file", update)

    result = gm_module.run_set_github_token(interactive=True, getpass_func=lambda prompt: "private-value", install_context=context, config_path=empty_config)
    unsaved_output = capsys.readouterr().out
    gm_module.run_set_github_token(interactive=True, getpass_func=lambda prompt: "private-value", install_context=context, config_path=saved_config)
    saved_output = capsys.readouterr().out

    assert result == str(destination)
    # Nothing supplies a target in the first run, so only the monitoring command carries the placeholder
    assert runtime_command(f"After Doctor passes, start monitoring:\n    python3 github_monitor.py <github_target> --config-file {empty_config} --env-file '/opt/private settings.env'") in unsaved_output
    assert "<github_target>" not in unsaved_output.split("After Doctor passes, start monitoring:", 1)[0]
    assert "<github_target>" not in saved_output
    assert "octocat --config-file" not in saved_output
    assert "GITHUB_USERNAME" not in unsaved_output


# Verifies recovery fix commands use the same install-aware renderer
def test_recovery_fix_uses_install_aware_command(gm_module):
    context = gm_module.InstallContext("manual", "Linux", ("/usr/bin/python", "/opt/GitHub Monitor/github_monitor.py"))
    advice = gm_module.classify_recovery_error(ValueError("invalid"), "webhook", install_context=context)
    assert advice.code == "webhook.invalid"
    assert advice.fix == gm_module.recovery_fix_with_guide(runtime_command("Check the HTTPS destination then run: python3 github_monitor.py --set-webhook-url"), gm_module.WEBHOOK_GUIDE_URL)


# Verifies the disabled dotenv search reaches the commands that accept it and stays out of the ones that refuse it
def test_a_disabled_dotenv_search_is_carried_only_where_it_is_accepted(gm_module, monkeypatch):
    context = gm_module.InstallContext("pip", "Linux", ("github_monitor",))
    monkeypatch.setattr(gm_module, "CLI_CONFIG_PATH", None)
    monkeypatch.setattr(gm_module, "DOTENV_FILE", "none")

    assert gm_module.render_command(["--doctor"], install_context=context) == "github_monitor --doctor --env-file none"
    assert gm_module.render_command(["--set-github-token"], install_context=context) == "github_monitor --set-github-token"
    assert gm_module.render_command(["--setup"], install_context=context) == "github_monitor --setup"


# Verifies the disabled config search reaches the commands that accept it and stays out of the ones that refuse it
def test_a_disabled_config_search_is_carried_only_where_it_is_accepted(gm_module, monkeypatch):
    context = gm_module.InstallContext("pip", "Linux", ("github_monitor",))
    monkeypatch.setattr(gm_module, "CLI_CONFIG_PATH", None)
    monkeypatch.setattr(gm_module, "CONFIG_DISCOVERY_DISABLED", True)
    monkeypatch.setattr(gm_module, "DOTENV_FILE", "")

    assert gm_module.render_command(["--doctor"], install_context=context) == "github_monitor --doctor --config-file none"
    assert gm_module.render_command(["--set-github-token"], install_context=context) == "github_monitor --set-github-token --config-file none"
    assert gm_module.render_command(["--setup"], install_context=context) == "github_monitor --setup"
    assert gm_module.render_command(["--doctor"], install_context=context, include_paths=False) == "github_monitor --doctor"


# Verifies a printed command carries the files this run was given, so the retest reads the settings that failed
def test_printed_commands_carry_the_files_this_run_was_given(gm_module, monkeypatch):
    context = gm_module.InstallContext("manual", "Linux", ("/usr/bin/python3", "/opt/GitHub Monitor/github_monitor.py"))
    monkeypatch.setattr(gm_module, "CLI_CONFIG_PATH", "/etc/github.conf")
    monkeypatch.setattr(gm_module, "DOTENV_FILE", "/etc/github.env")

    assert gm_module.render_command(["--set-github-token"], install_context=context) == runtime_command("python3 github_monitor.py --set-github-token --config-file /etc/github.conf --env-file /etc/github.env")
    assert gm_module.render_command(["--generate-config", "github_monitor.conf"], install_context=context, include_paths=False) == runtime_command("python3 github_monitor.py --generate-config github_monitor.conf")
    assert gm_module.render_command(["--doctor", "--config-file", "/tmp/other.conf"], install_context=context) == runtime_command("python3 github_monitor.py --doctor --config-file /tmp/other.conf --env-file /etc/github.env")


# Verifies the printed-command renderer takes the family's two shared parameters before any tool-specific one
def test_the_command_renderer_shares_one_contract(gm_module):
    parameters = list(inspect.signature(gm_module.render_command).parameters.values())
    assert [parameter.name for parameter in parameters[:2]] == ["arguments", "include_paths"]
    assert [parameter.default for parameter in parameters[:2]] == [None, True]
    # A tool-specific extra is keyword-only, so a positional call copied from a sibling cannot bind to it
    assert all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in parameters[2:])


# Verifies the renderer with no arguments prints the bare command, which is what the help screen puts before each example
def test_the_renderer_with_no_arguments_prints_the_bare_command(gm_module):
    prefix = gm_module.render_command(include_paths=False)
    assert prefix and not prefix.endswith(" ")
    assert gm_module.render_command(["--doctor"], include_paths=False) == f"{prefix} --doctor"
