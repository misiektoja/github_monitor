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
    assert calls.count("verbose_print") + calls.count("verbose_delivery_print") >= 10
    assert source.count("debug_github_operation(") >= 40
    assert "except Exception:" not in source


# Verifies the completed check stays a debug trace, since one verbose line per cycle buried the events worth reading
def test_the_completed_check_is_a_debug_only_trace(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "DEBUG_MODE", False)
    gm_module.debug_monitor_check_timing(1, "watched", gm_module.time.monotonic(), 30, outcome="degraded")
    assert capsys.readouterr().out == ""
    monkeypatch.setattr(gm_module, "DEBUG_MODE", True)
    gm_module.debug_monitor_check_timing(1, "watched", gm_module.time.monotonic(), 30, outcome="degraded")
    output = capsys.readouterr().out
    assert "Completed monitoring check" in output
    assert "degraded" in output


# Verifies a verbose notice prints its lines then closes the block with the shared timestamp trailer
def test_a_verbose_notice_closes_its_block(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", True)
    monkeypatch.setattr(gm_module, "MONITORING_ACTIVE", True)

    gm_module.verbose_notice("first notice", "second notice")

    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert lines[0] == "* first notice"
    assert lines[1] == "* second notice"
    assert lines[2].startswith("Timestamp:")
    assert set(lines[3]) == {"\u2500"}


# Verifies a notice printed before monitoring starts stays a bare line, since the monitoring header closes that block
def test_a_verbose_notice_stays_bare_on_the_startup_screen(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", True)
    monkeypatch.setattr(gm_module, "MONITORING_ACTIVE", False)

    gm_module.verbose_notice("first notice")

    assert capsys.readouterr().out == "* first notice\n"


# Verifies a degraded feature reported during monitoring is closed once by the check instead of by each line
def test_degraded_feature_lines_are_closed_once_by_the_check(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", True)
    monkeypatch.setattr(gm_module, "MONITORING_ACTIVE", True)
    monkeypatch.setattr(gm_module, "PENDING_NOTICE_BLOCK", False)

    gm_module.verbose_degraded_feature("Block status", "block and unblock alerts")
    gm_module.verbose_degraded_feature("Starred repository count", "starred repository change alerts")
    gm_module.close_pending_notice_block()

    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert lines[0] == "* Block status: unavailable, so block and unblock alerts cannot fire"
    assert lines[1] == "* Starred repository count: unavailable, so starred repository change alerts cannot fire"
    assert lines[2].startswith("Timestamp:")
    assert set(lines[3]) == {"\u2500"}


# Verifies a report that closes its own block absorbs a degraded line printed inside it, so no extra trailer follows
def test_a_report_trailer_absorbs_a_degraded_line_printed_inside_it(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", True)
    monkeypatch.setattr(gm_module, "MONITORING_ACTIVE", True)
    monkeypatch.setattr(gm_module, "PENDING_NOTICE_BLOCK", False)

    gm_module.verbose_degraded_feature("Event payload", "complete event notification details")
    gm_module.print_cur_ts("Timestamp:\t\t\t")
    capsys.readouterr()

    gm_module.close_pending_notice_block()

    assert capsys.readouterr().out == ""


# Verifies a lasting outage is reported on the check it starts rather than on every check it continues
def test_a_lasting_degraded_feature_is_reported_once(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", True)
    monkeypatch.setattr(gm_module, "MONITORING_ACTIVE", True)

    for _ in range(3):
        gm_module.verbose_degraded_feature("Block status", "block and unblock alerts")
        gm_module.report_recovered_features()

    output = capsys.readouterr().out
    assert output.count("Block status: unavailable, so block and unblock alerts cannot fire") == 1
    assert "is available again" not in output


# Verifies a feature that works again is reported once, so verbose says when the alert can fire again
def test_a_recovered_feature_is_reported_once(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", True)
    monkeypatch.setattr(gm_module, "MONITORING_ACTIVE", True)

    gm_module.verbose_degraded_feature("Block status", "block and unblock alerts")
    gm_module.report_recovered_features()
    capsys.readouterr()

    gm_module.report_recovered_features()
    gm_module.report_recovered_features()

    output = capsys.readouterr().out
    assert output.count("Block status: available again, so block and unblock alerts can fire again") == 1


# Verifies a verbose notice stays silent while verbose mode is off, so the trailer cannot leak into a quiet run
def test_a_verbose_notice_is_silent_while_verbose_is_off(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", False)

    gm_module.verbose_notice("nothing to see")

    assert capsys.readouterr().out == ""


# Verifies the one loop-level notice goes through the helper rather than printing a line with no timestamp
def test_the_initial_snapshot_notice_closes_its_block():
    source = (PROJECT_ROOT / "github_monitor.py").read_text(encoding="utf-8")

    assert 'verbose_notice(f"Initial snapshot completed for {user}")' in source


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
    assert "HTTP GET: url=https://api.example.test/user" in output
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
    assert "Block status: unavailable, so block and unblock alerts cannot fire" in output
    assert "Block status: outcome=degraded, error=ConnectionError" in output
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
    assert "channel=discord, host=https://discord.com, attempt=1/2, timeout=10s" in output
    assert "attempt=1/2, status=503, retryable=True" in output
    assert "reason=webhook HTTP 503 retry attempt 2/2" in output
    assert "attempt=2/2, status=204, retryable=False" in output
    assert "outcome=OK, attempt=2/2" in output
    assert "Webhook sent through Discord" in output
    assert "private-diagnostic-token" not in output
    assert sleeps == [gm_module.WEBHOOK_FALLBACK_RETRY_SECONDS]


# Verifies file diagnostics cover both a successful write and a failed read branch
def test_file_transcript_covers_success_and_failure(gm_module, monkeypatch, capsys, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    destination = Path(directory.name) / ".env"
    monkeypatch.setattr(gm_module, "DEBUG_MODE", True)

    gm_module.update_dotenv_file(destination, {"GITHUB_TOKEN": "private-file-value"})
    with pytest.raises(IsADirectoryError):
        gm_module.update_dotenv_file(Path(directory.name), {"GITHUB_TOKEN": "private-file-value"})

    output = capsys.readouterr().out
    assert f"Private settings file update succeeded: path={destination}" in output
    # The read covers the whole file rather than one key, so the line names the path and what went wrong
    assert f"Private settings file read: path={directory.name}, outcome=failed" in output
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
    assert "Starting monitoring check: check=#7, user=octocat" in output
    assert "Completed monitoring check: check=#7, user=octocat, outcome=OK, duration=2.500s" in output
    assert "interval=1 minute" in output
    assert "Waiting: interval=1 minute, reason=normal monitoring interval" in output
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
    assert f"Reading configuration file: path={config}" in output
    assert "Configuration applied" in output and "settings=2" in output
    assert f"Reading dotenv file: path={dotenv}" in output
    assert "Secret resolution: name=GITHUB_TOKEN, source=dotenv file, value=set" in output
    assert "Secret resolution: name=SMTP_PASSWORD, source=configuration file, value=set" in output
    assert "Secret resolution: name=NTFY_ACCESS_TOKEN, source=environment, value=set" in output
    # The settings count is a mechanical detail, so it belongs to debug rather than to the verbose narration
    assert "Loaded 2 settings from the configuration file" not in output
    for secret in ("config-private-value", "dotenv-private-token", "private-diagnostic-topic", "environment-private-token"):
        assert secret not in output


# Verifies verbose startup output expands concise rows while logs retain the complete summary
def test_startup_summary_routes_concise_full_and_log_views(gm_module):
    rows = [gm_module.StartupSummaryRow("Target", "octocat", concise=True), gm_module.StartupSummaryRow("Debug detail", "enabled", concise=False), gm_module.StartupSummaryRow("More details", "use --verbose", concise=True, full=False)]
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


# Records what a split destination was asked to put on the terminal and what it was asked to put in the log
class RecordingSplitStream:
    def __init__(self):
        self.terminal = []
        self.log = []
        self.plain = []
        self.flushes = 0

    # Takes the rows meant for the screen
    def terminal_only(self, line):
        self.terminal.append(line)

    # Takes the rows meant for the log file
    def log_only(self, line):
        self.log.append(line)

    # Takes anything written without choosing a destination
    def write(self, line):
        self.plain.append(line)

    # Counts the flushes so the plain and the split paths can be told apart
    def flush(self):
        self.flushes += 1


# Verifies the log keeps the complete summary whatever the terminal was shown, which is what makes a log
# attached to a bug report carry every effective setting
def test_the_log_keeps_the_full_summary_whatever_the_terminal_showed(gm_module):
    rows = [gm_module.StartupSummaryRow("Target", "octocat", concise=True), gm_module.StartupSummaryRow("Debug detail", "enabled", concise=False)]
    destination = RecordingSplitStream()

    gm_module.emit_startup_summary(rows, show_full=False, stream=destination)

    assert "Target:" in "".join(destination.terminal)
    assert "Debug detail:" not in "".join(destination.terminal)
    assert "Debug detail:" in "".join(destination.log)
    assert destination.plain == [], "a destination that splits its output was written to directly"
    assert destination.flushes == 0, "a split destination flushes itself"


# Records what a destination with no separate log was written to, which is what a redirected stdout looks like
class RecordingPlainStream:
    def __init__(self):
        self.plain = []
        self.flushes = 0

    # Takes everything, since this destination has no second half to route to
    def write(self, line):
        self.plain.append(line)

    # Counts the flushes so the plain and the split paths can be told apart
    def flush(self):
        self.flushes += 1


# Verifies a destination that cannot split is written to and flushed, since nothing else closes the block
def test_a_plain_destination_is_written_to_and_flushed(gm_module):
    rows = [gm_module.StartupSummaryRow("Target", "octocat", concise=True), gm_module.StartupSummaryRow("Debug detail", "enabled", concise=False)]
    destination = RecordingPlainStream()

    gm_module.emit_startup_summary(rows, show_full=False, stream=destination)

    assert "Target:" in "".join(destination.plain)
    assert "Debug detail:" not in "".join(destination.plain)
    assert destination.flushes == 1


# Verifies a shorter progress line paints over the longer one before it, since the bar is redrawn in place and
# whatever the previous line left behind would otherwise stay on screen
def test_a_shorter_progress_line_is_padded_over_the_previous_one(gm_module, monkeypatch):
    terminal = RecordingSplitStream()
    monkeypatch.setattr(gm_module, "stdout_bck", terminal)
    monkeypatch.setattr(gm_module.shutil, "get_terminal_size", lambda fallback=(80, 20): type("Size", (), {"columns": 200})())
    monkeypatch.setattr(gm_module, "_progress_line_width", 0)

    gm_module._display_progress(1, 2, "a-long-repository-name")
    long_line = terminal.plain[-1]
    gm_module._display_progress(2, 2, "short")
    short_line = terminal.plain[-1]

    assert "a-long-repository-name" in long_line
    assert short_line.rstrip(" ").endswith("short")
    # The shorter line is padded out to the width of the one it replaces, so none of the longer name survives
    assert len(short_line) == len(long_line)


# Verifies the concise output row does not repeat the path the full view already carries as Output logging
def test_the_output_row_does_not_repeat_the_log_path(gm_module):
    rows = gm_module.build_startup_summary("octocat", "github_monitor.conf", ".env", "github_monitor_octocat.log")
    output = next(row for row in rows if row.label == "Output")
    output_logging = next(row for row in rows if row.label == "Output logging")

    assert (output.concise, output.full) == (True, False)
    assert output_logging.full is True
    assert "github_monitor_octocat.log" in output_logging.value


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
    assert "* Error: GitHub could not find the requested resource" in output
    assert "To fix: Check the target name and token access then try again" in output
    assert "github_pat_broken_target_secret" not in output
    if mode == "--debug":
        assert "HTTP GET: url=https://api.example.test, operation=startup connectivity, timeout=4s" in output
        assert "PyGithub client: operation=repository listing, endpoint=https://api.example.test, timeout=15s, token=" in output
        assert "PyGithub: operation=user profile lookup" in output
        assert "Technical detail:" in output
    else:
        # --list-repos exits before the notification gates, so verbose has only the recovery block to show here
        assert "Loaded 9 settings from the configuration file" not in output
        assert "[DEBUG " not in output


# The diagnostic line is documented as an operation followed by comma-separated key=value fields
@pytest.mark.parametrize("value, expected", [
    ("github_pat_a_real_looking_token", {"value": "set"}),
    ("your_github_token", {"value": "not set"}),
    ("", {"value": "not set"}),
    (None, {"value": "not set"}),
])
def test_no_secret_field_value_carries_a_comma(gm_module, value, expected):
    assert gm_module.secret_fields(value) == expected
    assert all("," not in str(part) for part in expected.values())


# A source outside the set is a typo rather than a new layer, so it is rejected instead of reaching the summary
def test_an_unsupported_secret_source_is_refused(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "SECRET_SOURCES", {})

    with pytest.raises(ValueError, match="Unsupported secret source"):
        gm_module.record_secret_source("GITHUB_TOKEN", "somewhere else", "github_pat_value")

    assert gm_module.SECRET_SOURCES == {}


# A placeholder is not a value, so recording it clears the earlier answer rather than adding a row
def test_a_placeholder_clears_the_recorded_source(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "SECRET_SOURCES", {"GITHUB_TOKEN": "dotenv file"})

    gm_module.record_secret_source("GITHUB_TOKEN", "command line", "your_github_token")

    assert gm_module.SECRET_SOURCES == {}


# The secret trace is one operation followed by fields, which a hand-written line silently broke for command-line secrets
@pytest.mark.parametrize("extra_args, expected", [
    (["--github-token", "github_pat_command_line_secret", "--webhook-url", "https://ntfy.sh/command-line-topic"], ["GITHUB_TOKEN", "WEBHOOK_URL"]),
    (["--webhook-url", "https://ntfy.sh/command-line-topic"], ["WEBHOOK_URL"]),
])
def test_a_command_line_secret_is_traced_as_fields(gm_module, monkeypatch, capsys, request, extra_args, expected):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config = Path(directory.name) / "github_monitor.conf"
    config.write_text('GITHUB_API_URL = "https://api.example.test"\nCHECK_INTERNET_URL = GITHUB_API_URL\nCLEAR_SCREEN = False\nLOCAL_TIMEZONE = "UTC"\nDISABLE_LOGGING = True\n', encoding="utf-8")

    class MissingTargetGithub:
        # Accepts the real client constructor settings without making a network call
        def __init__(self, *args, **kwargs):
            pass

        # Raises the same exception as GitHub for a missing user
        def get_user(self, login=None):
            raise gm_module.UnknownObjectException(404, {"message": "Not Found"})

    monkeypatch.setattr(gm_module, "Github", MissingTargetGithub)
    for name in ("CLI_CONFIG_PATH", "DOTENV_FILE", "GITHUB_TOKEN", "GITHUB_API_URL", "CHECK_INTERNET_URL", "CLEAR_SCREEN", "LOCAL_TIMEZONE", "DISABLE_LOGGING", "VERBOSE_MODE", "DEBUG_MODE", "WEBHOOK_URL", "WEBHOOK_ENABLED", "SECRET_SOURCES"):
        monkeypatch.setattr(gm_module, name, getattr(gm_module, name))
    for name in gm_module.SECRET_KEYS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(gm_module.req, "get", Mock(return_value=FakeResponse(200)))
    monkeypatch.setattr(gm_module.signal, "signal", lambda *args: None)
    monkeypatch.setattr(gm_module.sys, "argv", ["github_monitor", "missing-user", "--config-file", str(config), "--env-file", "none", "--debug"] + extra_args + ["--list-repos"])

    with pytest.raises(SystemExit):
        gm_module.main()

    output = capsys.readouterr().out
    traced = [line.split("name=")[1].split(",")[0] for line in output.splitlines() if "Secret resolution: name=" in line]
    assert traced == expected
    for name in expected:
        assert f"Secret resolution: name={name}, source=command line, value=set" in output
    assert "Secret resolution name=" not in output
    assert "No private settings were resolved" not in output
    assert "github_pat_command_line_secret" not in output


# The command line is the last layer to supply a secret, so a run with none says so only after it has had its say
def test_a_run_with_no_secret_anywhere_says_so(gm_module, monkeypatch, capsys, request):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config = Path(directory.name) / "github_monitor.conf"
    config.write_text('GITHUB_API_URL = "https://api.example.test"\nCHECK_INTERNET_URL = GITHUB_API_URL\nCLEAR_SCREEN = False\nLOCAL_TIMEZONE = "UTC"\nDISABLE_LOGGING = True\n', encoding="utf-8")

    class MissingTargetGithub:
        # Accepts the real client constructor settings without making a network call
        def __init__(self, *args, **kwargs):
            pass

        # Raises the same exception as GitHub for a missing user
        def get_user(self, login=None):
            raise gm_module.UnknownObjectException(404, {"message": "Not Found"})

    monkeypatch.setattr(gm_module, "Github", MissingTargetGithub)
    for name in ("CLI_CONFIG_PATH", "DOTENV_FILE", "GITHUB_TOKEN", "GITHUB_API_URL", "CHECK_INTERNET_URL", "CLEAR_SCREEN", "LOCAL_TIMEZONE", "DISABLE_LOGGING", "VERBOSE_MODE", "DEBUG_MODE", "WEBHOOK_URL", "WEBHOOK_ENABLED", "SECRET_SOURCES"):
        monkeypatch.setattr(gm_module, name, getattr(gm_module, name))
    for name in gm_module.SECRET_KEYS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(gm_module.req, "get", Mock(return_value=FakeResponse(200)))
    monkeypatch.setattr(gm_module.signal, "signal", lambda *args: None)
    monkeypatch.setattr(gm_module.sys, "argv", ["github_monitor", "missing-user", "--config-file", str(config), "--env-file", "none", "--debug", "--list-repos"])

    with pytest.raises(SystemExit):
        gm_module.main()

    output = capsys.readouterr().out
    assert "Secret resolution:" not in output
    assert "No private settings were resolved from config, dotenv, environment or the command line" in output


# The rows shared with the sibling monitors, in the order every one of them prints
SHARED_ROW_ORDER = ("Target", "Polling interval", "Notifications (email)", "Email transport", "Email recipient", "Notifications (webhook)", "Webhook provider", "Delivery confirmations", "Output", "Output logging", "Config", "Dotenv", "Liveness output", "CSV output", "Terminal truncation", "Process id", "Python version", "Operating system", "Local timezone", "Install method", "Secrets from dotenv", "Secrets from environment", "Secrets from config file", "Secrets from command line", "TLS verification", "ASCII log separators", "Coloured output", "Verbose mode", "Debug mode", "More details")


# Verifies the shared rows keep the order and the label column width every sibling monitor prints
def test_the_shared_summary_rows_match_the_sibling_tools(gm_module):
    rows = gm_module.build_startup_summary("octocat", "github_monitor.conf", ".env", "github_monitor_octocat.log")

    assert [row.label for row in rows if row.label in SHARED_ROW_ORDER] == list(SHARED_ROW_ORDER)
    # The renderer pads "<label>:" into a 30-character column, so a longer label swallows the separating space
    assert max(len(row.label) for row in rows) <= 28


# Verifies only debug keeps the screen, since a cleared terminal loses the run being compared against
@pytest.mark.parametrize(("flag", "expected"), (("--debug", False), ("--verbose", True)))
def test_only_debug_mode_keeps_the_screen(gm_module, monkeypatch, request, restored_globals, flag, expected):
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config = Path(directory.name) / "github_monitor.conf"
    config.write_text('CLEAR_SCREEN = True\nDISABLE_LOGGING = True\nGITHUB_TOKEN = "test-token-value"\n', encoding="utf-8")
    cleared = []
    monkeypatch.setattr(gm_module, "clear_screen", lambda enabled=True: cleared.append(bool(enabled)))
    monkeypatch.setattr(gm_module, "CLEAR_SCREEN", True)
    monkeypatch.setattr(gm_module, "DEBUG_MODE", False)
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", False)
    monkeypatch.setattr(gm_module.sys.stdout, "isatty", lambda: True, raising=False)
    monkeypatch.setattr(gm_module, "check_internet", lambda *args, **kwargs: True)
    monkeypatch.setattr(gm_module.signal, "signal", lambda *args: None)
    monkeypatch.setattr(gm_module, "github_monitor_user", Mock(side_effect=SystemExit(0)))
    monkeypatch.setattr(gm_module.sys, "argv", ["github_monitor", "misiektoja", "--config-file", str(config), "--env-file", "none", flag])

    with pytest.raises(SystemExit):
        gm_module.main()

    assert cleared == [expected]


# Verifies the one-shot commands keep whatever is already on the screen, so their output stays scrollable
@pytest.mark.parametrize(("argv", "expected"), ((["github_monitor", "--doctor"], True), (["github_monitor", "--set-github-token"], True), (["github_monitor", "--send-test-email"], True), (["github_monitor", "--help"], True), (["github_monitor", "misiektoja"], False)))
def test_one_shot_commands_keep_the_terminal_history(gm_module, monkeypatch, argv, expected):
    monkeypatch.setattr(gm_module.sys, "argv", argv)

    assert gm_module.keep_terminal_history() is expected


# Verifies a redirected stdout is never cleared, so no escape sequence or TERM warning reaches the captured output
def test_a_redirected_stdout_is_never_cleared(gm_module, monkeypatch):
    commands = []
    monkeypatch.setattr(gm_module.sys.stdout, "isatty", lambda: False, raising=False)
    monkeypatch.setattr(gm_module.os, "system", lambda command: commands.append(command))

    gm_module.clear_screen(True)

    assert commands == []


class FakeSMTP:
    # Accepts one message without contacting a server, so a delivery transcript can be read offline
    def __init__(self):
        self.sent = []

    # Records the message the caller handed over
    def sendmail(self, sender, recipient, message):
        self.sent.append((sender, recipient, message))

    # Ends the session the way a real one is ended
    def quit(self):
        return None


# Configures one usable SMTP destination for delivery transcript tests
def configure_smtp(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "SMTP_HOST", "smtp.example.test")
    monkeypatch.setattr(gm_module, "SMTP_PORT", 587)
    monkeypatch.setattr(gm_module, "SMTP_USER", "monitor@example.test")
    monkeypatch.setattr(gm_module, "SMTP_PASSWORD", "private-diagnostic-password")
    monkeypatch.setattr(gm_module, "SENDER_EMAIL", "monitor@example.test")
    monkeypatch.setattr(gm_module, "RECEIVER_EMAIL", "alerts@example.test")


# Verifies an email receipt names its recipient
def test_the_delivered_email_names_the_recipient(gm_module, monkeypatch, capsys):
    configure_smtp(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", True)
    monkeypatch.setattr(gm_module, "smtp_connect_and_login", lambda *args, **kwargs: FakeSMTP())

    assert gm_module.send_email("New release in misiektoja/github_monitor", "body", "", True) == 0

    assert "* Email sent to alerts@example.test" in capsys.readouterr().out


# Verifies DELIVERY_CONFIRMATIONS drops the delivery lines without turning the rest of verbose mode off
def test_delivery_confirmations_can_be_turned_off(gm_module, monkeypatch, capsys):
    configure_smtp(gm_module, monkeypatch)
    configure_webhook(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", True)
    monkeypatch.setattr(gm_module, "DELIVERY_CONFIRMATIONS", False)
    monkeypatch.setattr(gm_module, "smtp_connect_and_login", lambda *args, **kwargs: FakeSMTP())
    monkeypatch.setattr(gm_module.WEBHOOK_SESSION, "post", Mock(return_value=FakeResponse(204)))

    assert gm_module.send_email("New release in misiektoja/github_monitor", "body", "", True) == 0
    assert gm_module.send_webhook("Title", "Body", "profile", sleeper=lambda _seconds: None) == 0

    output = capsys.readouterr().out
    assert "Email sent to" not in output
    assert "Webhook sent through" not in output


# Verifies verbose does not report a failed delivery twice. It adds the triage fields every recovery block
# carries under verbose and nothing else, since a second description of the same failure would only repeat it
def test_a_failed_delivery_is_reported_once_with_verbose_on(gm_module, monkeypatch, capsys):
    configure_smtp(gm_module, monkeypatch)
    configure_webhook(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "smtp_connect_and_login", Mock(side_effect=OSError("the server refused the connection")))
    monkeypatch.setattr(gm_module.WEBHOOK_SESSION, "post", Mock(return_value=FakeResponse(404)))
    transcripts = {}

    for verbose in (False, True):
        monkeypatch.setattr(gm_module, "VERBOSE_MODE", verbose)
        assert gm_module.send_email("subject", "body", "", True) == 1
        assert gm_module.send_webhook("Title", "Body", "profile", sleeper=lambda seconds: None) == 1
        transcripts[verbose] = capsys.readouterr().out

    added = [line for line in transcripts[True].splitlines() if line not in transcripts[False].splitlines()]
    assert added == [], added
    for transcript in transcripts.values():
        assert transcript.count("* Error: ") == 2
        assert transcript.count("To fix: ") == 2


# Verifies an unusable SMTP setting names the fix and the guide, so no delivery path reports without saying what to do
def test_a_refused_smtp_setting_carries_the_shared_error_block(gm_module, monkeypatch, capsys):
    configure_smtp(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "SMTP_PORT", "not a port")

    assert gm_module.send_email("subject", "body", "", True) == 1

    output = capsys.readouterr().out
    assert "* Error: The SMTP settings are incorrect: SMTP_PORT is not a port number between 1 and 65535" in output
    assert "To fix: Check SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SENDER_EMAIL and RECEIVER_EMAIL then run: " in output
    assert f"Guide: {gm_module.SMTP_GUIDE_URL}" in output


# Verifies a mail server that refuses the session is reported with the fix rather than as a bare line
def test_a_refused_smtp_session_carries_the_shared_error_block(gm_module, monkeypatch, capsys):
    configure_smtp(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "smtp_connect_and_login", Mock(side_effect=OSError("the server refused the connection")))

    assert gm_module.send_email("subject", "body", "", True) == 1

    output = capsys.readouterr().out
    assert "* Error: The SMTP server could not be reached" in output
    assert f"Guide: {gm_module.SMTP_GUIDE_URL}" in output


@pytest.mark.parametrize("status, code, retryable", [(404, "webhook.rejected", False), (500, "webhook.rejected", True)])
# Verifies a refused delivery carries the fix, the guide and a retryable flag that follows the status
def test_a_refused_webhook_delivery_carries_the_shared_error_block(gm_module, monkeypatch, status, code, retryable):
    configure_webhook(gm_module, monkeypatch)

    advice = gm_module.webhook_failure_advice(f"The webhook service returned HTTP {status}", FakeResponse(status, text="the service said no"))

    assert advice.code == code
    assert advice.retryable is retryable
    assert advice.fix.endswith(f"\nGuide: {gm_module.WEBHOOK_GUIDE_URL}")
    assert advice.detail == "the service said no"


@pytest.mark.parametrize("message, code", [
    ("WEBHOOK_URL must contain a complete HTTPS link", "webhook.invalid"),
    ("WEBHOOK_PROVIDER must be discord or ntfy", "webhook.invalid"),
    ("The webhook service could not be reached (ConnectionError)", "webhook.connection"),
    ("The webhook delivery did not complete", "webhook.rejected"),
])
# Verifies each webhook failure reaches its own code rather than one catch-all the taxonomy cannot distinguish
def test_each_webhook_failure_reaches_its_own_code(gm_module, message, code):
    assert gm_module.webhook_failure_advice(message).code == code


# Verifies no delivery path prints at all, since a print there is an error line that skipped the recovery block
def test_no_delivery_path_prints_outside_the_recovery_block(gm_module):
    delivery = {"send_email", "send_webhook", "print_webhook_error", "smtp_connect_and_login", "post_webhook_request"}
    offenders = []
    for node in ast.walk(ast.parse(Path(gm_module.__file__).read_text(encoding="utf-8"))):
        if not isinstance(node, ast.FunctionDef) or node.name not in delivery:
            continue
        offenders.extend(f"{node.name}:{call.lineno}" for call in ast.walk(node) if isinstance(call, ast.Call) and getattr(call.func, "id", "") == "print")

    assert not offenders, "delivery paths printing outside the recovery block: " + ", ".join(offenders)


# Collects every debug trace in the module as an operation name mapped to the field sets its call sites pass
def traced_operations(module):
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    traced = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "debug_print" and node.args and isinstance(node.args[0], ast.Constant):
            traced.setdefault(node.args[0].value, []).append({keyword.arg for keyword in node.keywords})
    return traced


# Verifies both ends of a monitoring check report a result, since a trace that records only the healthy ones
# makes a failing run look like a hung one. The loop has no offline driver, so this reads the call sites
def test_both_ends_of_a_monitoring_check_report_a_result(gm_module):
    completed = traced_operations(gm_module).get("Completed monitoring check", [])

    assert len(completed) == 2, "a monitoring check ends on two paths, and each one reports how it went"
    assert all("outcome" in fields for fields in completed), "a completed check is traced without saying how it went"
    assert any({"code", "error"} <= fields for fields in completed), "the failing path names neither the category nor the error"


# Verifies every scheduled wait says how long it is and what it is waiting for, since a measured pause with no
# reason explains nothing about why the run is idle
def test_every_wait_says_how_long_it_is_and_why(gm_module):
    waits = traced_operations(gm_module).get("Waiting", [])

    assert waits, "no wait is traced at all"
    assert all({"interval", "reason"} <= fields for fields in waits), "a wait is traced without its length or its reason"
