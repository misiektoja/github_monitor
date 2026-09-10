"""Offline tests for startup configuration precedence and early consumers."""

import tempfile
from pathlib import Path
import argparse
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = PROJECT_ROOT / "local" / "startup_configuration_test_artifacts"


# Creates one disposable startup test directory under the project local directory
def make_test_directory():
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=ARTIFACT_ROOT)


# Verifies config, environment and CLI precedence before startup checks consume effective values
def test_main_resolves_configuration_before_startup_consumers(gm_module, monkeypatch, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config = Path(directory.name) / "startup.conf"
    config.write_text(
        'GITHUB_TOKEN = "config-value"\n'
        'GITHUB_API_URL = "https://config.example/api/v3"\n'
        'CHECK_INTERNET_URL = GITHUB_API_URL\n'
        "CHECK_INTERNET_TIMEOUT = 17\n"
        "CLEAR_SCREEN = False\n"
        'LOCAL_TIMEZONE = "UTC"\n'
        'WEBHOOK_PROVIDER = "ntfy"\n'
        'WEBHOOK_URL = "https://ntfy.sh/config-topic"\n'
        'VERBOSE_MODE = False\n'
        'DEBUG_MODE = False\n',
        encoding="utf-8",
    )
    for name in ("CLI_CONFIG_PATH", "DOTENV_FILE", "GITHUB_TOKEN", "GITHUB_API_URL", "CHECK_INTERNET_URL", "CHECK_INTERNET_TIMEOUT", "CLEAR_SCREEN", "LOCAL_TIMEZONE", "WEBHOOK_PROVIDER", "WEBHOOK_URL", "VERBOSE_MODE", "DEBUG_MODE", "stdout_bck"):
        monkeypatch.setattr(gm_module, name, getattr(gm_module, name))
    monkeypatch.setenv("GITHUB_TOKEN", "environment-value")
    monkeypatch.setenv("WEBHOOK_URL", "https://ntfy.sh/environment-topic")
    observed = {}

    def capture_clear(enabled):
        observed["clear"] = enabled

    def capture_connectivity():
        observed["connectivity"] = (gm_module.GITHUB_API_URL, gm_module.CHECK_INTERNET_URL, gm_module.CHECK_INTERNET_TIMEOUT, gm_module.GITHUB_TOKEN)
        return True

    def capture_webhook(*args, **kwargs):
        observed["webhook_url"] = gm_module.WEBHOOK_URL
        return 0

    real_load_config_file = gm_module.load_config_file

    def capture_config_load(*args, **kwargs):
        observed["diagnostics_during_config_load"] = (gm_module.VERBOSE_MODE, gm_module.DEBUG_MODE)
        return real_load_config_file(*args, **kwargs)

    monkeypatch.setattr(gm_module, "load_config_file", capture_config_load)
    monkeypatch.setattr(gm_module, "clear_screen", capture_clear)
    monkeypatch.setattr(gm_module, "check_internet", capture_connectivity)
    monkeypatch.setattr(gm_module, "send_webhook", capture_webhook)
    monkeypatch.setattr(gm_module.signal, "signal", lambda *args: None)
    monkeypatch.setattr(gm_module.sys, "argv", ["github_monitor", "--config-file", str(config), "--env-file", "none", "--github-token", "cli-value", "--github-url", "https://cli.example/api/v3", "--verbose", "--debug", "--send-test-webhook"])

    with pytest.raises(SystemExit) as exit_error:
        gm_module.main()

    assert exit_error.value.code == 0
    assert observed == {
        "clear": False,
        "diagnostics_during_config_load": (True, True),
        "connectivity": ("https://cli.example/api/v3", "https://cli.example/api/v3", 17, "cli-value"),
        "webhook_url": "https://ntfy.sh/environment-topic",
    }
    assert gm_module.VERBOSE_MODE is True
    assert gm_module.DEBUG_MODE is True


# Verifies exported secrets take precedence over the selected dotenv file
def test_exported_secrets_override_dotenv_values(gm_module, monkeypatch, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    dotenv = Path(directory.name) / ".env"
    dotenv.write_text('GITHUB_TOKEN="dotenv-value"\nWEBHOOK_URL="https://ntfy.sh/dotenv-topic"\n', encoding="utf-8")
    monkeypatch.setattr(gm_module, "DOTENV_FILE", "")
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", "config-value")
    monkeypatch.setattr(gm_module, "WEBHOOK_URL", "https://ntfy.sh/config-topic")
    monkeypatch.setenv("GITHUB_TOKEN", "environment-value")
    monkeypatch.delenv("WEBHOOK_URL", raising=False)

    env_path = gm_module.load_startup_secrets(str(dotenv))

    assert env_path == str(dotenv)
    assert gm_module.GITHUB_TOKEN == "environment-value"
    assert gm_module.WEBHOOK_URL == "https://ntfy.sh/dotenv-topic"


# Verifies an empty export is treated as absent, so a shell-profile leftover does not blank the dotenv value
def test_an_empty_export_does_not_shadow_the_dotenv_value(gm_module, monkeypatch, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    dotenv = Path(directory.name) / ".env"
    dotenv.write_text('GITHUB_TOKEN="dotenv-value"\n', encoding="utf-8")
    monkeypatch.setattr(gm_module, "DOTENV_FILE", "")
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", "config-value")
    monkeypatch.setenv("GITHUB_TOKEN", "")

    gm_module.load_startup_secrets(str(dotenv))

    assert gm_module.GITHUB_TOKEN == "dotenv-value"


# Verifies an unedited placeholder is never reported as a configured secret, whichever layer carried it
def test_placeholder_secrets_are_not_reported_as_configured(gm_module, monkeypatch, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    dotenv = Path(directory.name) / ".env"
    dotenv.write_text('GITHUB_TOKEN="real-token-value"\n', encoding="utf-8")
    monkeypatch.setattr(gm_module, "DOTENV_FILE", "")
    monkeypatch.setattr(gm_module, "SECRET_SOURCES", {})
    monkeypatch.setattr(gm_module, "WEBHOOK_URL", "your_webhook_url")
    monkeypatch.setattr(gm_module, "SMTP_PASSWORD", "your_smtp_password")
    monkeypatch.setattr(gm_module, "NTFY_ACCESS_TOKEN", "   ")
    for name in gm_module.SECRET_KEYS:
        monkeypatch.delenv(name, raising=False)

    gm_module.load_startup_secrets(str(dotenv), {"WEBHOOK_URL", "SMTP_PASSWORD"})

    assert gm_module.SECRET_SOURCES == {"GITHUB_TOKEN": "dotenv file"}
    assert gm_module.startup_secret_buckets() == (["GITHUB_TOKEN"], [], [], [])


# Verifies the summary rows name only the secrets that carry a real value
def test_the_summary_rows_skip_placeholder_secrets(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "SECRET_SOURCES", {"GITHUB_TOKEN": "dotenv file", "WEBHOOK_URL": "configuration file"})
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", "real-token-value")
    monkeypatch.setattr(gm_module, "WEBHOOK_URL", "your_webhook_url")

    assert gm_module.startup_secret_buckets() == (["GITHUB_TOKEN"], [], [], [])


# Verifies explicit debug mode is active while an invalid config is being loaded, and that the offending setting is
# named once rather than repeated by a technical detail that only echoes the summary
def test_debug_flag_exposes_sanitized_config_loader_detail(request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config = Path(directory.name) / "invalid.conf"
    config.write_text("DEBUG_MODE = False\nNOT_A_REAL_SETTING = 1\n", encoding="utf-8")

    result = subprocess.run([sys.executable, str(PROJECT_ROOT / "github_monitor.py"), "--debug", "--config-file", str(config)], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    assert result.returncode == 1
    assert "* Error: " in result.stdout
    assert "NOT_A_REAL_SETTING" in result.stdout
    assert "Configuration load: " in result.stdout, "the debug diagnostic line reports the failed load"
    assert "Technical detail:" not in result.stdout, "the detail here only repeats the summary"


# Verifies an explicitly configured connectivity endpoint stays independent from the GitHub API override
def test_explicit_connectivity_url_is_not_replaced_by_cli_api(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", "environment-value")
    monkeypatch.setattr(gm_module, "GITHUB_API_URL", "https://config.example/api/v3")
    monkeypatch.setattr(gm_module, "CHECK_INTERNET_URL", "https://status.example/health")
    args = SimpleNamespace(github_token=None, github_url="https://cli.example/api/v3")

    gm_module.apply_startup_cli_overrides(args, {"GITHUB_API_URL", "CHECK_INTERNET_URL"})

    assert gm_module.GITHUB_API_URL == "https://cli.example/api/v3"
    assert gm_module.CHECK_INTERNET_URL == "https://status.example/health"


# Verifies connectivity defaults are read when the check runs instead of when the module imports
def test_connectivity_check_uses_effective_runtime_defaults(gm_module, monkeypatch):
    request_get = Mock(return_value=object())
    monkeypatch.setattr(gm_module.req, "get", request_get)
    monkeypatch.setattr(gm_module, "CHECK_INTERNET_URL", "https://runtime.example/health")
    monkeypatch.setattr(gm_module, "CHECK_INTERNET_TIMEOUT", 23)

    assert gm_module.check_internet() is True
    request_get.assert_called_once_with("https://runtime.example/health", timeout=23, verify=True)


# Drives the real command line up to the monitoring call and returns the webhook state startup settled on
def webhook_state_after_startup(gm_module, monkeypatch, request, webhook_url):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config = Path(directory.name) / "webhook.conf"
    config.write_text('CLEAR_SCREEN = False\nDISABLE_LOGGING = True\nWEBHOOK_ENABLED = True\nWEBHOOK_PROVIDER = "ntfy"\n' + f'WEBHOOK_URL = "{webhook_url}"\n', encoding="utf-8")
    for name in gm_module.SECRET_KEYS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GITHUB_TOKEN", "test-token-value")
    monkeypatch.setattr(gm_module, "WEBHOOK_ENABLED", False, raising=False)
    monkeypatch.setattr(gm_module, "WEBHOOK_URL", "", raising=False)
    monkeypatch.setattr(gm_module, "check_internet", lambda *args, **kwargs: True)
    monkeypatch.setattr(gm_module.signal, "signal", lambda *args: None)

    def stop_before_monitoring(*_args, **_kwargs):
        raise SystemExit(0)

    monkeypatch.setattr(gm_module, "github_monitor_user", stop_before_monitoring)
    monkeypatch.setattr(gm_module.sys, "argv", ["github_monitor", "misiektoja", "--config-file", str(config), "--env-file", "none"])

    with pytest.raises(SystemExit) as exit_error:
        gm_module.main()

    assert exit_error.value.code == 0
    return gm_module.WEBHOOK_ENABLED


# Verifies an unedited webhook destination switches the channel off instead of being treated as configured
def test_a_placeholder_webhook_url_switches_the_channel_off(gm_module, monkeypatch, request, restored_globals):
    assert webhook_state_after_startup(gm_module, monkeypatch, request, "your_webhook_url") is False


# Verifies a real destination still leaves the webhook channel on
def test_a_configured_webhook_url_keeps_the_channel_on(gm_module, monkeypatch, request, restored_globals):
    assert webhook_state_after_startup(gm_module, monkeypatch, request, "https://ntfy.sh/some-topic") is True


# Verifies each source that can supply a secret gets its own bucket, so none of them is filed under another
@pytest.mark.parametrize("source, position", [("dotenv file", 0), ("environment", 1), ("configuration file", 2), ("command line", 3)])
def test_each_secret_source_lands_in_its_own_bucket(gm_module, monkeypatch, source, position):
    for name in gm_module.SECRET_KEYS:
        monkeypatch.setattr(gm_module, name, "your_placeholder", raising=False)
    monkeypatch.setattr(gm_module, "SECRET_SOURCES", {"GITHUB_TOKEN": source})
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", "real-token-value")

    buckets = gm_module.startup_secret_buckets()

    assert buckets[position] == ["GITHUB_TOKEN"]
    assert [names for index, names in enumerate(buckets) if index != position] == [[], [], []]


# Verifies the summary reports a command-line secret under the command line rather than the configuration file
def test_a_command_line_secret_is_not_reported_as_a_config_file_secret(gm_module, monkeypatch):
    for name in gm_module.SECRET_KEYS:
        monkeypatch.setattr(gm_module, name, "your_placeholder", raising=False)
    monkeypatch.setattr(gm_module, "SECRET_SOURCES", {"GITHUB_TOKEN": "command line"})
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", "real-token-value")

    rows = {row.label: row.value for row in gm_module.build_startup_summary("someuser", None, None, None)}

    assert rows["Secrets from command line"] == "GITHUB_TOKEN"
    assert rows["Secrets from config file"] == "None"


# Verifies the liveness reminder follows the configured interval whatever the check interval is
@pytest.mark.parametrize("check_interval,liveness_interval,expected", [(1800, 43200, 43200), (86400, 43200, 43200), (1800, 0, 0)])
def test_the_liveness_reminder_follows_the_configured_interval(gm_module, monkeypatch, check_interval, liveness_interval, expected):
    monkeypatch.setattr(gm_module, "LIVENESS_CHECK_INTERVAL", liveness_interval)
    monkeypatch.setattr(gm_module, "LIVENESS_REMINDER_SECONDS", 99)
    args = argparse.Namespace(check_interval=check_interval, csv_file=None, disable_logging=False, get_all_repos=False, no_monitor_events=False, notify_daily_contribs=False, notify_errors=False, notify_events=False, notify_profile=False, notify_repo_changes=False, notify_repo_update_date=False, repos=None, track_contribs_changes=False, track_repos_changes=False)

    gm_module.apply_monitoring_cli_overrides(args, argparse.ArgumentParser())

    assert gm_module.LIVENESS_REMINDER_SECONDS == expected


# Verifies a first run without a username is told about the target before it is told about the token
def test_a_missing_username_is_reported_before_the_token():
    result = subprocess.run([sys.executable, str(PROJECT_ROOT / "github_monitor.py"), "--config-file", "none", "--env-file", "none"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    output = result.stdout + result.stderr
    assert result.returncode == 1
    assert "* Error: No GitHub username was provided" in output
    assert "No usable GitHub token is configured" not in output
