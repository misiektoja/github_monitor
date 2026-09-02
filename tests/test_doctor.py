"""Offline contract tests for the comprehensive doctor preflight."""

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

    result = gm_module.run_doctor_preflight(doctor_args(), Mock(), request_get=successful_request, github_factory=FakeGithub, module_finder=lambda name: object(), stream=output)

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

    gm_module.run_doctor_preflight(doctor_args(), Mock(), request_get=successful_request, github_factory=FakeGithub, module_finder=lambda name: object(), stream=output)

    transcript = output.getvalue()
    method = gm_module.detect_install_context().install_method
    assert f"\nDoctor\nDetected install method: {method}\n" in transcript
    assert "[PASS] Install method" not in transcript


# Verifies missing setup produces all useful failures in one report and exits unhealthy
def test_doctor_reports_missing_authentication_and_target(gm_module, monkeypatch):
    configure_healthy_doctor(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", "")
    output = io.StringIO()

    result = gm_module.run_doctor_preflight(doctor_args(username=None), Mock(), request_get=successful_request, github_factory=FakeGithub, module_finder=lambda name: object(), stream=output)

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

    result = gm_module.run_doctor_preflight(doctor_args(username=None), Mock(), request_get=successful_request, github_factory=FakeGithub, module_finder=lambda name: object(), stream=output)

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

    result = gm_module.run_doctor_preflight(doctor_args(), Mock(), request_get=offline_request, github_factory=FakeGithub, module_finder=lambda name: object(), stream=output)

    transcript = output.getvalue()
    assert result == 1
    assert "[FAIL] GitHub token validation failed" in transcript
    assert "[FAIL] Configured connectivity endpoint is unreachable" in transcript
    assert "ConnectionError" in transcript
    assert "[FAIL] GitHub target could not be checked" in transcript


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
    assert missing.detail == "Coloured output in the classic Windows Command Prompt will not work while other features remain available"
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
    assert "To fix: Install Python 3.10 or newer" in transcript
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

    failed_labels = {check.label for check in report.checks if check.status == "FAIL"}
    assert {"Polling interval is invalid", "Connectivity timeout is invalid", "Recent event window is invalid", "GitHub retry policy is invalid", "Event type selection is invalid"} <= failed_labels


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
    monkeypatch.setattr(gm_module, "PROFILE_NOTIFICATION", True)
    monkeypatch.setattr(gm_module, "WEBHOOK_ENABLED", True)
    monkeypatch.setattr(gm_module, "WEBHOOK_PROFILE_NOTIFICATION", True)
    invalid = gm_module.DoctorReport()

    gm_module.doctor_check_notifications(invalid)

    assert [check.status for check in invalid.checks] == ["WARN", "WARN"]
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
    assert "[PASS] Test email was delivered" in transcript
    assert "Send one test webhook through Discord now? This will publish a real notification [y/N]: " in transcript
    assert "[SKIP] Test webhook through Discord was not sent" in transcript
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
    assert "[FAIL] Test email delivery failed" in output.getvalue()


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


# Verifies every non-pass transcript row carries its fix and guide contract
def test_doctor_non_pass_rows_always_render_fix_and_guide(gm_module):
    report = gm_module.DoctorReport()
    report.add("Configuration", "WARN", "Warning row", "warning detail", "correct warning")
    report.add("Authentication", "FAIL", "Failure row", "failure detail", "correct failure")
    report.add("Optional delivery tests", "SKIP", "Skipped row", "declined", "approve later")
    output = io.StringIO()

    for check in report.checks:
        gm_module.render_doctor_check(check, output)

    transcript = output.getvalue()
    assert transcript.count("To fix:") == 3
    assert transcript.count("Guide:") == 3
    assert {check.status for check in report.checks} == {"WARN", "FAIL", "SKIP"}


# Verifies the support loop asks bug reporters for the complete doctor transcript
def test_bug_report_collects_doctor_output():
    issue_template = (PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").read_text(encoding="utf-8")
    support = (PROJECT_ROOT / "SUPPORT.md").read_text(encoding="utf-8")
    assert "id: doctor-output" in issue_template
    assert "github_monitor --doctor <github_username>" in issue_template
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
