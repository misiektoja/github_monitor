"""Tests for the HTML notification body, its Discord markdown form and its match with the plain text."""

import datetime
import difflib
import html as html_module
import json
import os
import re
from itertools import count
from pathlib import Path

import pytest
import requests

from test_monitoring_loop import OUTAGE, FakeGithub, FakeUser, LoopStopped

USER = "watched"


# Reduces one HTML body back to the text it represents, independently of the module's own converter
def html_to_text(body_html):
    text = re.sub(r"(?is)</?(?:html|head|body)\s*>", "", str(body_html or ""))
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", "", text)
    return html_module.unescape(text)


# Replaces every anchor with its destination, which is what a plain body prints on a bare URL line
def links_as_destinations(line):
    return re.sub(r'(?is)<a\s[^>]*?href="([^"]*)"[^>]*>.*?</a>', r"\1", line)


# Reports whether one HTML line says what its plain counterpart says, whether it links a name or a bare URL
def line_agrees(plain_line, html_line):
    return plain_line in (html_to_text(html_line), html_to_text(links_as_destinations(html_line)))


# Returns what differs between the plain body and the HTML body, empty when their lines and blank lines match
def structural_diff(body, body_html):
    plain_lines = body.split("\n")
    html_lines = re.sub(r"(?is)</?(?:html|head|body)\s*>", "", str(body_html or "")).split("<br>")
    if len(plain_lines) == len(html_lines) and all(line_agrees(*pair) for pair in zip(plain_lines, html_lines, strict=True)):
        return ""
    return "\n".join(difflib.unified_diff(plain_lines, [html_to_text(line) for line in html_lines], fromfile="plain", tofile="html-reduced", lineterm=""))


# Builds the account the loop sees after the change, carrying every profile field a check compares
def changed_user():
    user = FakeUser(USER)
    user.name = "Renamed Person"
    user.location = "Warsaw"
    user.bio = "Writes monitors"
    user.company = "Example Inc"
    user.email = "watched@example.test"
    user.blog = "https://example.test/blog"
    user.updated_at = datetime.datetime(2026, 2, 1, tzinfo=datetime.timezone.utc)
    return user


# Runs the real loop against the scripted lookups and returns every alert it handed to the delivery helper
def alerts_from_loop(gm_module, monkeypatch, tmp_path, lookups, stop_after, visibility=None, blocked=None):
    captured = []
    for name, value in (("SMTP_HOST", "smtp.example.com"), ("SMTP_PORT", 587), ("SMTP_USER", "sender@example.com"), ("SMTP_PASSWORD", "test-password"), ("SENDER_EMAIL", "sender@example.com"), ("RECEIVER_EMAIL", "receiver@example.com"), ("WEBHOOK_PROVIDER", "discord"), ("WEBHOOK_URL", "https://discord.com/api/webhooks/123/private-token")):
        monkeypatch.setattr(gm_module, name, value)
    sleeps = []
    now = [1_800_000_000.0]

    def record(notification_type, subject, body, body_html="", email_enabled=False, webhook_enabled=None, webhook_body=None, webhook_body_html=None):
        captured.append({"type": notification_type, "subject": subject, "body": body, "body_html": body_html, "webhook_body": body if webhook_body is None else webhook_body, "discord": gm_module.html_body_to_discord_markdown(body_html if webhook_body_html is None else webhook_body_html)})
        return bool(email_enabled), bool(webhook_enabled)

    def stopping_sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds
        if len(sleeps) >= stop_after:
            raise LoopStopped

    # Answers the block-status check without reaching GitHub, which is not what these tests drive
    def transport(session, request, **kwargs):
        response = requests.Response()
        response.request = request
        response.url = request.url
        response.status_code = 200
        response._content = json.dumps({"login": "viewer"} if request.url.endswith("/user") else {"data": {"user": {"viewerCanFollow": True}}}).encode()
        return response

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(gm_module.time, "sleep", stopping_sleep)
    monkeypatch.setattr(gm_module.time, "time", lambda: now[0])
    monkeypatch.setattr(gm_module, "GITHUB_CHECK_INTERVAL", 300)
    monkeypatch.setattr(gm_module, "LIVENESS_REMINDER_SECONDS", 30000)
    monkeypatch.setattr(gm_module, "PROFILE_NOTIFICATION", True)
    monkeypatch.setattr(gm_module, "ERROR_NOTIFICATION", True)
    monkeypatch.setattr(gm_module, "WEBHOOK_ENABLED", True)
    monkeypatch.setattr(gm_module, "WEBHOOK_ERROR_NOTIFICATION", True)
    monkeypatch.setattr(gm_module, "TRACK_REPOS_CHANGES", False)
    monkeypatch.setattr(gm_module, "TRACK_CONTRIB_CHANGES", False)
    monkeypatch.setattr(gm_module, "GET_ALL_REPOS", False)
    monkeypatch.setattr(gm_module, "DEBUG_MODE", False)
    monkeypatch.setattr(gm_module, "VERBOSE_MODE", False)
    monkeypatch.setattr(requests.Session, "send", transport)
    monkeypatch.setattr(gm_module, "is_profile_public", visibility or (lambda *arguments, **keywords: True))
    if blocked is not None:
        monkeypatch.setattr(gm_module, "is_blocked_by", blocked)
    monkeypatch.setattr(gm_module, "send_notification_channels", record)
    monkeypatch.setattr(gm_module, "create_github_client", lambda *arguments, **keywords: FakeGithub(lookups))
    with pytest.raises(LoopStopped):
        gm_module.github_monitor_user(USER, "")
    return captured


@pytest.fixture
# Every alert a timeline covering the profile changes, a visibility flip, a block and an outage produces
def timeline_alerts(gm_module, monkeypatch, tmp_path, capsys):
    visibility_checks = count(1)
    blocked_checks = count(1)
    alerts = alerts_from_loop(
        gm_module, monkeypatch, tmp_path,
        [changed_user(), changed_user(), changed_user(), OUTAGE],
        5,
        visibility=lambda *arguments, **keywords: next(visibility_checks) < 4,
        blocked=lambda *arguments, **keywords: next(blocked_checks) >= 3,
    )
    capsys.readouterr()
    return alerts


# Verifies a value taken from GitHub is escaped before it reaches the HTML body
def test_untrusted_text_is_escaped(gm_module):
    assert gm_module.html_text("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"
    assert gm_module.html_text("line\nbreak") == "line<br>break"


# Verifies a bare URL in an alert becomes a link while one already inside an attribute is left alone
def test_bare_urls_are_linked_once(gm_module):
    assert gm_module.html_autolink_urls("Guide: https://example.test/a") == 'Guide: <a href="https://example.test/a">https://example.test/a</a>'
    assert gm_module.html_autolink_urls('<a href="https://example.test/a">x</a>') == '<a href="https://example.test/a">x</a>'


# Verifies the Discord body carries the email's emphasis and links instead of raw markup
def test_discord_markdown_mirrors_the_html_body(gm_module):
    body_html = f'<html><head></head><body>GitHub user <b>{USER}</b> bio has changed<br><br>Guide: <a href="https://example.test/a">docs</a></body></html>'

    assert gm_module.html_body_to_discord_markdown(body_html) == f"GitHub user **{USER}** bio has changed\n\nGuide: [docs](https://example.test/a)"


# Verifies the failure alert bolds its summary and the two values that say how bad the outage is
def test_the_failure_alert_bolds_its_summary_and_outage_fields(gm_module):
    advice = gm_module.make_recovery_advice("github.unavailable", "GitHub is unreachable", gm_module.recovery_fix_with_guide("Retry later", "https://example.test/guide"), True)

    rendered = gm_module.recovery_alert_body_html(advice, 60, failed_checks=2, failing_since=1800000000)

    assert rendered.startswith("<html><head></head><body><b>GitHub is unreachable</b><br><br>")
    assert 'Guide: <a href="https://example.test/guide">' in rendered
    assert "Failed checks in a row: <b>2</b>" in rendered
    assert "Failing since: <b>" in rendered
    # The retry delay is configured rather than observed, so it carries no emphasis
    assert "Next retry in: 1 minute" in rendered
    assert rendered.endswith("</body></html>")


# Verifies the timeline reaches both alert types, so the structural check is not silently narrow
def test_the_timeline_covers_the_profile_and_failure_alerts(timeline_alerts):
    assert {alert["type"] for alert in timeline_alerts} == {"profile", "error"}


# Verifies the timeline reaches the profile fields that had no HTML body of their own
def test_the_timeline_covers_the_fields_without_their_own_html_body(timeline_alerts):
    subjects = " | ".join(alert["subject"] for alert in timeline_alerts)

    assert "blog URL has changed" in subjects
    assert "account has been updated" in subjects
    assert "changed profile visibility" in subjects
    assert "blocked you" in subjects


# Verifies every alert carries an HTML body next to its plain one
def test_every_alert_has_an_html_body(timeline_alerts):
    assert [alert["subject"] for alert in timeline_alerts if not alert["body_html"]] == []


# Verifies each HTML body reduces back to its plain body, so no line break was added or lost
def test_html_bodies_match_the_plain_text(timeline_alerts):
    mismatches = [f"{alert['type']}: {alert['subject']}\n{structural_diff(alert['body'], alert['body_html'])}" for alert in timeline_alerts if structural_diff(alert["body"], alert["body_html"])]

    assert mismatches == []


# Verifies every HTML body is one complete document, so no fragment reaches a mail client unwrapped
def test_html_bodies_are_complete_documents(timeline_alerts):
    for alert in timeline_alerts:
        assert alert["body_html"].startswith("<html><head></head><body>")
        assert alert["body_html"].endswith("</body></html>")


# Verifies the Discord body keeps the wording the ntfy body carries once its markers are removed
def test_discord_bodies_keep_the_plain_wording(timeline_alerts):
    for alert in timeline_alerts:
        stripped = re.sub(r"\[([^\]]*)\]\((?:[^)]*)\)", r"\1", alert["discord"]).replace("**", "").replace("*", "")

        assert stripped == alert["webhook_body"].strip()


# Verifies the watched account is the bold subject of every alert that names it
def test_alerts_bold_the_account_they_name(timeline_alerts):
    for alert in timeline_alerts:
        if alert["type"] == "profile":
            assert f"<b>{USER}</b>" in alert["body_html"]


# Writes the captured alerts as JSON when PREVIEW_ALERTS_JSON names a destination, so a preview tool can render them
@pytest.mark.skipif(not os.environ.get("PREVIEW_ALERTS_JSON"), reason="set PREVIEW_ALERTS_JSON to dump the alerts")
def test_dump_the_alerts_for_a_preview(timeline_alerts):
    Path(os.environ["PREVIEW_ALERTS_JSON"]).write_text(json.dumps(timeline_alerts, indent=2), encoding="utf-8")
