"""Offline tests for Discord and ntfy webhook notification behavior."""

import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = PROJECT_ROOT / "local" / "webhook_test_artifacts"


# Creates one disposable webhook test directory under the project local directory
def make_test_directory():
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=ARTIFACT_ROOT)


# Stores one fake webhook response with optional rate-limit metadata
class FakeResponse:
    # Initializes one response value used by isolated transport tests
    def __init__(self, status_code=204, text="", headers=None, payload=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}
        self.payload = payload

    # Returns the configured JSON payload or raises when none was provided
    def json(self):
        if self.payload is None:
            raise ValueError("no JSON payload")
        return self.payload


# Enables one valid test webhook without affecting email settings
def configure_webhook(gm_module, monkeypatch, provider="discord"):
    monkeypatch.setattr(gm_module, "WEBHOOK_ENABLED", True)
    monkeypatch.setattr(gm_module, "WEBHOOK_URL", "https://discord.com/api/webhooks/123/private-token")
    monkeypatch.setattr(gm_module, "WEBHOOK_PROVIDER", provider)
    monkeypatch.setattr(gm_module, "WEBHOOK_USERNAME", "GitHub Monitor")
    monkeypatch.setattr(gm_module, "WEBHOOK_AVATAR_URL", "")
    monkeypatch.setattr(gm_module, "WEBHOOK_HEADERS", {})
    monkeypatch.setattr(gm_module, "WEBHOOK_TRANSFORMS", [])
    monkeypatch.setattr(gm_module, "NTFY_ACCESS_TOKEN", "")
    monkeypatch.setattr(gm_module, "WEBHOOK_PROFILE_NOTIFICATION", True)
    monkeypatch.setattr(gm_module, "WEBHOOK_TEMPLATE", {"username": "{username}", "avatar_url": "{avatar_url}", "allowed_mentions": {"parse": []}, "embeds": [{"title": "{title}", "description": "{description}", "color": "{color}", "timestamp": "{timestamp}"}]})


# Verifies startup summaries use short labels and unstarred bounded continuation lines
def test_startup_notification_summaries_use_compact_rollups(gm_module, monkeypatch):
    email_settings = {"PROFILE_NOTIFICATION": True, "EVENT_NOTIFICATION": True, "REPO_NOTIFICATION": True, "REPO_UPDATE_DATE_NOTIFICATION": True, "CONTRIB_NOTIFICATION": True, "ERROR_NOTIFICATION": True}
    webhook_settings = {"WEBHOOK_ENABLED": True, "WEBHOOK_PROFILE_NOTIFICATION": True, "WEBHOOK_EVENT_NOTIFICATION": True, "WEBHOOK_REPO_NOTIFICATION": True, "WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION": True, "WEBHOOK_CONTRIB_NOTIFICATION": True, "WEBHOOK_ERROR_NOTIFICATION": True}
    for setting, value in {**email_settings, **webhook_settings}.items():
        monkeypatch.setattr(gm_module, setting, value)
    rows = {row.label: row.value for row in gm_module.build_startup_summary("octocat", None, None, None)}
    assert rows["Notifications (email)"] == "On (profile, events, repositories, repository updates, contributions, errors)"
    assert rows["Notifications (webhook)"] == "On (profile, events, repositories, repository updates, contributions, errors)"


# Verifies webhook categories remain off while the master switch is disabled
def test_startup_webhook_summary_respects_master_switch(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "WEBHOOK_ENABLED", False)
    monkeypatch.setattr(gm_module, "WEBHOOK_PROFILE_NOTIFICATION", True)
    monkeypatch.setattr(gm_module, "WEBHOOK_ERROR_NOTIFICATION", True)
    monkeypatch.setattr(gm_module, "PROFILE_NOTIFICATION", True)
    for setting in ("EVENT_NOTIFICATION", "REPO_NOTIFICATION", "REPO_UPDATE_DATE_NOTIFICATION", "CONTRIB_NOTIFICATION", "ERROR_NOTIFICATION"):
        monkeypatch.setattr(gm_module, setting, False)

    rows = {row.label: row.value for row in gm_module.build_startup_summary("octocat", None, None, None)}

    assert rows["Notifications (webhook)"] == "Off"
    # The two rows are read side by side, so the email row has to keep reporting its own channel
    assert rows["Notifications (email)"] == "On (profile)"


# Verifies SIGHUP schedules API client recreation and redetects an ntfy destination
def test_sighup_reload_updates_auth_generation_and_webhook_provider(gm_module, monkeypatch):
    replacements = {"GITHUB_TOKEN": "new-github-token", "WEBHOOK_URL": "https://ntfy.sh/new-private-topic"}
    monkeypatch.setattr(gm_module, "DOTENV_FILE", "test.env")
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", "old-github-token")
    monkeypatch.setattr(gm_module, "GITHUB_AUTH_REFRESH_VERSION", 6)
    monkeypatch.setattr(gm_module, "WEBHOOK_URL", "https://discord.com/api/webhooks/123/old-token")
    monkeypatch.setattr(gm_module, "WEBHOOK_PROVIDER", "discord")
    with patch("dotenv.load_dotenv"), patch.object(gm_module.os, "getenv", side_effect=replacements.get):
        gm_module.reload_secrets_signal_handler(gm_module.signal.SIGHUP, None)
    assert gm_module.GITHUB_TOKEN == "new-github-token"
    assert gm_module.GITHUB_AUTH_REFRESH_VERSION == 7
    assert gm_module.WEBHOOK_PROVIDER == "ntfy"


@pytest.mark.parametrize("url,expected", [("https://discord.com/api/webhooks/123/token", True), ("https://hooks.example.test/discord/path", True), ("http://discord.com/api/webhooks/123/token", False), ("https://user:password@example.test/hook", False), ("https://example.test", False), ("not-a-url", False), ("", False)])
# Verifies webhook URLs require complete HTTPS endpoints without embedded credentials
def test_webhook_url_validation(gm_module, url, expected):
    assert gm_module.validate_webhook_url(url) is expected


@pytest.mark.parametrize("url,expected", [("https://discord.com/api/webhooks/123/token", "discord"), ("https://canary.discord.com/api/v10/webhooks/123/token", "discord"), ("https://ntfy.sh/private-topic", "ntfy"), ("https://ntfy.example.test/private-topic", ""), ("https://example.test/custom-hook", "")])
# Verifies distinctive Discord and public ntfy URLs select the proper payload provider
def test_webhook_provider_detection(gm_module, url, expected):
    assert gm_module.detect_webhook_provider(url) == expected


@pytest.mark.parametrize("value,expected", [("https://ntfy.example.test/private-topic?auth=value", "https://ntfy.example.test/private-topic?auth=value"), (" private_Topic-123 ", "https://ntfy.sh/private_Topic-123"), ("a" * 64, f"https://ntfy.sh/{'a' * 64}"), ("a" * 65, ""), ("ntfy.sh/private-topic", ""), ("http://ntfy.sh/private-topic", ""), ("private.topic", ""), ("private/topic", ""), (None, "")])
# Verifies ntfy input normalization preserves HTTPS URLs and expands only valid bare topics
def test_ntfy_topic_url_normalization(gm_module, value, expected):
    assert gm_module.normalize_ntfy_topic_url(value) == expected


# Verifies Discord payloads are bounded, mention-safe and secret-redacted
def test_webhook_payload_is_bounded_and_safe(gm_module, monkeypatch):
    configure_webhook(gm_module, monkeypatch)
    secret = "https://discord.com/api/webhooks/123/private-token"
    github_token = "github_pat_private"
    monkeypatch.setattr(gm_module, "GITHUB_TOKEN", github_token)
    payload = gm_module.build_webhook_payload("@everyone " + ("t" * 300), f"failed at {secret} with {github_token} @here", "error")
    embed = payload["embeds"][0]
    assert len(embed["title"]) == gm_module.WEBHOOK_EMBED_TITLE_LIMIT
    assert secret not in embed["description"]
    assert github_token not in embed["description"]
    assert payload["allowed_mentions"] == {"parse": []}
    assert embed["color"] == 0xE74C3C


# Verifies custom templates, avatars, transformations and header placeholders share sanitized values
def test_advanced_webhook_customization(gm_module, monkeypatch):
    configure_webhook(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "WEBHOOK_AVATAR_URL", "https://cdn.example.test/avatar.png")
    monkeypatch.setattr(gm_module, "WEBHOOK_HEADERS", {"X-Webhook-Title": "{title}", "X-Webhook-Version": "{version}"})
    monkeypatch.setattr(gm_module, "WEBHOOK_TEMPLATE", {"content": "{title}: {description}", "avatar_url": "{avatar_url}", "color": "{color}", "allowed_mentions": {"parse": ["everyone"]}})
    monkeypatch.setattr(gm_module, "WEBHOOK_TRANSFORMS", [("title", "replace", "secret", "masked"), ("description", "upper")])
    webhook_post = Mock(return_value=FakeResponse())
    monkeypatch.setattr(gm_module.WEBHOOK_SESSION, "post", webhook_post)
    assert gm_module.send_webhook("secret title", "custom body", "profile") == 0
    request = webhook_post.call_args
    assert request.kwargs["json"] == {"content": "masked title: CUSTOM BODY", "avatar_url": "https://cdn.example.test/avatar.png", "color": 0x2F81F7, "allowed_mentions": {"parse": []}}
    assert request.kwargs["headers"]["X-Webhook-Title"] == "masked title"
    assert request.kwargs["headers"]["X-Webhook-Version"] == gm_module.VERSION


# Verifies formatted headers are validated again before network delivery
def test_formatted_webhook_headers_reject_line_breaks(gm_module, monkeypatch):
    configure_webhook(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "WEBHOOK_HEADERS", {"X-Description": "{description}"})
    webhook_post = Mock(side_effect=AssertionError("webhook request attempted"))
    monkeypatch.setattr(gm_module.WEBHOOK_SESSION, "post", webhook_post)
    assert gm_module.send_webhook("Title", "first\nsecond", "profile") == 1
    webhook_post.assert_not_called()


# Verifies ntfy receives native UTF-8 text with bearer authentication
def test_successful_ntfy_webhook_uses_native_topic_api(gm_module, monkeypatch):
    configure_webhook(gm_module, monkeypatch, provider="ntfy")
    monkeypatch.setattr(gm_module, "WEBHOOK_URL", "https://ntfy.sh/private-topic?auth=private-auth-value")
    monkeypatch.setattr(gm_module, "NTFY_ACCESS_TOKEN", "tk_private_access_token")
    webhook_post = Mock(return_value=FakeResponse(200))
    monkeypatch.setattr(gm_module.WEBHOOK_SESSION, "post", webhook_post)
    assert gm_module.send_webhook("GitHub title", "New event: push", "profile") == 0
    request = webhook_post.call_args
    assert request.args == ("https://ntfy.sh/private-topic?auth=private-auth-value",)
    assert request.kwargs["data"] == b"New event: push"
    assert request.kwargs["params"] == {"title": "GitHub title"}
    assert request.kwargs["headers"]["Authorization"] == "Bearer tk_private_access_token"
    assert request.kwargs["headers"]["Content-Type"] == "text/plain; charset=utf-8"
    assert "json" not in request.kwargs


# Verifies long ntfy messages stay below the server attachment boundary with a visible truncation marker
def test_ntfy_message_stays_below_attachment_boundary(gm_module):
    title, message = gm_module.build_ntfy_webhook_message("GitHub title", ("a" * gm_module.NTFY_MESSAGE_LIMIT_BYTES) + "\U0001f3b5")
    assert title == "GitHub title"
    assert message.endswith(gm_module.NTFY_TRUNCATION_SUFFIX)
    assert len(message.encode("utf-8")) <= gm_module.NTFY_MESSAGE_LIMIT_BYTES
    assert len(message.encode("utf-8")) < 4096
    assert "\ufffd" not in message


# Verifies rate-limited webhook delivery waits for a capped delay then retries once
def test_rate_limit_retries_once_with_capped_delay(gm_module, monkeypatch):
    configure_webhook(gm_module, monkeypatch)
    webhook_post = Mock(side_effect=[FakeResponse(429, headers={"Retry-After": "99"}), FakeResponse(204)])
    sleeps = []
    monkeypatch.setattr(gm_module.WEBHOOK_SESSION, "post", webhook_post)
    assert gm_module.send_webhook("Title", "Body", "profile", sleeper=sleeps.append) == 0
    assert webhook_post.call_count == 2
    assert sleeps == [gm_module.WEBHOOK_MAX_RETRY_AFTER_SECONDS]


# Verifies webhook delivery remains independent when email alerts are disabled
def test_notification_channels_are_independent(gm_module, monkeypatch):
    configure_webhook(gm_module, monkeypatch)
    email_send = Mock()
    webhook_send = Mock(return_value=0)
    monkeypatch.setattr(gm_module, "send_email", email_send)
    monkeypatch.setattr(gm_module, "send_webhook", webhook_send)
    assert gm_module.send_notification_channels("profile", "Title", "Body", email_enabled=False) == (False, True)
    email_send.assert_not_called()
    webhook_send.assert_called_once_with("Title", "Body", "profile", force=True)


# Verifies category CLI overrides enable webhooks while preserving an explicit error override
def test_webhook_cli_overrides_match_runtime_settings(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "WEBHOOK_ENABLED", False)
    monkeypatch.setattr(gm_module, "WEBHOOK_PROFILE_NOTIFICATION", False)
    monkeypatch.setattr(gm_module, "WEBHOOK_ERROR_NOTIFICATION", True)
    args = SimpleNamespace(webhook_provider="ntfy", webhook_url="https://ntfy.sh/private-topic", webhook_enabled=None, webhook_profile=True, webhook_events=None, webhook_repo_changes=None, webhook_repo_update_date=None, webhook_daily_contribs=None, webhook_errors=False)
    parser = Mock()
    gm_module.apply_webhook_cli_overrides(args, parser)
    parser.error.assert_not_called()
    assert gm_module.WEBHOOK_ENABLED is True
    assert gm_module.WEBHOOK_PROVIDER == "ntfy"
    assert gm_module.WEBHOOK_URL == "https://ntfy.sh/private-topic"
    assert gm_module.WEBHOOK_PROFILE_NOTIFICATION is True
    assert gm_module.WEBHOOK_ERROR_NOTIFICATION is False


# Verifies a known ntfy URL corrects a stale configured provider and sends native text
def test_runtime_provider_detection_corrects_config_mismatch(gm_module, monkeypatch, capsys):
    configure_webhook(gm_module, monkeypatch)
    args = SimpleNamespace(webhook_provider=None, webhook_url="https://ntfy.sh/private-topic", webhook_enabled=None, webhook_profile=None, webhook_events=None, webhook_repo_changes=None, webhook_repo_update_date=None, webhook_daily_contribs=None, webhook_errors=None)
    parser = Mock()
    gm_module.apply_webhook_cli_overrides(args, parser)
    assert gm_module.WEBHOOK_PROVIDER == "ntfy"
    assert "Using ntfy" in capsys.readouterr().out
    parser.error.assert_not_called()
    webhook_post = Mock(return_value=FakeResponse(200))
    monkeypatch.setattr(gm_module.WEBHOOK_SESSION, "post", webhook_post)
    assert gm_module.send_webhook("GitHub title", "New event: push", "profile", force=True) == 0
    request = webhook_post.call_args
    assert request.kwargs["data"] == b"New event: push"
    assert "json" not in request.kwargs


# Verifies hidden webhook setup persists the secret without printing it
def test_set_webhook_url_keeps_secret_hidden(gm_module, monkeypatch, capsys):
    secret = "https://discord.com/api/webhooks/123/private-token"
    with make_test_directory() as directory_name:
        destination = Path(directory_name) / ".env"
        destination.write_text("# keep\nUNRELATED=stay\nWEBHOOK_URL=old-value\n", encoding="utf-8")
        result = gm_module.run_set_webhook_url(env_file=destination, interactive=True, input_func=lambda prompt: "y", getpass_func=lambda prompt: secret)
        output = capsys.readouterr().out
        assert result == str(destination.resolve())
        assert secret not in output
        assert destination.read_text(encoding="utf-8") == f'# keep\nUNRELATED=stay\nWEBHOOK_URL="{secret}"\n'


# Verifies the generated configuration exposes the shared webhook settings
def test_generated_config_contains_webhook_options(gm_module):
    namespace = {}
    exec(gm_module.CONFIG_BLOCK, namespace)
    assert namespace["WEBHOOK_PROVIDER"] == "discord"
    assert namespace["WEBHOOK_USERNAME"] == "GitHub Monitor"
    assert namespace["WEBHOOK_HEADERS"] == {}
    assert namespace["WEBHOOK_TEMPLATE"]["allowed_mentions"] == {"parse": []}
    assert namespace["WEBHOOK_ERROR_NOTIFICATION"] is True
    assert namespace["NTFY_ACCESS_TOKEN"] == ""


# Verifies command help exposes provider, runtime and private setup options
def test_command_help_lists_webhook_options():
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, str(project_root / "github_monitor.py"), "--help"], cwd=project_root, capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert "--webhook-provider {discord,ntfy}" in result.stdout
    assert "--webhook-url URL" in result.stdout
    assert "--set-webhook-url" in result.stdout
    assert "--send-test-webhook" in result.stdout


# Verifies every delivery carries the deadline and refuses a redirect, which could retarget the payload
def test_webhook_delivery_is_bounded_and_does_not_follow_redirects(gm_module, monkeypatch):
    configure_webhook(gm_module, monkeypatch)
    webhook_post = Mock(return_value=FakeResponse())
    monkeypatch.setattr(gm_module.WEBHOOK_SESSION, "post", webhook_post)

    assert gm_module.send_webhook("Title", "Body", "profile") == 0
    request = webhook_post.call_args
    assert request.args == (gm_module.WEBHOOK_URL,)
    assert request.kwargs["timeout"] == gm_module.WEBHOOK_TIMEOUT_SECONDS
    assert request.kwargs["allow_redirects"] is False


# Verifies a destination replaced mid-delivery is refused rather than posted to blindly
def test_webhook_delivery_refuses_a_destination_that_stopped_validating(gm_module, monkeypatch):
    configure_webhook(gm_module, monkeypatch)
    monkeypatch.setattr(gm_module, "WEBHOOK_URL", "http://example.test/hook")
    webhook_post = Mock(return_value=FakeResponse())
    monkeypatch.setattr(gm_module.WEBHOOK_SESSION, "post", webhook_post)

    with pytest.raises(gm_module.req.exceptions.InvalidURL):
        gm_module.post_webhook_request(json={"content": "body"})
    webhook_post.assert_not_called()


# Verifies both test commands carry the subject, title and body shared with the sibling monitors
def test_the_test_messages_use_the_shared_wording(gm_module, monkeypatch):
    email = Mock(return_value=0)
    delivery = Mock(return_value=0)
    monkeypatch.setattr(gm_module, "check_internet", lambda *args, **kwargs: True)
    monkeypatch.setattr(gm_module, "clear_screen", lambda *args, **kwargs: None)
    monkeypatch.setattr(gm_module, "send_email", email)
    monkeypatch.setattr(gm_module, "send_webhook", delivery)
    monkeypatch.setattr(gm_module.signal, "signal", lambda *args: None)

    for flag in ("--send-test-email", "--send-test-webhook"):
        monkeypatch.setattr(gm_module.sys, "argv", ["github_monitor", flag, "--config-file", "none", "--env-file", "none"])
        with pytest.raises(SystemExit) as exit_error:
            gm_module.main()
        assert exit_error.value.code == 0

    assert email.call_args.args[:2] == ("github_monitor: test email", "This test email was sent by --send-test-email. Your SMTP settings work.")
    assert delivery.call_args.args[:2] == ("github_monitor: test webhook", "This test notification was sent by --send-test-webhook. Your webhook settings work.")
