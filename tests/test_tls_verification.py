"""Tests for VERIFY_SSL: which requests honour it, what is reported while it is off and its shipped default."""

import ast
import ssl
from pathlib import Path
from types import SimpleNamespace

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = (PROJECT_ROOT / "github_monitor.py").read_text(encoding="utf-8")
WEBHOOK_URL = "https://discord.com/api/webhooks/123456789/aVeryLongWebhookTokenValue"
TOKEN = "github_pat_private_value"


# Answers None for every option doctor reads, so a test only sets the ones it cares about
class DoctorArgs:
    def __init__(self, **overrides):
        self.__dict__.update(overrides)

    def __getattr__(self, name):
        return None


# Records the keyword arguments of every request made through it and answers with a success the caller accepts
class RecordingRequests:
    def __init__(self, payload=None):
        self.calls = []
        self.payload = {"login": "octocat"} if payload is None else payload

    # Stands in for requests.get, requests.post and Session.post alike
    def __call__(self, url=None, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return SimpleNamespace(status_code=200, ok=True, headers={}, text="", reason="OK", json=lambda: self.payload)

    # Returns the TLS setting the single recorded request carried
    def verified(self):
        assert len(self.calls) == 1, f"expected one request, recorded {len(self.calls)}"
        return self.calls[0].get("verify")


@pytest.fixture
# Restores the setting after each test, since it is a module global the whole tool reads
def tls_setting(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module, "VERIFY_SSL", gm_module.VERIFY_SSL)
    return monkeypatch


@pytest.mark.parametrize("verify", [True, False])
# Verifies the connectivity check carries the configured setting rather than the requests library default
def test_the_connectivity_check_honours_the_setting(gm_module, tls_setting, verify):
    recorder = RecordingRequests()
    tls_setting.setattr(gm_module, "VERIFY_SSL", verify)
    tls_setting.setattr(gm_module.req, "get", recorder)

    assert gm_module.check_internet("https://github.example/health", 5) is True
    assert recorder.verified() is verify


@pytest.mark.parametrize("verify", [True, False])
# Verifies the token check carries the setting, since it reaches GitHub outside the PyGithub client
def test_the_token_check_honours_the_setting(gm_module, tls_setting, verify):
    recorder = RecordingRequests()
    tls_setting.setattr(gm_module, "VERIFY_SSL", verify)

    assert gm_module.validate_github_token(TOKEN, "https://api.github.com", request_get=recorder) == "octocat"
    assert recorder.verified() is verify


@pytest.mark.parametrize("verify", [True, False])
# Verifies the profile page read carries the setting, which is the one request that leaves the API host
def test_the_profile_page_read_honours_the_setting(gm_module, tls_setting, verify):
    recorder = RecordingRequests()
    tls_setting.setattr(gm_module, "VERIFY_SSL", verify)
    tls_setting.setattr(gm_module.req, "get", recorder)

    gm_module.has_private_banner("octocat")

    assert recorder.verified() is verify


@pytest.mark.parametrize("verify", [True, False])
# Verifies webhook deliveries carry the setting, so one channel cannot skip a check the others make
def test_the_webhook_delivery_honours_the_setting(gm_module, tls_setting, verify):
    recorder = RecordingRequests()
    tls_setting.setattr(gm_module, "VERIFY_SSL", verify)
    tls_setting.setattr(gm_module, "WEBHOOK_SESSION", SimpleNamespace(post=recorder))
    tls_setting.setattr(gm_module, "WEBHOOK_URL", WEBHOOK_URL)

    gm_module.post_webhook_request(json={"content": "hello"})

    assert recorder.verified() is verify


@pytest.mark.parametrize("verify", [True, False])
# Verifies the PyGithub client is handed the setting, since it owns the session every API call uses
def test_the_pygithub_client_honours_the_setting(gm_module, tls_setting, verify):
    built = {}
    tls_setting.setattr(gm_module, "VERIFY_SSL", verify)
    tls_setting.setattr(gm_module, "Github", lambda **kwargs: built.update(kwargs) or SimpleNamespace(**kwargs))
    tls_setting.setattr(gm_module, "Auth", SimpleNamespace(Token=lambda token: token))

    gm_module.create_github_client("test")

    assert built["verify"] is verify


# Every outbound request in the module, including the ones a test can replace, so no call site quietly skips the setting


@pytest.mark.parametrize("verify", [True, False])
# Verifies the SMTP handshake follows the setting, so email is not the one channel that keeps checking certificates
def test_the_smtp_context_honours_the_setting(gm_module, tls_setting, verify):
    tls_setting.setattr(gm_module, "VERIFY_SSL", verify)

    context = gm_module.smtp_ssl_context()

    assert context.check_hostname is verify
    assert (context.verify_mode == ssl.CERT_REQUIRED) is verify


# Verifies no SMTP call site builds its own context, which would keep that one connection verifying while the setting is off
def test_only_the_shared_helper_builds_an_smtp_context():
    assert SOURCE.count("ssl.create_default_context()") == 1


@pytest.mark.parametrize("verify, silenced", [(True, False), (False, True)])
# Verifies the certificate warning is silenced only once the reader has chosen to switch verification off
def test_the_certificate_warning_is_silenced_only_while_verification_is_off(gm_module, tls_setting, verify, silenced):
    disabled = []
    tls_setting.setattr(gm_module, "VERIFY_SSL", verify)
    tls_setting.setattr(gm_module.urllib3, "disable_warnings", lambda category: disabled.append(category))

    gm_module.apply_tls_verification_setting()

    assert bool(disabled) is silenced


# Returns the doctor's TLS row for the current setting
def tls_doctor_check(gm_module):
    report = gm_module.DoctorReport(target_name="octocat")
    gm_module.doctor_check_configuration(report, DoctorArgs(env_file="none", config_file="none"), object())
    return next(check for check in report.checks if "TLS" in check.label)


# Verifies the doctor passes the setting silently while it is on
def test_the_doctor_passes_while_verification_is_on(gm_module, tls_setting):
    tls_setting.setattr(gm_module, "VERIFY_SSL", True)

    check = tls_doctor_check(gm_module)

    assert (check.status, check.advice) == ("PASS", None)


# Verifies the doctor warns while verification is off and names the setting to change and where it is documented
def test_the_doctor_warns_while_verification_is_off(gm_module, tls_setting):
    tls_setting.setattr(gm_module, "VERIFY_SSL", False)

    check = tls_doctor_check(gm_module)

    assert check.status == "WARN"
    assert "VERIFY_SSL" in check.detail
    assert "VERIFY_SSL" in check.advice.fix
    assert check.advice.fix.endswith(f"\nGuide: {gm_module.TLS_GUIDE_URL}")


@pytest.mark.parametrize("verify, concise", [(True, False), (False, True)])
# Verifies the summary always records the setting and puts it in front of the reader only when it is off
def test_the_summary_promotes_the_row_only_while_verification_is_off(gm_module, tls_setting, verify, concise):
    tls_setting.setattr(gm_module, "VERIFY_SSL", verify)

    row = next(item for item in gm_module.build_startup_summary("octocat", None, None, None) if item.label == "TLS verification")

    assert (row.full, row.concise) == (True, concise)
    assert row.value.startswith("On" if verify else "Off")


# Verifies certificates are verified unless the reader turns that off, in the shipped config and the fallback alike
def test_certificates_are_verified_by_default(gm_module):
    shipped = gm_module.parse_config_content(gm_module.CONFIG_BLOCK, "<built-in-config>")

    assert shipped["VERIFY_SSL"] is True
    assert gm_module.VERIFY_SSL is True


HTTP_METHODS = frozenset(("get", "post", "put", "patch", "delete", "head", "options", "request"))
# The expressions that carry the TLS decision, so a call passing anything else is a second opinion
VERIFY_ARGUMENTS = frozenset(("VERIFY_SSL",))
# A guard against the sweep silently matching nothing after a rename: the tool has 7 call sites today
MINIMUM_HTTP_CALL_SITES = 7


# Returns every name the module binds to a requests session, so a session added later is swept without editing this
def session_receivers():
    return {node.targets[0].id for node in ast.walk(ast.parse(SOURCE)) if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and isinstance(node.value, ast.Call) and ast.unparse(node.value.func).endswith("Session")}


# Returns every outbound HTTP call in the module as a line number paired with its keyword arguments
def http_call_sites():
    receivers = {"req", "requests"} | session_receivers()
    for node in ast.walk(ast.parse(SOURCE)):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        receiver = node.func.value
        if node.func.attr in HTTP_METHODS and isinstance(receiver, ast.Name) and receiver.id in receivers:
            yield node.lineno, {keyword.arg: keyword.value for keyword in node.keywords}


# Verifies every outbound request passes the setting, so a call site added later cannot keep verifying while it is off
def test_every_outbound_request_passes_the_setting():
    calls = list(http_call_sites())

    assert len(calls) >= MINIMUM_HTTP_CALL_SITES, f"the sweep found {len(calls)} HTTP calls, so it no longer matches how requests are made"
    missing = [line for line, keywords in calls if "verify" not in keywords or ast.unparse(keywords["verify"]) not in VERIFY_ARGUMENTS]
    assert not missing, f"github_monitor.py lines {missing} make an HTTP call that does not pass the TLS setting"


# Verifies every outbound request carries a deadline, since a call without one hangs the monitoring loop indefinitely
def test_every_outbound_request_carries_a_deadline():
    # A call forwarding **kwargs takes its deadline from the helper that fills them in, which is not readable here
    missing = [line for line, keywords in http_call_sites() if "timeout" not in keywords and None not in keywords]

    assert not missing, f"github_monitor.py lines {missing} make an HTTP call without a timeout"
