"""Offline tests for structured recovery advice and secret-safe rendering."""

import io
import smtplib

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
