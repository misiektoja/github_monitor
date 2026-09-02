"""Offline tests for structured recovery advice and secret-safe rendering."""

import inspect
import io
import smtplib
import time

import pytest


# Verifies recovery advice accepts only the stable public code set
def test_recovery_codes_are_closed(gm_module):
    advice = gm_module.make_recovery_advice("config.invalid", "Bad config", "Fix config")
    assert advice.code == "config.invalid"
    assert isinstance(gm_module.RECOVERY_CODES, frozenset)
    with pytest.raises(ValueError, match="Unsupported recovery code"):
        gm_module.make_recovery_advice("config.typo", "Bad config", "Fix config")


# Verifies construction and rendering redact known values plus common credential shapes
def test_recovery_rendering_redacts_secrets_at_both_boundaries(gm_module, monkeypatch):
    github_token = "github_pat_private_recovery_value"
    webhook_url = "https://discord.com/api/webhooks/123/private-recovery-value"
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", github_token)
    monkeypatch.setattr(gm_module, "WEBHOOK_URL", webhook_url)
    advice = gm_module.make_recovery_advice("network.connection", f"Request failed for {github_token}", "Check the connection", True, f"Authorization: Bearer {github_token} at {webhook_url}", gm_module.DEBUG_GUIDE_URL)

    normal = gm_module.render_recovery_advice(advice, verbose=False, debug=False)
    debug = gm_module.render_recovery_advice(advice, verbose=False, debug=True)

    assert github_token not in normal + debug
    assert webhook_url not in normal + debug
    assert "Technical detail:" not in normal
    assert "Recovery code: network.connection" in debug
    assert "Retryable: Yes" in debug
    assert "Technical detail:" in debug
    assert "<redacted>" in debug


# Verifies verbose mode adds stable triage fields without exposing technical detail
def test_verbose_recovery_output_omits_technical_detail(gm_module):
    advice = gm_module.make_recovery_advice("target.missing", "No target", "Add a target", False, "internal detail")
    output = gm_module.render_recovery_advice(advice, verbose=True, debug=False)
    assert "Recovery code: target.missing" in output
    assert "Retryable: No" in output
    assert "Technical detail:" not in output


@pytest.mark.parametrize(
    ("error", "context", "code", "retryable"),
    [
        (TimeoutError("slow"), "network", "network.timeout", True),
        (PermissionError("denied"), "file", "file.unwritable", False),
        (FileNotFoundError("missing"), "config", "config.missing", False),
        (smtplib.SMTPAuthenticationError(535, b"rejected"), "smtp", "smtp.authentication", False),
        (ValueError("bad value"), "webhook", "webhook.invalid", False),
        (RuntimeError("unexpected"), "unknown", "unknown", False),
    ],
)
# Verifies the central classifier assigns stable codes and retryability by cause plus context
def test_recovery_classifier_maps_representative_failures(gm_module, error, context, code, retryable):
    advice = gm_module.classify_recovery_error(error, context)
    assert advice.code == code
    assert advice.retryable is retryable


# The connectivity check has no page of its own, and its fix already names the setting to look at
def test_the_connectivity_advice_carries_no_guide_link(gm_module):
    advice = gm_module.classify_recovery_error(gm_module.req.ConnectionError("offline"), "connectivity")

    assert advice.code == "network.connection"
    assert advice.fix == "Check network, DNS, proxy and CHECK_INTERNET_URL settings"
    assert advice.guide_url == ""


# Verifies RecoveryError carries structured advice and its original cause
def test_recovery_error_preserves_advice_and_cause(gm_module):
    cause = RuntimeError("underlying")
    advice = gm_module.make_recovery_advice("unknown", "Stopped", "Retry with debug")
    error = gm_module.RecoveryError(advice, cause)
    assert error.advice is advice
    assert error.cause is cause
    assert str(error) == "Stopped"


# Verifies secret masking reveals no characters from a configured value
def test_secret_masking_never_returns_the_complete_value(gm_module):
    secret = "abcdefghijk"
    masked = gm_module.mask_secret(secret)
    assert masked == "<redacted>"
    assert masked != secret


# Verifies the monitoring stream sanitizes both terminal and log output
def test_logger_redacts_secrets_from_terminal_and_log(gm_module, monkeypatch):
    secret = "github_pat_logger_private_value"
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", secret)
    logger = object.__new__(gm_module.Logger)
    logger.terminal = io.StringIO()
    logger.logfile = io.StringIO()

    logger.write(f"request failed for {secret}\n")

    assert secret not in logger.terminal.getvalue()
    assert secret not in logger.logfile.getvalue()
    assert "<redacted>" in logger.terminal.getvalue()


# Sanitizing runs over every logged line, so a short secret must not redact ordinary words in monitoring output
def test_short_secrets_do_not_redact_ordinary_output(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "SMTP_PASSWORD", "github")
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", "")
    monkeypatch.setattr(gm_module, "WEBHOOK_URL", "")

    assert gm_module.sanitize_error_text("Pushed to repo github/monitor") == "Pushed to repo github/monitor"
    # The assignment shape an error can actually expose stays covered
    assert "github" not in gm_module.sanitize_error_text("SMTP_PASSWORD = github")


# Verifies a credential of realistic length is still replaced wherever it appears
def test_full_length_secrets_are_still_redacted(gm_module, monkeypatch):
    token = "ghp_" + "A" * 36
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", token)

    assert token not in gm_module.sanitize_error_text(f"Request failed for {token}")


# Verifies a config failure names the rejected setting without waiting for --debug
def test_config_advice_summary_names_the_rejected_setting(gm_module):
    error = ValueError("Line 2: GITHUB_CHECK_INTERVAL must be a plain value")

    advice = gm_module.classify_recovery_error(error, "config")

    assert advice.code == "config.invalid"
    assert "GITHUB_CHECK_INTERVAL" in advice.summary
    assert "GITHUB_CHECK_INTERVAL" in gm_module.render_recovery_advice(advice, verbose=False, debug=False)


# Verifies a repeated failure category prints its fix once and keeps the retry note on the summary line
def test_repeated_advice_keeps_the_summary_and_drops_the_fix(gm_module, capsys):
    tracker = gm_module.RecoveryHintTracker()
    advice = gm_module.make_recovery_advice("github.api_error", "GitHub returned an API error", "Try again later", True)

    gm_module.print_recovery_advice(advice, verbose=False, debug=False, tracker=tracker, retry_note="retrying in 1 hour")
    first = capsys.readouterr().out
    gm_module.print_recovery_advice(advice, verbose=False, debug=False, tracker=tracker, retry_note="retrying in 1 hour")
    second = capsys.readouterr().out
    tracker.reset()
    gm_module.print_recovery_advice(advice, verbose=False, debug=False, tracker=tracker, retry_note="retrying in 1 hour")
    third = capsys.readouterr().out

    assert first == "* Error: GitHub returned an API error (retrying in 1 hour)\nTo fix: Try again later\n"
    assert second == "* Error: GitHub returned an API error (retrying in 1 hour)\n"
    assert third == first


# Verifies a lasting failure is reported once and then only once the liveness interval has passed
def test_the_outage_reporter_reports_once_then_on_the_cadence(gm_module, monkeypatch):
    clock = [1000000.0]
    monkeypatch.setattr(gm_module.time, "time", lambda: clock[0])
    reporter = gm_module.OutageReporter()
    advice = gm_module.make_recovery_advice("github.api_error", "GitHub returned an API error", "Try again later", True)

    assert reporter.failed(advice, 180) == "full"
    outcomes = []
    for _ in range(3):
        clock[0] += 60
        outcomes.append(reporter.failed(advice, 180))

    assert outcomes == ["", "", "degraded"]
    assert reporter.recovered() is not None
    assert reporter.recovered() is None


# Verifies the reminder follows the clock, so a run that retries faster than it polls does not remind more often
def test_the_outage_reminder_follows_the_clock_not_the_check_count(gm_module, monkeypatch):
    clock = [1000000.0]
    monkeypatch.setattr(gm_module.time, "time", lambda: clock[0])
    reporter = gm_module.OutageReporter()
    advice = gm_module.make_recovery_advice("github.api_error", "GitHub returned an API error", "Try again later", True)

    assert reporter.failed(advice, 900) == "full"
    outcomes = []
    for _ in range(60):
        clock[0] += 15
        outcomes.append(reporter.failed(advice, 900))

    assert outcomes.count("degraded") == 1


# Verifies the summary keeps its every-check cadence when the liveness banner is switched off
def test_the_outage_reporter_keeps_repeating_without_a_liveness_banner(gm_module):
    reporter = gm_module.OutageReporter()
    advice = gm_module.make_recovery_advice("github.api_error", "GitHub returned an API error", "Try again later", True)

    assert reporter.failed(advice, 0) == "full"
    assert [reporter.failed(advice, 0) for _ in range(2)] == ["repeat", "repeat"]


# Verifies a failure category that changes is reported in full again rather than hidden by the previous one
def test_a_changed_failure_category_is_reported_in_full(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "LOCAL_TIMEZONE", "UTC")
    reporter = gm_module.OutageReporter()
    api_error = gm_module.make_recovery_advice("github.api_error", "GitHub returned an API error", "Try again later", True)
    forbidden = gm_module.make_recovery_advice("github.forbidden", "GitHub refused access to the requested resource", "Check token permissions", False)

    assert reporter.failed(api_error, 5) == "full"
    assert reporter.failed(api_error, 5) == ""
    assert reporter.failed(forbidden, 5) == "full"

    gm_module.print_outage_liveness("misiektoja", forbidden, int(time.time()) - 60)
    gm_module.print_outage_recovery("misiektoja", 60)

    output = capsys.readouterr().out
    assert "* Monitoring degraded for misiektoja. GitHub refused access to the requested resource since " in output
    assert "Liveness check, timestamp:" in output
    assert "* Monitoring recovered for misiektoja after 1 minute" in output


# Verifies the monitoring loop classifies its own failures instead of printing raw exception text
def test_the_monitoring_loop_classifies_its_failures(gm_module):
    source = inspect.getsource(gm_module.github_monitor_user)

    assert 'classify_recovery_error(e, "target")' in source
    assert "outage.failed(advice, LIVENESS_REMINDER_SECONDS)" in source
    assert "print_outage_liveness(user, advice, outage.since)" in source
    assert "print_outage_recovery(user, outage_lasted)" in source
    assert '"Forbidden"' not in source, "the loop must classify failures rather than match exception text"
    assert '"Bad Request"' not in source, "the loop must classify failures rather than match exception text"


# Verifies a named sub-operation keeps the shared line shape rather than inventing its own
def test_a_labelled_failure_keeps_the_shared_shape(gm_module, capsys):
    advice = gm_module.make_recovery_advice("github.api_error", "GitHub returned an API error", "Try again later", True)

    gm_module.print_recovery_advice(advice, verbose=False, debug=False, retry_note="retrying in 1 hour", label="Warning")

    assert capsys.readouterr().out.splitlines()[0] == "* Warning: GitHub returned an API error (retrying in 1 hour)"


# Verifies the liveness banner explains itself without --verbose, so a plain run never prints a bare timestamp
def test_the_liveness_banner_explains_itself_without_diagnostics(gm_module, monkeypatch, capsys):
    monkeypatch.setattr(gm_module, "LOCAL_TIMEZONE", "UTC")
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", False)

    gm_module.print_liveness_banner("Monitoring healthy for misiektoja. No tracked change since the last check")

    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "* Monitoring healthy for misiektoja. No tracked change since the last check"
    assert lines[1].startswith("Liveness check, timestamp:")


# Verifies the monitoring loop reports its healthy banner through the shared helper
def test_the_loop_reports_its_healthy_banner_unconditionally(gm_module):
    source = inspect.getsource(gm_module.github_monitor_user)

    assert "print_liveness_banner(f\"Monitoring healthy for {user}." in source
    assert "verbose_print(f\"Monitoring healthy" not in source, "the healthy banner is no longer verbose-only"
