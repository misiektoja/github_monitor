"""Offline tests for private GitHub token validation and persistence."""

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = PROJECT_ROOT / "local" / "github_token_test_artifacts"


# Creates one disposable GitHub token test directory under the project local directory
def make_test_directory():
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=ARTIFACT_ROOT)


# Stores one requests-compatible GitHub token validation response
class FakeResponse:
    # Initializes one response with a status and optional JSON payload
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self.payload = payload

    # Returns the configured JSON payload
    def json(self):
        return self.payload


# Verifies successful token validation uses the configured API without redirects
def test_validate_github_token_returns_authenticated_login(gm_module):
    secret = "github_pat_private"
    request_get = Mock(return_value=FakeResponse(200, {"login": "octocat"}))
    assert gm_module.validate_github_token(secret, "https://github.example/api/v3", request_get=request_get) == "octocat"
    request_get.assert_called_once_with("https://github.example/api/v3/user", headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {secret}", "User-Agent": f"GitHubMonitor/{gm_module.VERSION}"}, timeout=10, allow_redirects=False, verify=True)


@pytest.mark.parametrize("api_url", ["http://github.example/api/v3", "https://user:password@github.example/api/v3", "https://github.example/api/v3?token=value", "not-a-url", ""])
# Verifies private token validation rejects unsafe or malformed API destinations
def test_validate_github_token_rejects_unsafe_api_urls(gm_module, api_url):
    request_get = Mock(side_effect=AssertionError("network request attempted"))
    with pytest.raises(gm_module.GitHubTokenConfigurationError, match="GITHUB_API_URL"):
        gm_module.validate_github_token("github_pat_private", api_url, request_get=request_get)
    request_get.assert_not_called()


# Verifies validation network errors cannot expose the entered token
def test_validate_github_token_hides_network_error_details(gm_module):
    secret = "github_pat_network_private"
    request_get = Mock(side_effect=gm_module.req.ConnectionError(f"request failed for {secret}"))
    with pytest.raises(gm_module.GitHubTokenConfigurationError, match="Could not reach") as error:
        gm_module.validate_github_token(secret, "https://api.github.example", request_get=request_get)
    assert secret not in str(error.value)


# Verifies token setup validates before replacing only the intended dotenv assignment
def test_set_github_token_validates_then_persists_without_leak(gm_module, monkeypatch, capsys):
    secret = "github_pat_private"
    request_get = Mock(return_value=FakeResponse(200, {"login": "octocat"}))
    monkeypatch.setattr(gm_module.req, "get", request_get)
    with make_test_directory() as directory_name:
        destination = Path(directory_name) / ".env"
        destination.write_text("# keep\nUNRELATED=stay\nGITHUB_TOKEN=old-value\n", encoding="utf-8")
        result = gm_module.run_set_github_token(env_file=destination, interactive=True, input_func=lambda prompt: "y", getpass_func=lambda prompt: secret)
        output = capsys.readouterr().out
        assert result == str(destination.resolve())
        assert secret not in output
        assert "octocat" in output
        assert destination.read_text(encoding="utf-8") == f'# keep\nUNRELATED=stay\nGITHUB_TOKEN="{secret}"\n'
    assert request_get.call_count == 1


# Verifies a rejected token never changes the dotenv file or appears in diagnostics
def test_set_github_token_rejection_preserves_dotenv(gm_module, monkeypatch, capsys):
    secret = "github_pat_rejected_private"
    monkeypatch.setattr(gm_module.req, "get", Mock(return_value=FakeResponse(401, {"message": secret})))
    with make_test_directory() as directory_name:
        destination = Path(directory_name) / ".env"
        original = "# keep\nGITHUB_TOKEN=old-value\n"
        destination.write_text(original, encoding="utf-8")
        with pytest.raises(gm_module.GitHubTokenConfigurationError, match="GitHub rejected") as error:
            gm_module.run_set_github_token(env_file=destination, interactive=True, input_func=lambda prompt: "y", getpass_func=lambda prompt: secret)
        output = capsys.readouterr().out
        assert destination.read_text(encoding="utf-8") == original
        assert secret not in output
        assert secret not in str(error.value)


# Verifies private GitHub token entry requires an interactive terminal
def test_set_github_token_requires_interactive_terminal(gm_module):
    with pytest.raises(gm_module.GitHubTokenConfigurationError, match="interactive terminal"):
        gm_module.run_set_github_token(interactive=False, getpass_func=Mock(side_effect=AssertionError("prompted")))


# Verifies generated configuration recommends hidden validated token setup
def test_config_block_prefers_private_github_token_setup(gm_module):
    assert "Preferred method:" in gm_module.CONFIG_BLOCK
    assert "github_monitor --set-github-token" in gm_module.CONFIG_BLOCK
    assert "Fallback methods:" in gm_module.CONFIG_BLOCK


# Verifies command help exposes the private GitHub token setup action
def test_command_help_lists_private_github_token_setup():
    result = subprocess.run([sys.executable, str(PROJECT_ROOT / "github_monitor.py"), "--help"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert "--set-github-token" in result.stdout
    assert "hidden prompt" in result.stdout


# Verifies private token setup cannot be combined with a shell-visible token value
def test_private_token_setup_rejects_runtime_token_argument():
    result = subprocess.run([sys.executable, str(PROJECT_ROOT / "github_monitor.py"), "--set-github-token", "--github-token", "github_pat_private"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 2
    assert "not allowed with argument" in result.stderr
