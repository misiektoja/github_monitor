"""Offline tests for startup configuration precedence and early consumers."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest


# Verifies config, environment and CLI precedence before startup checks consume effective values
def test_main_resolves_configuration_before_startup_consumers(gm_module, monkeypatch, tmp_path):
    config = tmp_path / "startup.conf"
    config.write_text(
        'GITHUB_TOKEN = "config-value"\n'
        'GITHUB_API_URL = "https://config.example/api/v3"\n'
        'CHECK_INTERNET_URL = GITHUB_API_URL\n'
        "CHECK_INTERNET_TIMEOUT = 17\n"
        "CLEAR_SCREEN = False\n"
        'LOCAL_TIMEZONE = "UTC"\n'
        'WEBHOOK_PROVIDER = "ntfy"\n'
        'WEBHOOK_URL = "https://ntfy.sh/config-topic"\n',
        encoding="utf-8",
    )
    for name in ("CLI_CONFIG_PATH", "DOTENV_FILE", "GITHUB_TOKEN", "GITHUB_API_URL", "CHECK_INTERNET_URL", "CHECK_INTERNET_TIMEOUT", "CLEAR_SCREEN", "LOCAL_TIMEZONE", "WEBHOOK_PROVIDER", "WEBHOOK_URL", "stdout_bck"):
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

    monkeypatch.setattr(gm_module, "clear_screen", capture_clear)
    monkeypatch.setattr(gm_module, "check_internet", capture_connectivity)
    monkeypatch.setattr(gm_module, "send_webhook", capture_webhook)
    monkeypatch.setattr(gm_module.signal, "signal", lambda *args: None)
    monkeypatch.setattr(gm_module.sys, "argv", ["github_monitor", "--config-file", str(config), "--env-file", "none", "--github-token", "cli-value", "--github-url", "https://cli.example/api/v3", "--send-test-webhook"])

    with pytest.raises(SystemExit) as exit_error:
        gm_module.main()

    assert exit_error.value.code == 0
    assert observed == {
        "clear": False,
        "connectivity": ("https://cli.example/api/v3", "https://cli.example/api/v3", 17, "cli-value"),
        "webhook_url": "https://ntfy.sh/environment-topic",
    }


# Verifies exported secrets take precedence over the selected dotenv file
def test_exported_secrets_override_dotenv_values(gm_module, monkeypatch, tmp_path):
    dotenv = tmp_path / ".env"
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
    request_get.assert_called_once_with("https://runtime.example/health", timeout=23)
