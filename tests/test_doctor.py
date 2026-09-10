"""Offline contract tests for the comprehensive doctor preflight."""

import inspect
import io
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = PROJECT_ROOT / "local" / "doctor_test_artifacts"


# Creates one disposable doctor directory under the project local directory
def make_test_directory():
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=ARTIFACT_ROOT)


# Builds the complete argument namespace consumed by doctor configuration
def doctor_args(**overrides):
    values = {
        "username": "octocat",
        "config_file": None,
        "env_file": "none",
        "github_token": None,
        "github_url": None,
        "webhook_provider": None,
        "webhook_url": None,
        "webhook_enabled": None,
        "webhook_profile": None,
        "webhook_events": None,
        "webhook_repo_changes": None,
        "webhook_repo_update_date": None,
        "webhook_daily_contribs": None,
        "webhook_errors": None,
        "check_interval": None,
        "csv_file": None,
        "disable_logging": None,
        "notify_profile": None,
        "notify_events": None,
        "notify_repo_changes": None,
        "notify_repo_update_date": None,
        "notify_daily_contribs": None,
        "notify_errors": None,
        "track_repos_changes": None,
        "repos": None,
        "track_contribs_changes": None,
        "no_monitor_events": None,
        "get_all_repos": None,
        "verbose": None,
        "debug": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class FakeResponse:
    # Stores one deterministic HTTP status and authenticated login
    def __init__(self, status_code=200, login="doctor-user"):
        self.status_code = status_code
        self.login = login

    # Returns the token-validation response body
    def json(self):
        return {"login": self.login}


class FakeProfile:
    login = "octocat"

    # Returns an empty accessible repository feed
    def get_repos(self, **kwargs):
        return []

    # Returns an empty accessible starred repository feed
    def get_starred(self):
        return []

    # Returns an empty accessible event feed
    def get_events(self):
        return []


class FakeGithub:
    # Stores a reusable target profile for all doctor lookups
    def __init__(self, *args, **kwargs):
        self.profile = FakeProfile()

    # Returns the accessible test target
    def get_user(self, username):
        return self.profile


class FakeTTY(io.StringIO):
    # Reports an interactive terminal while retaining written transcript data
    def isatty(self):
        return True


# Resets every effective setting consumed by doctor to a healthy offline baseline
def configure_healthy_doctor(gm_module, monkeypatch):
    settings = {
        "CLI_CONFIG_PATH": None,
        "DOTENV_FILE": "",
        "SECRET_SOURCES": {},
        "GITHUB_TOKEN": "github_pat_doctor_private_token",
        "TARGET_GITHUB_USERNAME": "",
        "GITHUB_API_URL": "https://api.example.test",
        "GITHUB_HTML_URL": "https://github.example.test",
        "CHECK_INTERNET_URL": "https://api.example.test",
        "CHECK_INTERNET_TIMEOUT": 4,
        "LOCAL_TIMEZONE": "UTC",
        "GITHUB_CHECK_INTERVAL": 60,
        "EVENTS_NUMBER": 30,
        "EVENTS_TO_MONITOR": ["ALL"],
        "NET_MAX_RETRIES": 5,
        "NET_BASE_BACKOFF_SEC": 1,
        "ASCII_LOG_SEPARATORS": "Auto",
        "CSV_FILE": "",
        "DISABLE_LOGGING": True,
        "GITHUB_LOGFILE": "github_monitor",
        "PROFILE_NOTIFICATION": False,
        "EVENT_NOTIFICATION": False,
        "REPO_NOTIFICATION": False,
        "REPO_UPDATE_DATE_NOTIFICATION": False,
        "CONTRIB_NOTIFICATION": False,
        "ERROR_NOTIFICATION": False,
        "SMTP_HOST": "your_smtp_server_ssl",
        "SMTP_PORT": 587,
        "SMTP_USER": "your_smtp_user",
        "SMTP_PASSWORD": "your_smtp_password",
        "SENDER_EMAIL": "your_sender_email",
        "RECEIVER_EMAIL": "your_receiver_email",
        "WEBHOOK_ENABLED": False,
        "WEBHOOK_PROVIDER": "discord",
        "WEBHOOK_URL": "your_webhook_url",
        "WEBHOOK_PROFILE_NOTIFICATION": False,
        "WEBHOOK_EVENT_NOTIFICATION": False,
        "WEBHOOK_REPO_NOTIFICATION": False,
        "WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION": False,
        "WEBHOOK_CONTRIB_NOTIFICATION": False,
        "WEBHOOK_ERROR_NOTIFICATION": False,
        "WEBHOOK_HEADERS": {},
        "WEBHOOK_TRANSFORMS": [],
        "NTFY_ACCESS_TOKEN": "",
        "TRACK_REPOS_CHANGES": False,
        "REPOS_TO_MONITOR": ["ALL"],
        "TRACK_CONTRIB_CHANGES": False,
        "DO_NOT_MONITOR_GITHUB_EVENTS": False,
        "GET_ALL_REPOS": False,
        "LIVENESS_CHECK_INTERVAL": 0,
    }
    for name, value in settings.items():
        monkeypatch.setattr(gm_module, name, value)
    monkeypatch.setattr(gm_module, "find_config_file", lambda path=None: None)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.delenv("WEBHOOK_URL", raising=False)
    monkeypatch.delenv("NTFY_ACCESS_TOKEN", raising=False)


# Returns a successful response for every bounded doctor request
def successful_request(*args, **kwargs):
    return FakeResponse()


# Verifies a complete healthy transcript follows the fixed section and verdict contract
def test_doctor_healthy_transcript_is_complete(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    output = io.StringIO()

    result = gm_module.run_doctor(doctor_args(), Mock(), request_get=successful_request, github_factory=FakeGithub, module_finder=lambda name: object(), stream=output)

    transcript = output.getvalue()
    assert result == 0
    assert transcript.startswith(gm_module.STARTUP_BANNER + f"\n                     v{gm_module.VERSION}\n\nRunning preflight checks. No files will be written. Interactive email and webhook tests run only after separate approval.\n\nDoctor\n")
    sections = [transcript.index(f"\n{name}\n") for name in ("Environment", "Configuration", "Authentication", "Connectivity", "Target", "Monitoring", "Notifications", "Summary")]
    assert sections == sorted(sections)
    assert "[PASS] GitHub token was accepted" in transcript
    assert "[PASS] Required dependency urllib3 is installed" in transcript
    assert "[PASS] GitHub target is accessible" in transcript
    assert "[PASS] Repository feed is accessible" in transcript
    assert "[PASS] Email notifications are disabled" in transcript
    assert "[PASS] Webhook alerts are disabled" in transcript
    assert "  All checks passed. You are good to go!" in transcript
    assert "[WARN]" not in transcript
    assert "[FAIL]" not in transcript
    assert "github_pat_doctor_private_token" not in transcript
    assert "\n\n\n" not in transcript
    markers = {line.split("]", 1)[0] + "]" for line in transcript.splitlines() if line.startswith("[")}
    assert markers == {"[PASS]"}


# Verifies the install method is stated as context instead of a check that can never fail
def test_doctor_reports_the_install_method_without_a_marker(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    output = io.StringIO()

    gm_module.run_doctor(doctor_args(), Mock(), request_get=successful_request, github_factory=FakeGithub, module_finder=lambda name: object(), stream=output)

    transcript = output.getvalue()
    method = gm_module.detect_install_context().install_method
    assert f"\nDoctor\nDetected install method: {method}\n" in transcript
    assert "[PASS] Install method" not in transcript


# Verifies missing setup produces all useful failures in one report and exits unhealthy
def test_doctor_reports_missing_authentication_and_target(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", "")
    output = io.StringIO()

    result = gm_module.run_doctor(doctor_args(username=None), Mock(), request_get=successful_request, github_factory=FakeGithub, module_finder=lambda name: object(), stream=output)

    transcript = output.getvalue()
    assert result == 1
    assert "[FAIL] GitHub token is missing" in transcript
    assert "[WARN] No GitHub target was provided" in transcript
    assert transcript.count("[WARN]") == 1
    assert "To fix:" in transcript
    assert "Guide:" in transcript
    assert "Fix the failures above before relying on the tool." in transcript


# Verifies Doctor uses the saved target when no positional target is supplied
def test_doctor_uses_saved_target(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "TARGET_GITHUB_USERNAME", "octocat")
    output = io.StringIO()

    result = gm_module.run_doctor(doctor_args(username=None), Mock(), request_get=successful_request, github_factory=FakeGithub, module_finder=lambda name: object(), stream=output)

    transcript = output.getvalue()
    assert result == 0
    assert "[PASS] GitHub target is accessible" in transcript
    assert "[WARN] No GitHub target was provided" not in transcript


# Verifies network failure is visible in authentication and connectivity checks
def test_doctor_offline_transcript_names_failed_paths(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    output = io.StringIO()

    def offline_request(*args, **kwargs):
        raise gm_module.req.ConnectionError("offline for doctor")

    result = gm_module.run_doctor(doctor_args(), Mock(), request_get=offline_request, github_factory=FakeGithub, module_finder=lambda name: object(), stream=output)

    transcript = output.getvalue()
    assert result == 1
    assert "[FAIL] GitHub token validation failed" in transcript
    assert "[FAIL] The connectivity endpoint could not be reached" in transcript
    assert f"Endpoint: {gm_module.diagnostic_endpoint(gm_module.CHECK_INTERNET_URL)}" in transcript
    assert "[SKIP] The monitored profile was not checked" in transcript
    assert "could not be checked" not in transcript


# Verifies required and optional dependency failures use different health states
def test_doctor_environment_distinguishes_required_and_optional_dependencies(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module.platform, "system", lambda: "Linux")
    report = gm_module.DoctorReport()

    gm_module.doctor_check_environment(report, lambda name: None if name in {"github", "tzlocal"} else object())

    rows = {(check.status, check.label) for check in report.checks}
    assert ("FAIL", "Required dependency PyGithub is missing") in rows
    assert ("WARN", "Optional dependency tzlocal is not installed") in rows
    assert not any(check.label.startswith("Install method") for check in report.checks)
    assert report.failure_count == 1
    assert report.warning_count == 1


# Verifies a warning about a library that cannot affect this machine is not shown at all
@pytest.mark.parametrize("system, reported", [("Windows", True), ("Linux", False), ("Darwin", False)])
def test_a_platform_specific_dependency_is_only_reported_where_it_applies(gm_module, monkeypatch, system, reported):
    configure_healthy_doctor(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module.platform, "system", lambda: system)
    report = gm_module.DoctorReport()

    gm_module.doctor_check_environment(report, lambda name: None)

    assert any("colorama" in check.label for check in report.checks) is reported


# Verifies the Windows colour library is reported there, so broken colours on that platform have a diagnostic
def test_missing_colorama_is_reported_on_windows(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module.platform, "system", lambda: "Windows")
    report = gm_module.DoctorReport()

    gm_module.doctor_check_environment(report, lambda name: None if name == "colorama" else object())

    missing = next(check for check in report.checks if "colorama" in check.label)
    assert missing.status == "WARN"
    assert missing.detail == "Coloured output in the classic Windows Command Prompt will not work. Every other feature is unaffected"
    assert "-m pip install colorama" in missing.fix


# Verifies the bootstrap report scopes the same library to the platform it applies to
@pytest.mark.parametrize("system, reported", [("Windows", True), ("Linux", False)])
def test_bootstrap_scopes_the_platform_specific_dependency(gm_module, monkeypatch, system, reported):
    monkeypatch.setattr(gm_module.platform, "system", lambda: system)
    output = io.StringIO()

    gm_module.bootstrap_doctor_dependency_report(lambda name: None if name in {"requests", "colorama"} else object(), output)

    assert ("Optional dependency colorama is not installed" in output.getvalue()) is reported


# Verifies doctor still reports a missing required import before full module startup
def test_doctor_bootstrap_reports_missing_required_dependency(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module.platform, "system", lambda: "Linux")
    output = io.StringIO()

    result = gm_module.bootstrap_doctor_dependency_report(lambda name: None if name in {"requests", "tzlocal"} else object(), output)

    transcript = output.getvalue()
    assert result == 1
    assert transcript.startswith(gm_module.STARTUP_BANNER + f"\n                     v{gm_module.VERSION}\n\nRunning preflight checks.")
    assert "[FAIL] Required dependency requests is missing" in transcript
    assert "[WARN] Optional dependency tzlocal is not installed" in transcript
    assert "To fix: Install it with:" in transcript
    assert "1 check(s) failed, 1 warning(s)." in transcript


# Verifies unsupported Python gets the same actionable doctor contract before imports
def test_doctor_bootstrap_reports_unsupported_python(gm_module, monkeypatch):
    output = io.StringIO()
    monkeypatch.setattr(gm_module.sys, "version_info", (3, 9, 18))

    result = gm_module.bootstrap_doctor_python_report(output)

    transcript = output.getvalue()
    assert result == 1
    assert "[FAIL] Python 3.9.18 is unsupported" in transcript
    assert f"  Minimum supported version: {gm_module.MINIMUM_PYTHON_VERSION_TEXT}" in transcript
    assert f"To fix: Install Python {gm_module.MINIMUM_PYTHON_VERSION_TEXT} or newer" in transcript
    assert "1 check(s) failed, 0 warning(s)." in transcript


# Verifies configuration source rows expose names and paths without private values
def test_doctor_configuration_reports_secret_sources_without_values(gm_module, monkeypatch, request):
    configure_healthy_doctor(gm_module, monkeypatch)
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config = Path(directory.name) / "github_monitor.conf"
    dotenv = Path(directory.name) / ".env"
    config.write_text('GITHUB_TOKEN = "github_pat_config_doctor_secret"\nLOCAL_TIMEZONE = "UTC"\n', encoding="utf-8")
    dotenv.write_text('WEBHOOK_URL="https://ntfy.sh/private-doctor-topic"\n', encoding="utf-8")
    monkeypatch.setattr(gm_module, "find_config_file", lambda path=None: str(config))
    report = gm_module.DoctorReport(target_name="octocat")

    gm_module.doctor_check_configuration(report, doctor_args(config_file=str(config), env_file=str(dotenv)), Mock())

    rendered = io.StringIO()
    gm_module.render_doctor_sections(report, rendered)
    transcript = rendered.getvalue()
    assert "[PASS] Configuration file loaded" in transcript
    assert f"Path: {config}" in transcript
    assert "[PASS] Dotenv file loaded" in transcript
    assert "Secrets loaded from the dotenv file\n  WEBHOOK_URL" in transcript
    assert "Secrets loaded from the configuration file\n  GITHUB_TOKEN" in transcript
    assert "github_pat_config_doctor_secret" not in transcript
    assert "private-doctor-topic" not in transcript


# Verifies invalid CLI combinations become report rows instead of aborting doctor
def test_doctor_reports_repository_selection_without_tracking(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    report = gm_module.DoctorReport(target_name="octocat")

    gm_module.doctor_check_configuration(report, doctor_args(repos="one,two"), Mock())

    check = next(check for check in report.checks if check.label == "Repository selection cannot take effect")
    assert check.status == "FAIL"
    assert "--track-repos-changes" in check.fix


# Verifies invalid timing, retry and event settings are diagnosed before runtime
def test_doctor_reports_invalid_runtime_configuration(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "GITHUB_CHECK_INTERVAL", 0)
    monkeypatch.setattr(gm_module, "CHECK_INTERNET_TIMEOUT", -1)
    monkeypatch.setattr(gm_module, "EVENTS_NUMBER", 0)
    monkeypatch.setattr(gm_module, "NET_MAX_RETRIES", 0)
    monkeypatch.setattr(gm_module, "EVENTS_TO_MONITOR", [])
    report = gm_module.DoctorReport(target_name="octocat")

    gm_module.doctor_check_configuration(report, doctor_args(), Mock())

    failed = {check.label: check.detail for check in report.checks if check.status == "FAIL"}
    assert {"One or more numeric settings are invalid", "Event type selection is invalid"} <= set(failed)
    # Every invalid setting is named in the one row, so a run does not have to be repeated to find the next one
    assert all(name in failed["One or more numeric settings are invalid"] for name in ("GITHUB_CHECK_INTERVAL", "CHECK_INTERNET_TIMEOUT", "EVENTS_NUMBER", "NET_MAX_RETRIES"))


# Verifies an invalid config becomes one row while later checks still run
def test_doctor_keeps_checking_after_invalid_configuration_file(gm_module, monkeypatch, request):
    configure_healthy_doctor(gm_module, monkeypatch)
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config = Path(directory.name) / "invalid.conf"
    config.write_text("import os\n", encoding="utf-8")
    monkeypatch.setattr(gm_module, "find_config_file", lambda path=None: str(config))
    report = gm_module.DoctorReport(target_name="octocat")

    gm_module.doctor_check_configuration(report, doctor_args(config_file=str(config)), Mock())

    assert any(check.status == "FAIL" and check.label == "Configuration file could not be loaded" for check in report.checks)
    assert any(check.label == "TLS certificate verification is on" for check in report.checks)


# Verifies doctor only inspects output paths and does not create configured files or directories
def test_doctor_output_path_checks_are_read_only(gm_module, monkeypatch, request):
    configure_healthy_doctor(gm_module, monkeypatch)
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    nested = Path(directory.name) / "not-created"
    csv_path = nested / "events.csv"
    log_path = nested / "monitor"
    monkeypatch.setattr(gm_module, "CSV_FILE", str(csv_path))
    monkeypatch.setattr(gm_module, "DISABLE_LOGGING", False)
    monkeypatch.setattr(gm_module, "GITHUB_LOGFILE", str(log_path))
    report = gm_module.DoctorReport(target_name="octocat", target_profile=FakeProfile(), github_token="token")

    gm_module.doctor_check_output_paths(report)

    assert not nested.exists()
    assert not csv_path.exists()
    assert not Path(f"{log_path}_octocat.log").exists()
    rows = {(check.section, check.label) for check in report.checks}
    assert ("Configuration", "CSV destination appears writable") in rows
    assert ("Configuration", "Log destination appears writable") in rows


# Verifies the log destination waits for a target because the file name carries it
def test_doctor_defers_the_log_destination_without_a_target(gm_module, monkeypatch, request):
    configure_healthy_doctor(gm_module, monkeypatch)
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    monkeypatch.setattr(gm_module, "CSV_FILE", "")
    monkeypatch.setattr(gm_module, "DISABLE_LOGGING", False)
    monkeypatch.setattr(gm_module, "GITHUB_LOGFILE", str(Path(directory.name) / "monitor"))
    report = gm_module.DoctorReport()

    gm_module.doctor_check_output_paths(report)

    rows = {(check.status, check.label) for check in report.checks}
    assert ("PASS", "Log destination will be finalized after a target is selected") in rows
    assert ("PASS", "CSV logging is disabled") in rows


# Verifies notification readiness follows enabled state before validating destinations
def test_doctor_notification_checks_gate_disabled_and_invalid_channels(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    disabled = gm_module.DoctorReport()
    gm_module.doctor_check_notifications(disabled)
    assert [check.label for check in disabled.checks] == ["Email notifications are disabled", "Webhook alerts are disabled"]
    # The webhook label says everything, so the row carries no detail that only repeats it
    assert [check.detail for check in disabled.checks] == ["No SMTP connection was attempted and no email was sent", ""]
    monkeypatch.setattr(gm_module, "PROFILE_NOTIFICATION", True)
    monkeypatch.setattr(gm_module, "WEBHOOK_ENABLED", True)
    monkeypatch.setattr(gm_module, "WEBHOOK_PROFILE_NOTIFICATION", True)
    invalid = gm_module.DoctorReport()

    gm_module.doctor_check_notifications(invalid)

    assert [check.status for check in invalid.checks] == ["WARN", "FAIL"]
    assert invalid.email_ready is False
    assert invalid.webhook_ready is False


# Verifies each ready channel receives its own approval and declined tests use SKIP
def test_doctor_optional_delivery_tests_require_separate_approval(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "RECEIVER_EMAIL", "alerts@example.test")
    monkeypatch.setattr(gm_module, "WEBHOOK_URL", "https://discord.com/api/webhooks/123/private-doctor-token")
    report = gm_module.DoctorReport(email_ready=True, webhook_ready=True)
    answers = iter(["yes", "no"])
    output = FakeTTY()
    email_sender = Mock(return_value=0)
    webhook_sender = Mock(return_value=0)

    gm_module.doctor_run_optional_delivery_tests(report, lambda: next(answers), FakeTTY(), output, email_sender, webhook_sender)

    transcript = output.getvalue()
    assert "Send one test email now? This will deliver a real message [y/N]: " in transcript
    assert "[PASS] Doctor test email delivered" in transcript
    assert "Send one test webhook through Discord now? This will publish a real notification [y/N]: " in transcript
    assert "[SKIP] Test webhook through Discord was not sent" in transcript
    # The detail and fix lines carry the sentences the sibling tools print on one detail line
    assert "  One real test email was sent after confirmation" in transcript
    assert "  You declined the real delivery test" in transcript
    assert "Run doctor again and approve the webhook test when ready" in transcript
    assert email_sender.call_count == 1
    assert webhook_sender.call_count == 0
    assert report.failure_count == 0


# Verifies non-interactive doctor runs never send or prompt for real messages
def test_doctor_non_interactive_run_stays_message_free(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    report = gm_module.DoctorReport(email_ready=True, webhook_ready=True)
    output = io.StringIO()
    email_sender = Mock(return_value=0)
    webhook_sender = Mock(return_value=0)

    gm_module.doctor_run_optional_delivery_tests(report, lambda: "yes", io.StringIO(), output, email_sender, webhook_sender)

    assert output.getvalue() == ""
    assert email_sender.call_count == 0
    assert webhook_sender.call_count == 0
    assert report.checks == []
    gm_module.doctor_run_optional_delivery_tests(report, lambda: "yes", FakeTTY(), output, email_sender, webhook_sender)
    assert output.getvalue() == ""
    assert email_sender.call_count == 0
    assert webhook_sender.call_count == 0


# Verifies the explicit none sentinel disables Doctor configuration discovery
def test_doctor_configuration_honours_disabled_discovery(gm_module, monkeypatch):
    report = gm_module.DoctorReport()
    args = doctor_args(config_file="none")
    finder = Mock(side_effect=AssertionError("configuration discovery must stay disabled"))
    monkeypatch.setattr(gm_module, "find_config_file", finder)
    monkeypatch.setattr(gm_module, "load_startup_secrets", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(gm_module, "apply_startup_cli_overrides", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(gm_module, "apply_webhook_cli_overrides", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(gm_module, "apply_monitoring_cli_overrides", lambda *_args, **_kwargs: None)

    gm_module.doctor_check_configuration(report, args, Mock())

    assert finder.call_count == 0
    assert any(check.label == "No configuration file selected" and check.detail == "Using built-in defaults and command-line overrides" and check.status == "PASS" for check in report.checks)


# Verifies approved delivery failure changes the final healthcheck exit state
def test_doctor_approved_delivery_failure_is_unhealthy(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    report = gm_module.DoctorReport(email_ready=True)
    output = FakeTTY()

    gm_module.doctor_run_optional_delivery_tests(report, lambda: "yes", FakeTTY(), output, Mock(return_value=1), None)

    assert report.failure_count == 1
    assert "[FAIL] Doctor test email delivery failed" in output.getvalue()
    assert "  The approved test email could not be delivered" in output.getvalue()
    assert "Review the SMTP error above" in output.getvalue()


# Verifies transient cursor output appears only for a TTY and is erased cleanly
def test_doctor_progress_is_tty_only(gm_module):
    terminal = FakeTTY()
    progress = gm_module.DoctorProgress(terminal)
    progress.show("authentication")
    progress.clear()
    assert terminal.getvalue() == "* Checking authentication ...\r" + " " * len("* Checking authentication ...") + "\r"
    piped = io.StringIO()
    progress = gm_module.DoctorProgress(piped)
    progress.show("authentication")
    progress.clear()
    assert piped.getvalue() == ""


# Verifies every non-pass transcript row carries an action plus a link only when the row has a page of its own
def test_doctor_non_pass_rows_always_render_a_fix(gm_module):
    report = gm_module.DoctorReport()
    report.add("Configuration", "WARN", "Warning row", "warning detail", "correct warning")
    report.add("Authentication", "FAIL", "Failure row", "failure detail", "correct failure", gm_module.AUTH_GUIDE_URL)
    report.add("Optional delivery tests", "SKIP", "Skipped row", "declined", "approve later")
    output = io.StringIO()

    for check in report.checks:
        gm_module.print_doctor_check(check, stream=output)

    transcript = output.getvalue()
    assert transcript.count("To fix:") == 3
    # The closing summary already links the doctor page, so only the row with its own page repeats a link
    assert transcript.count("Guide:") == 1
    assert gm_module.AUTH_GUIDE_URL in transcript
    assert {check.status for check in report.checks} == {"WARN", "FAIL", "SKIP"}


# Verifies the support loop asks bug reporters for the complete doctor transcript
def test_bug_report_collects_doctor_output():
    issue_template = (PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").read_text(encoding="utf-8")
    support = (PROJECT_ROOT / "SUPPORT.md").read_text(encoding="utf-8")
    assert "id: doctor-output" in issue_template
    assert "github_monitor --doctor <github_target>" in issue_template
    assert "complete sanitized output" in issue_template
    assert "## Doctor preflight" in support


# Drives --doctor through main and verifies it exits without entering monitoring
def test_doctor_cli_path_runs_preflight_and_exits(gm_module, monkeypatch, capsys):
    configure_healthy_doctor(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module.req, "get", successful_request)
    monkeypatch.setattr(gm_module, "Github", FakeGithub)
    monkeypatch.setattr(gm_module.signal, "signal", lambda *args: None)
    monkeypatch.setattr(gm_module.sys, "argv", ["github_monitor", "octocat", "--env-file", "none", "--doctor"])
    monitor = Mock()
    monkeypatch.setattr(gm_module, "github_monitor_user", monitor)

    with pytest.raises(SystemExit) as exit_error:
        gm_module.main()

    assert exit_error.value.code == 0
    transcript = capsys.readouterr().out
    assert "Running preflight checks. No files will be written." in transcript
    assert "[PASS] GitHub target is accessible" in transcript
    assert "All checks passed. You are good to go!" in transcript
    assert monitor.call_count == 0


# Verifies doctor rejects file-generating actions before any destination is written
def test_doctor_cannot_be_combined_with_generate_config(gm_module, monkeypatch, request):
    configure_healthy_doctor(gm_module, monkeypatch)
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    destination = Path(directory.name) / "must-not-exist.conf"
    monkeypatch.setattr(gm_module.signal, "signal", lambda *args: None)
    monkeypatch.setattr(gm_module.sys, "argv", ["github_monitor", "--doctor", "--generate-config", str(destination)])

    with pytest.raises(SystemExit) as exit_error:
        gm_module.main()

    assert exit_error.value.code == 2
    assert not destination.exists()


# Verifies the doctor surfaces a retired setting as a warning rather than failing the whole configuration
def test_doctor_warns_about_retired_configuration_settings(gm_module, monkeypatch, request):
    configure_healthy_doctor(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "RETIRED_CONFIG_SETTINGS", frozenset(("OBSOLETE_TEST_SETTING",)))
    directory = make_test_directory()
    request.addfinalizer(directory.cleanup)
    config = Path(directory.name) / "retired.conf"
    config.write_text('OBSOLETE_TEST_SETTING = "gone"\nLOCAL_TIMEZONE = "UTC"\n', encoding="utf-8")
    monkeypatch.setattr(gm_module, "find_config_file", lambda path=None: str(config))
    report = gm_module.DoctorReport(target_name="octocat")

    gm_module.doctor_check_configuration(report, doctor_args(config_file=str(config)), Mock())

    assert any(check.status == "PASS" and check.label == "Configuration file loaded" for check in report.checks)
    warning = next(check for check in report.checks if check.label == "Retired configuration settings were ignored")
    assert warning.status == "WARN" and "OBSOLETE_TEST_SETTING" in warning.detail


# Applies a complete email setup so the ready path can be reached without touching a real server
def configure_email(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "SMTP_HOST", "smtp.example.invalid")
    monkeypatch.setattr(gm_module, "SMTP_PORT", 587)
    monkeypatch.setattr(gm_module, "SMTP_SSL", True)
    monkeypatch.setattr(gm_module, "SMTP_USER", "monitor@example.invalid")
    monkeypatch.setattr(gm_module, "SMTP_PASSWORD", "app-password-placeholder")
    monkeypatch.setattr(gm_module, "SENDER_EMAIL", "monitor@example.invalid")
    monkeypatch.setattr(gm_module, "RECEIVER_EMAIL", "owner@example.invalid")
    monkeypatch.setattr(gm_module, "PROFILE_NOTIFICATION", True)


# Verifies the email ready row reports the sign-in and the selected alert categories
def test_the_email_ready_row_reports_the_sign_in_and_the_alerts(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    configure_email(gm_module, monkeypatch)
    closed = []
    monkeypatch.setattr(gm_module, "smtp_connect_and_login", lambda use_ssl, smtp_timeout=15: SimpleNamespace(quit=lambda: closed.append(True)))
    report = gm_module.DoctorReport()

    gm_module.doctor_check_notifications(report)

    email_check = report.checks[0]
    assert email_check.status == "PASS"
    assert email_check.label == gm_module.SMTP_READY_CHECK_LABEL
    assert email_check.detail == "Alerts: profile. No email was sent during this passive check"
    assert report.email_ready is True
    assert closed == [True]


# Verifies email alerts that cannot deliver are one WARN whose detail and action name the same settings
def test_unusable_email_settings_warn_and_name_the_same_settings(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    configure_email(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "SMTP_PASSWORD", "your_smtp_password")
    monkeypatch.setattr(gm_module, "smtp_connect_and_login", Mock(side_effect=AssertionError("SMTP was contacted")))
    report = gm_module.DoctorReport()

    gm_module.doctor_check_notifications(report)

    email_check = report.checks[0]
    assert email_check.status == "WARN"
    assert email_check.label == gm_module.EMAIL_UNUSABLE_CHECK_LABEL
    assert email_check.detail == "SMTP_USER or SMTP_PASSWORD is empty or still set to its placeholder"
    assert email_check.fix == "Set SMTP_USER and SMTP_PASSWORD or turn the email alerts off"
    assert email_check.guide == gm_module.SMTP_GUIDE_URL
    assert report.email_ready is False


# Verifies a rejected SMTP sign-in fails the check instead of reporting the channel as ready
def test_a_rejected_smtp_sign_in_fails_the_check(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    configure_email(gm_module, monkeypatch)

    # Raises the rejection the same way a live server would, so the classifier picks the SMTP branch
    def reject(use_ssl, smtp_timeout=15):
        raise gm_module.smtplib.SMTPAuthenticationError(535, b"authentication failed")

    monkeypatch.setattr(gm_module, "smtp_connect_and_login", reject)
    report = gm_module.DoctorReport()

    gm_module.doctor_check_notifications(report)

    email_check = report.checks[0]
    assert email_check.status == "FAIL"
    assert email_check.fix
    assert report.email_ready is False


# Verifies settings that are merely valid take no row, since a value that is fine is not a finding
def test_valid_settings_take_no_configuration_rows(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "TARGET_GITHUB_USERNAME", "octocat")
    report = gm_module.DoctorReport(target_name="octocat")

    gm_module.doctor_check_configuration(report, doctor_args(), Mock())

    labels = {check.label for check in report.checks}
    assert labels.isdisjoint({"GitHub API URL is valid", "GitHub web URL is valid", "Polling interval is valid", "Saved GitHub target is valid", "Connectivity timeout is valid", "Recent event window is valid", "GitHub retry policy is valid", "Liveness interval is valid", "Event type selection is valid", "Event type selection is not required", "Log separator mode is valid"})
    assert "Local timezone is valid" in labels
    assert ("Local timezone is valid", f"Time zone: {gm_module.LOCAL_TIMEZONE}") in {(check.label, check.detail) for check in report.checks}


# Verifies every doctor detail keeps to the agreed shapes: it never repeats its label, gives an instruction or joins values with a pipe
def test_doctor_details_keep_to_the_agreed_shapes(gm_module):
    import ast
    import inspect

    # Renders one detail argument as text, standing in {} for the parts an f-string fills at runtime
    def detail_text(node):
        if isinstance(node, ast.Constant):
            return node.value if isinstance(node.value, str) else None
        if isinstance(node, ast.JoinedStr):
            return "".join(part.value if isinstance(part, ast.Constant) else "{}" for part in node.values)
        return None

    offenders = []
    for node in ast.walk(ast.parse(inspect.getsource(gm_module))):
        if not isinstance(node, ast.Call) or ast.unparse(node.func) not in {"make_doctor_check", "report.add"} or len(node.args) < 4:
            continue
        label, text = node.args[2], detail_text(node.args[3])
        if text is None:
            continue
        if isinstance(label, ast.Constant) and text == label.value:
            offenders.append(f"{node.lineno}: the detail repeats its label")
        if text.startswith(("Use ", "Set ", "Run ")):
            offenders.append(f"{node.lineno}: the detail gives an instruction, which belongs in the fix line")
        if " | " in text:
            offenders.append(f"{node.lineno}: the detail joins two values with a pipe")
        if text.endswith("."):
            offenders.append(f"{node.lineno}: the detail ends with a full stop")

    assert not offenders, "doctor details outside the agreed shapes:\n" + "\n".join(offenders)


# Verifies the constructor drops a detail that only repeats its label, so no row says the same thing twice
def test_a_detail_that_repeats_its_label_is_dropped(gm_module):
    report = gm_module.DoctorReport()

    check = report.add("Configuration", "PASS", "Output logging is disabled", "Output logging is disabled")

    assert check.detail == ""
    assert report.checks == [check]


# Verifies a row the user has to act on cannot reach the report without an action
def test_an_actionable_row_is_rejected_without_a_fix(gm_module):
    report = gm_module.DoctorReport()
    for status in ("WARN", "FAIL"):
        with pytest.raises(ValueError):
            report.add("Configuration", status, "a label", "some detail")

    assert report.add("Configuration", "SKIP", "a label").status == "SKIP"


# Verifies a link in a detail line takes the link colour while a styled action line keeps its own colour
def test_a_link_in_a_detail_line_is_coloured_as_a_link(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "COLOR_ENABLED", True)
    monkeypatch.setattr(gm_module, "_COLOR_STYLES", {name: gm_module._build_ansi_sequence(value) for name, value in gm_module.DEFAULT_COLOR_THEME.items() if gm_module._build_ansi_sequence(value)})
    report = gm_module.DoctorReport()
    report.add("Connectivity", "PASS", "The connectivity endpoint is reachable", "Endpoint: https://api.github.com")
    report.add("Authentication", "FAIL", "The token did not validate", "", "Create a token at https://github.com/settings/tokens", gm_module.DOCTOR_GUIDE_URL)
    stream = io.StringIO()

    gm_module.render_doctor_sections(report, stream)
    rendered = stream.getvalue()
    fix_line = next(line for line in rendered.splitlines() if "To fix:" in line)

    assert f"  Endpoint: {gm_module.colorize('link', 'https://api.github.com')}" in rendered
    assert fix_line == f"  {gm_module.colorize('info', 'To fix: Create a token at https://github.com/settings/tokens')}"

# Verifies only the four shared markers can reach a report
def test_only_the_four_shared_markers_are_accepted(gm_module):
    report = gm_module.DoctorReport()
    assert gm_module.DOCTOR_STATUSES == ("PASS", "WARN", "FAIL", "SKIP")
    assert [report.add("Configuration", status, "a label", "", "do the thing").status for status in gm_module.DOCTOR_STATUSES] == list(gm_module.DOCTOR_STATUSES)

    with pytest.raises(ValueError):
        report.add("Configuration", "INFO", "a label", "", "do the thing")


# Verifies one row reads as one block: the action lines sit under the marker at the detail indent while a pass row has none
def test_the_action_lines_sit_indented_under_their_marker(gm_module):
    report = gm_module.DoctorReport()
    report.add("Configuration", "WARN", "a warning row", "a detail worth keeping", "do the thing", gm_module.DOCTOR_GUIDE_URL)
    report.add("Configuration", "PASS", "a passing row")
    output = io.StringIO()

    gm_module.render_doctor_sections(report, output)
    rows = [line for line in output.getvalue().splitlines() if line]

    assert rows[1:] == ["[WARN] a warning row", "  a detail worth keeping", "  To fix: do the thing", f"  Guide: {gm_module.DOCTOR_GUIDE_URL}", "[PASS] a passing row"]


# Verifies an approved delivery test that failed reaches the summary, so a failing run cannot report a clean one
def test_a_failed_delivery_test_reaches_the_summary(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "RECEIVER_EMAIL", "alerts@example.test")
    report = gm_module.DoctorReport(email_ready=True)
    output = FakeTTY()

    gm_module.doctor_run_optional_delivery_tests(report, lambda: "yes", FakeTTY(), output, Mock(return_value=1), Mock(return_value=0))

    assert [(check.section, check.status, check.label) for check in report.checks] == [("Optional delivery tests", "FAIL", "Doctor test email delivery failed")]
    assert report.failure_count == 1
    summary = io.StringIO()
    gm_module.render_doctor_summary(report, summary)
    assert "1 check(s) failed, 0 warning(s)." in summary.getvalue()


# Verifies a failed delivery test fails the whole run, so the exit code and the last sentence agree
def test_a_failed_delivery_test_changes_the_exit_code(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    configure_email(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "smtp_connect_and_login", lambda use_ssl, smtp_timeout=15: SimpleNamespace(quit=lambda: None))
    output = FakeTTY()

    result = gm_module.run_doctor(doctor_args(), Mock(), request_get=successful_request, github_factory=FakeGithub, module_finder=lambda name: object(), input_func=lambda: "yes", input_stream=FakeTTY(), stream=output, email_sender=Mock(return_value=1), webhook_sender=Mock(return_value=0))

    transcript = output.getvalue()
    assert result == 1
    assert "[FAIL] Doctor test email delivery failed" in transcript
    assert "1 check(s) failed" in transcript
    assert "All checks passed" not in transcript


# Verifies every doctor entry point renders its summary after the delivery tests, so the sentence and the exit code describe one run
def test_the_summary_is_rendered_after_the_delivery_tests(gm_module):
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(gm_module))
    checked = 0
    for function in [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]:
        calls = [(call.lineno, ast.unparse(call.func)) for call in ast.walk(function) if isinstance(call, ast.Call)]
        offers = [lineno for lineno, name in calls if name.endswith("doctor_run_optional_delivery_tests")]
        summaries = [lineno for lineno, name in calls if name.endswith("render_doctor_summary")]
        if not offers or not summaries:
            continue
        checked += 1
        assert max(offers) < min(summaries), f"{function.name} renders the summary before the delivery tests"

    assert checked, "no doctor entry point runs the delivery tests and then the summary"


# Verifies the connectivity row carries the label and the endpoint detail shared with the sibling monitors
def test_the_connectivity_row_names_the_shared_endpoint(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "CHECK_INTERNET_URL", "https://probe.example/ping")

    def offline_request(*args, **kwargs):
        raise gm_module.req.ConnectionError("offline for doctor")

    passing_report = gm_module.DoctorReport()
    gm_module.doctor_check_connectivity(passing_report, request_get=lambda *args, **kwargs: SimpleNamespace(status_code=204))
    failing_report = gm_module.DoctorReport()
    gm_module.doctor_check_connectivity(failing_report, request_get=offline_request)

    passing = passing_report.checks[0]
    failing = failing_report.checks[0]
    assert (passing.status, passing.label, passing.detail) == ("PASS", "The connectivity endpoint is reachable", "Endpoint: https://probe.example/ping")
    assert (failing.status, failing.label, failing.detail) == ("FAIL", "The connectivity endpoint could not be reached", "Endpoint: https://probe.example/ping")
    # The row carries no guide, because no page covers this check and the report ends with the doctor link
    assert (failing.fix, failing.guide) == ("Check network, DNS, proxy and CHECK_INTERNET_URL settings", "")


# Verifies a timed out endpoint keeps the wording the recovery advice gives every other surface
def test_the_connectivity_row_names_a_timeout(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "CHECK_INTERNET_URL", "https://probe.example/ping")

    def slow_request(*args, **kwargs):
        raise gm_module.req.Timeout("too slow for doctor")

    report = gm_module.DoctorReport()
    gm_module.doctor_check_connectivity(report, request_get=slow_request)

    assert (report.checks[0].status, report.checks[0].label) == ("FAIL", "The connectivity endpoint did not answer in time")


@pytest.mark.parametrize("status", [204, 403, 500, 504])
# Verifies the check reports reachability like the sibling monitors, which never read the status code
def test_the_connectivity_row_passes_on_any_answer(gm_module, monkeypatch, status):
    monkeypatch.setattr(gm_module, "CHECK_INTERNET_URL", "https://probe.example/ping")

    report = gm_module.DoctorReport()
    gm_module.doctor_check_connectivity(report, request_get=lambda *args, **kwargs: SimpleNamespace(status_code=status))

    assert (report.checks[0].status, report.checks[0].label) == ("PASS", "The connectivity endpoint is reachable")


# Verifies a report read on its own ends with the command that starts monitoring, carrying this run's files
def test_the_report_ends_with_the_command_that_starts_monitoring(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "CLI_CONFIG_PATH", "/etc/github.conf")
    monkeypatch.setattr(gm_module, "DOTENV_FILE", "/etc/github.env")
    destination = io.StringIO()

    gm_module.print_doctor_next_steps(destination, doctor_exit=0)

    transcript = destination.getvalue()
    assert "Next steps" in transcript
    assert "Start monitoring:" in transcript
    assert "--config-file /etc/github.conf --env-file /etc/github.env" in transcript
    assert transcript.rstrip().endswith(gm_module.QUICK_START_GUIDE_URL)


# Verifies a failing report names the order to work in, rather than inviting a run that cannot succeed yet
def test_a_failing_report_asks_for_the_failures_first(gm_module):
    destination = io.StringIO()

    gm_module.print_doctor_next_steps(destination, doctor_exit=1)

    assert "After Doctor passes, start monitoring:" in destination.getvalue()


# Verifies a target the command line named is carried, so the printed command watches the account just checked
def test_a_command_line_target_is_carried_into_the_command(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "CLI_CONFIG_PATH", "")
    monkeypatch.setattr(gm_module, "DOTENV_FILE", "")
    destination = io.StringIO()

    gm_module.print_doctor_next_steps(destination, "someone", doctor_exit=0)

    assert "someone" in destination.getvalue()


# Verifies the monitoring command carries a target only when the config will not supply one
def test_the_monitoring_command_leaves_out_a_target_the_config_supplies(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "CLI_CONFIG_PATH", "")
    monkeypatch.setattr(gm_module, "DOTENV_FILE", "")
    saved = io.StringIO()
    unsaved = io.StringIO()

    gm_module.print_doctor_next_steps(saved, "someone", "someone", doctor_exit=0)
    gm_module.print_doctor_next_steps(unsaved, None, "", doctor_exit=0)

    assert "someone" not in saved.getvalue()
    assert "<github_target>" not in saved.getvalue()
    assert "<github_target>" in unsaved.getvalue()


# Verifies the row names the state the shared resolver settled on, so it says what a restart would say
def test_the_timezone_row_follows_the_shared_resolver(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "LOCAL_TIMEZONE", "Mars/Olympus_Mons")
    monkeypatch.setattr(gm_module, "LOCAL_TIMEZONE_STATE", "config")
    # The check reassigns both from its arguments, so they are restored rather than left for the next test
    monkeypatch.setattr(gm_module, "CLI_CONFIG_PATH", None)
    monkeypatch.setattr(gm_module, "DOTENV_FILE", "")
    report = gm_module.DoctorReport(target_name="octocat")

    gm_module.doctor_check_configuration(report, doctor_args(), Mock())

    assert gm_module.LOCAL_TIMEZONE_STATE == "invalid"
    row = next(check for check in report.checks if check.label in gm_module.TIMEZONE_CHECK_LABELS.values())
    assert (row.status, row.label, row.detail) == ("FAIL", "Local timezone is invalid", "Time zone: Mars/Olympus_Mons")
    # A failed resolution still leaves a zone the rest of the report can stamp timestamps with
    assert gm_module.LOCAL_TIMEZONE == "UTC"


# Verifies Ctrl+C at a delivery prompt ends the run instead of declining one test and asking the next
def test_a_delivery_prompt_interrupt_ends_the_run(gm_module, monkeypatch):
    def interrupt(prompt=""):
        raise KeyboardInterrupt

    # The handler restores the saved stream, so it is pointed at the one this test captures
    monkeypatch.setattr(gm_module, "stdout_bck", gm_module.sys.stdout)

    with pytest.raises(SystemExit) as raised:
        gm_module.ask_doctor_approval("Send one test", interrupt)

    assert raised.value.code == 0


# Verifies an unreadable delivery answer is asked again rather than counted as a refusal the user did not give
def test_an_unreadable_delivery_answer_is_asked_again(gm_module):
    answers = iter(["maybe", "yes"])
    stream = io.StringIO()

    approved = gm_module.ask_doctor_approval("Send one test", lambda: next(answers), stream)

    assert approved is True
    written = stream.getvalue()
    assert written.count("Send one test [y/N]: ") == 2
    assert "Please answer 'y' or 'n'." in written


# Verifies a blank answer still declines, so the prompt keeps defaulting to no rather than looping forever
def test_a_blank_delivery_answer_still_declines(gm_module):
    stream = io.StringIO()

    assert gm_module.ask_doctor_approval("Send one test", lambda: "", stream) is False
    assert stream.getvalue().count("Send one test [y/N]: ") == 1


# Verifies a closed input at a delivery prompt says the test was skipped rather than ending on a bare newline
def test_a_closed_delivery_prompt_says_the_test_was_skipped(gm_module):
    def closed():
        raise EOFError

    stream = io.StringIO()

    assert gm_module.ask_doctor_approval("Send one test", closed, stream) is False
    assert "Delivery test skipped." in stream.getvalue()


# An interval below the safe floor gets the token rate limited, which looks like the tool being broken
def test_a_rate_limiting_interval_is_warned_about(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "GITHUB_CHECK_INTERVAL", 5)
    report = gm_module.DoctorReport(target_name="octocat")

    gm_module.doctor_check_configuration(report, doctor_args(), Mock())

    rows = [check for check in report.checks if check.label == "Check intervals are short"]
    assert [check.status for check in rows] == ["WARN"]
    assert str(gm_module.DOCTOR_MIN_SAFE_CHECK_INTERVAL) in rows[0].fix


# The default interval is safe, so the row must stay away rather than warning about every run
def test_a_safe_interval_is_not_warned_about(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "GITHUB_CHECK_INTERVAL", gm_module.DOCTOR_MIN_SAFE_CHECK_INTERVAL)
    report = gm_module.DoctorReport(target_name="octocat")

    gm_module.doctor_check_configuration(report, doctor_args(), Mock())

    assert not [check for check in report.checks if check.label == "Check intervals are short"]


# A run with no target warns with the sentence every monitor in this family uses, so the report reads the same
def test_a_missing_target_warns_with_the_shared_detail(gm_module):
    report = gm_module.DoctorReport()

    gm_module.doctor_check_target(report)

    rows = [check for check in report.checks if check.section == "Target"]
    assert [check.status for check in rows] == ["WARN"]
    assert rows[0].detail == "Nothing will be monitored until one is given"


# Verifies a target that cannot be looked up is skipped rather than failed, as in every sibling
def test_doctor_skips_the_target_and_its_feeds_without_authentication(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "TRACK_CONTRIB_CHANGES", True)
    report = gm_module.DoctorReport(target_name="octocat", authenticated_login=None)

    gm_module.doctor_check_target(report)
    gm_module.doctor_check_monitoring(report)

    skipped = [(check.section, check.label) for check in report.checks if check.status == "SKIP"]
    assert ("Target", "The monitored profile was not checked") in skipped
    assert ("Monitoring", "Core monitoring feeds were not checked") in skipped
    assert ("Monitoring", "Daily contribution feed was not checked") in skipped
    assert not any(check.status == "FAIL" for check in report.checks)


# Verifies webhook alert types selected while the channel is off warn, since nothing would ever be delivered
def test_doctor_warns_when_webhook_alerts_are_selected_but_switched_off(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "WEBHOOK_ENABLED", False)
    monkeypatch.setattr(gm_module, "WEBHOOK_PROFILE_NOTIFICATION", True)
    report = gm_module.DoctorReport()

    gm_module.doctor_check_notifications(report)

    webhook = report.checks[-1]
    assert (webhook.status, webhook.label) == ("WARN", "Webhook alert types are selected but webhooks are switched off")
    assert "WEBHOOK_ENABLED" in webhook.fix
    assert report.webhook_ready is False


# Verifies configured mail settings with no alert types selected warn, since nothing would ever be emailed
def test_doctor_warns_when_email_is_configured_but_nothing_is_selected(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    for name in ("PROFILE_NOTIFICATION", "EVENT_NOTIFICATION", "REPO_NOTIFICATION", "REPO_UPDATE_DATE_NOTIFICATION", "CONTRIB_NOTIFICATION", "ERROR_NOTIFICATION"):
        monkeypatch.setattr(gm_module, name, False)
    monkeypatch.setattr(gm_module, "SMTP_HOST", "smtp.example.test")
    monkeypatch.setattr(gm_module, "SMTP_USER", "monitor")
    monkeypatch.setattr(gm_module, "SMTP_PASSWORD", "private-password")
    monkeypatch.setattr(gm_module, "SENDER_EMAIL", "monitor@example.test")
    monkeypatch.setattr(gm_module, "RECEIVER_EMAIL", "alerts@example.test")
    monkeypatch.setattr(gm_module, "smtp_connect_and_login", Mock(side_effect=AssertionError("SMTP was contacted")))
    report = gm_module.DoctorReport()

    gm_module.doctor_check_notifications(report)

    email = report.checks[0]
    assert (email.status, email.label) == ("WARN", "Email is configured but no alert types are selected")
    assert email.fix == "Turn on at least one email alert in the configuration file"
    assert report.email_ready is False


# Every sibling builds its doctor rows through this name, and the report method is one caller among them
def test_the_doctor_row_builder_carries_the_family_name(gm_module):
    row = gm_module.make_doctor_check("Environment", "pass", "A label", "A label")

    assert row.status == "PASS"
    # A detail that repeats its label reads as two problems, so the builder drops it
    assert row.detail == ""
    with pytest.raises(ValueError, match="Unsupported doctor status"):
        gm_module.make_doctor_check("Environment", "NOTE", "A label")
    with pytest.raises(ValueError, match="rows require a fix"):
        gm_module.make_doctor_check("Environment", "FAIL", "A label")


# The report method has to stay the same validation rather than a second copy of it
def test_the_report_method_validates_through_the_builder(gm_module):
    report = gm_module.DoctorReport()

    added = report.add("Environment", "warn", "A label", "A detail", "A fix")

    assert report.checks == [added]
    assert added == gm_module.make_doctor_check("Environment", "warn", "A label", "A detail", "A fix")


# Verifies the preflight and its row printer answer to the names every sibling uses for them
def test_the_doctor_entry_points_carry_the_family_names(gm_module):
    assert callable(gm_module.run_doctor) and callable(gm_module.print_doctor_check)
    assert not hasattr(gm_module, "run_doctor_preflight") and not hasattr(gm_module, "render_doctor_check")
    # The row printer takes the row alone, so the stream this tool injects cannot bind to a sibling's parameter
    parameters = list(inspect.signature(gm_module.print_doctor_check).parameters.values())
    assert parameters[0].name == "check"
    assert all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in parameters[1:])
