"""Offline transcript tests for complete verbose and debug observability."""

import ast
import io
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = PROJECT_ROOT / "local" / "diagnostic_mode_test_artifacts"


# Creates one disposable diagnostic test directory under the project local directory
def make_test_directory():
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=ARTIFACT_ROOT)


class FakeResponse:
    # Stores one deterministic response for request and delivery transcripts
    def __init__(self, status_code=200, payload=None, headers=None, text=""):
        self.status_code = status_code
        self.payload = payload
        self.headers = headers or {}
        self.text = text
        self.ok = 200 <= status_code <= 299

    # Returns the configured JSON response body
    def json(self):
        return self.payload


# Configures one valid Discord destination for delivery transcript tests
def configure_webhook(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "WEBHOOK_ENABLED", True)
    monkeypatch.setattr(gm_module, "WEBHOOK_URL", "https://discord.com/api/webhooks/123/private-diagnostic-token")
    monkeypatch.setattr(gm_module, "WEBHOOK_PROVIDER", "discord")
    monkeypatch.setattr(gm_module, "WEBHOOK_USERNAME", "GitHub Monitor")
    monkeypatch.setattr(gm_module, "WEBHOOK_AVATAR_URL", "")
    monkeypatch.setattr(gm_module, "WEBHOOK_HEADERS", {})
    monkeypatch.setattr(gm_module, "WEBHOOK_TRANSFORMS", [])
    monkeypatch.setattr(gm_module, "NTFY_ACCESS_TOKEN", "")
    monkeypatch.setattr(gm_module, "WEBHOOK_PROFILE_NOTIFICATION", True)
    monkeypatch.setattr(gm_module, "WEBHOOK_TEMPLATE", {"embeds": [{"title": "{title}", "description": "{description}"}]})


# Verifies diagnostic coverage cannot regress to flags with only token call sites
def test_diagnostic_printers_keep_broad_runtime_coverage():
    source = (PROJECT_ROOT / "github_monitor.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = [node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]

    assert calls.count("debug_print") >= 70
    assert calls.count("verbose_print") >= 15
    assert source.count("debug_github_operation(") >= 40
    assert "except Exception:" not in source


# Verifies disabled diagnostic modes suppress every shared diagnostic printer
def test_diagnostic_printers_are_silent_when_disabled(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", "github_pat_disabled_diagnostic_secret")

    gm_module.debug_http_request("GET", "https://api.example.test/user", "disabled request", 5, token=gm_module.GITHUB_TOKEN)
    gm_module.verbose_degraded_feature("Profile", "profile alerts", RuntimeError("disabled failure"))

    assert capsys.readouterr().out == ""


# Verifies an outbound authentication call names its endpoint and masks its token
def test_debug_transcript_covers_outbound_call_and_response(gm_module, monkeypatch, capsys):
    token = "github_pat_diagnostic_outbound_secret"
    monkeypatch.setattr(gm_module, "DEBUG_MODE", True)
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", token)
    request_get = Mock(return_value=FakeResponse(200, {"login": "octocat"}))

    assert gm_module.validate_github_token(token, api_url="https://api.example.test", request_get=request_get) == "octocat"

    output = capsys.readouterr().out
    assert "HTTP GET https://api.example.test/user" in output
    assert "operation=GitHub token validation" in output
    assert "timeout=10s" in output
    assert "status=200" in output
    assert "token=" in output
    assert token not in output


# Verifies one swallowed request failure is visible in debug and actionable in verbose mode
def test_swallowed_exception_reports_degraded_feature(gm_module, monkeypatch, capsys):
    token = "github_pat_diagnostic_swallowed_secret"
    monkeypatch.setattr(gm_module, "DEBUG_MODE", True)
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", True)
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", token)
    monkeypatch.setattr(gm_module.req, "get", Mock(side_effect=gm_module.req.ConnectionError(f"failed with {token}")))

    assert gm_module.is_blocked_by("octocat") is None

    output = capsys.readouterr().out
    assert "Block status is unavailable, so block and unblock alerts cannot fire this cycle" in output
    assert "Block status degraded: ConnectionError" in output
    assert token not in output


# Verifies delivery diagnostics include attempts, status, retryability, wait and confirmed success
def test_delivery_transcript_covers_retry_and_outcome(gm_module, monkeypatch, capsys):
    configure_webhook(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "DEBUG_MODE", True)
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", True)
    webhook_post = Mock(side_effect=[FakeResponse(503), FakeResponse(204)])
    monkeypatch.setattr(gm_module.WEBHOOK_SESSION, "post", webhook_post)
    sleeps = []

    assert gm_module.send_webhook("Title", "Body", "profile", sleeper=sleeps.append) == 0

    output = capsys.readouterr().out
    assert "channel=discord host=https://discord.com attempt=1/2 timeout=10s" in output
    assert "attempt=1/2 status=503 retryable=True" in output
    assert "reason=webhook HTTP 503 retry attempt 2/2" in output
    assert "attempt=2/2 status=204 retryable=False" in output
    assert "outcome=success attempt=2/2" in output
    assert "Webhook delivery through discord succeeded" in output
    assert "private-diagnostic-token" not in output
    assert sleeps == [gm_module.WEBHOOK_FALLBACK_RETRY_SECONDS]


# Verifies file diagnostics cover both a successful write and a failed read branch
def test_file_transcript_covers_success_and_failure(gm_module, monkeypatch, capsys, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    destination = Path(directory.name) / ".env"
    monkeypatch.setattr(gm_module, "DEBUG_MODE", True)

    gm_module.update_dotenv_value(destination, "GITHUB_TOKEN", "private-file-value")
    with pytest.raises(IsADirectoryError):
        gm_module.update_dotenv_value(Path(directory.name), "GITHUB_TOKEN", "private-file-value")

    output = capsys.readouterr().out
    assert f"Private settings file update succeeded path={destination}" in output
    assert f"Private settings file read failed path={directory.name}" in output
    assert "IsADirectoryError" in output
    assert "private-file-value" not in output


# Verifies one poll transcript records its number, duration, interval and next scheduled wait
def test_monitor_timing_transcript_covers_poll_and_sleep(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "DEBUG_MODE", True)
    monotonic = Mock(side_effect=[10.0, 12.5])
    monkeypatch.setattr(gm_module.time, "monotonic", monotonic)

    started_at = gm_module.debug_monitor_check_start(7, "octocat")
    gm_module.debug_monitor_check_timing(7, "octocat", started_at, 60)
    gm_module.debug_monitor_wait_timing("normal monitoring interval", 60)

    output = capsys.readouterr().out
    assert "Starting monitoring check #7 for octocat" in output
    assert "Completed monitoring check #7 for octocat duration=2.500s" in output
    assert "interval=1 minute" in output
    assert "Waiting 1 minute reason=normal monitoring interval" in output
    assert "next=" in output


# Verifies config and private-setting transcripts name files, counts and sources without values
def test_config_and_secret_resolution_transcript(gm_module, monkeypatch, capsys, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config = Path(directory.name) / "github_monitor.conf"
    dotenv = Path(directory.name) / ".env"
    config.write_text('SMTP_PASSWORD = "config-private-value"\nCLEAR_SCREEN = False\n', encoding="utf-8")
    dotenv.write_text('GITHUB_TOKEN="dotenv-private-token"\nWEBHOOK_URL="https://ntfy.sh/private-diagnostic-topic"\n', encoding="utf-8")
    monkeypatch.setattr(gm_module, "DEBUG_MODE", True)
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", True)
    for name in ("DOTENV_FILE", "GITHUB_TOKEN", "SMTP_PASSWORD", "WEBHOOK_URL", "NTFY_ACCESS_TOKEN", "CLEAR_SCREEN"):
        monkeypatch.setattr(gm_module, name, getattr(gm_module, name))
    monkeypatch.setenv("NTFY_ACCESS_TOKEN", "environment-private-token")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("WEBHOOK_URL", raising=False)
    loaded = set()

    assert gm_module.load_config_file(config, loaded_names_out=loaded) is True
    assert gm_module.load_startup_secrets(str(dotenv), loaded) == str(dotenv)

    output = capsys.readouterr().out
    assert f"Reading configuration file path={config}" in output
    assert "Configuration applied" in output and "settings=2" in output
    assert f"Reading dotenv file path={dotenv}" in output
    assert "Secret resolution name=GITHUB_TOKEN source=dotenv file" in output
    assert "Secret resolution name=SMTP_PASSWORD source=configuration file" in output
    assert "Secret resolution name=NTFY_ACCESS_TOKEN source=environment" in output
    assert "Loaded 2 settings from the configuration file" in output
    for secret in ("config-private-value", "dotenv-private-token", "private-diagnostic-topic", "environment-private-token"):
        assert secret not in output


# Verifies verbose startup output expands concise rows while logs retain the complete summary
def test_startup_summary_routes_concise_full_and_log_views(gm_module):
    rows = [gm_module.StartupSummaryRow("Target", "octocat", concise=True), gm_module.StartupSummaryRow("Debug detail", "enabled", concise=False), gm_module.StartupSummaryRow("More details", "use --verbose", concise=True, full=False, log=False)]
    concise = io.StringIO()
    complete = io.StringIO()

    gm_module.emit_startup_summary(rows, show_full=False, stream=concise)
    gm_module.emit_startup_summary(rows, show_full=True, stream=complete)

    assert "Target:" in concise.getvalue()
    assert "More details:" in concise.getvalue()
    assert "Debug detail:" not in concise.getvalue()
    assert "Target:" in complete.getvalue()
    assert "Debug detail:" in complete.getvalue()
    assert "More details:" not in complete.getvalue()


@pytest.mark.parametrize("mode", ["--verbose", "--debug"])
# Drives a broken target through main and verifies each mode produces useful user-visible output
def test_broken_target_transcript_exercises_real_cli_path(gm_module, monkeypatch, capsys, request, mode):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config = Path(directory.name) / "github_monitor.conf"
    config.write_text('GITHUB_TOKEN = "github_pat_broken_target_secret"\nGITHUB_API_URL = "https://api.example.test"\nCHECK_INTERNET_URL = GITHUB_API_URL\nCHECK_INTERNET_TIMEOUT = 4\nCLEAR_SCREEN = False\nLOCAL_TIMEZONE = "UTC"\nDISABLE_LOGGING = True\nVERBOSE_MODE = False\nDEBUG_MODE = False\n', encoding="utf-8")

    class MissingTargetGithub:
        # Accepts the real client constructor settings without making a network call
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        # Raises the same exception as GitHub for a missing user
        def get_user(self, login=None):
            raise gm_module.UnknownObjectException(404, {"message": "Not Found"})

    monkeypatch.setattr(gm_module, "Github", MissingTargetGithub)
    for name in ("CLI_CONFIG_PATH", "DOTENV_FILE", "GITHUB_TOKEN", "GITHUB_API_URL", "CHECK_INTERNET_URL", "CHECK_INTERNET_TIMEOUT", "CLEAR_SCREEN", "LOCAL_TIMEZONE", "DISABLE_LOGGING", "VERBOSE_MODE", "DEBUG_MODE", "SECRET_SOURCES"):
        monkeypatch.setattr(gm_module, name, getattr(gm_module, name))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(gm_module.req, "get", Mock(return_value=FakeResponse(200)))
    monkeypatch.setattr(gm_module.signal, "signal", lambda *args: None)
    monkeypatch.setattr(gm_module.sys, "argv", ["github_monitor", "missing-user", "--config-file", str(config), "--env-file", "none", "--list-repos", mode])

    with pytest.raises(SystemExit) as exit_error:
        gm_module.main()

    assert exit_error.value.code == 1
    output = capsys.readouterr().out
    assert "Recovery code: target.not_found" in output
    assert "github_pat_broken_target_secret" not in output
    if mode == "--debug":
        assert "HTTP GET https://api.example.test operation=startup connectivity timeout=4s" in output
        assert "PyGithub client operation=repository listing endpoint=https://api.example.test timeout=15s token=" in output
        assert "PyGithub operation=user profile lookup" in output
        assert "Technical detail:" in output
    else:
        assert "Loaded 9 settings from the configuration file" in output
        assert "[DEBUG " not in output
