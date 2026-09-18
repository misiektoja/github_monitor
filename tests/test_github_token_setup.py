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
    assert "--set-github-token cannot be combined with -t/--github-token" in result.stderr


PROGRESS_LINES = (
    "* Checking the entered GitHub token before changing the dotenv file ...",
    "  Checking the token with GitHub ...",
)


# Verifies each wait on a remote service is announced with the wording every sibling monitor uses
@pytest.mark.parametrize("line", PROGRESS_LINES)
def test_the_progress_lines_use_the_shared_checking_wording(line):
    assert line in (PROJECT_ROOT / "github_monitor.py").read_text(encoding="utf-8"), line


# Verifies the replace question names the secret the way every sibling one-shot command names its own
def test_set_github_token_replace_question_uses_the_shared_wording(gm_module, monkeypatch):
    monkeypatch.setattr(gm_module.req, "get", Mock(return_value=FakeResponse(200, {"login": "octocat"})))
    with make_test_directory() as directory_name:
        destination = Path(directory_name) / ".env"
        destination.write_text("GITHUB_TOKEN=old-value\n", encoding="utf-8")
        prompts = []

        gm_module.run_set_github_token(env_file=destination, interactive=True, input_func=lambda prompt: prompts.append(prompt) or "y", getpass_func=lambda prompt: "github_pat_private")

        assert prompts == [f"Replace the saved GitHub token in '{destination.resolve()}'? [y/N]: "]


# Verifies a secret cleared by its owner leaves the file rather than staying behind as an empty value
def test_a_cleared_secret_is_removed_rather_than_emptied(gm_module, tmp_path):
    destination = tmp_path / ".env-monitor"
    destination.write_text('UNRELATED=stay\nNTFY_ACCESS_TOKEN="tk_old"\n', encoding="utf-8")

    gm_module.update_dotenv_file(destination, {"NTFY_ACCESS_TOKEN": ""})

    assert destination.read_text(encoding="utf-8") == "UNRELATED=stay\n"


# Verifies a saved value written across several lines is replaced whole, since replacing only its first
# line left the rest of the old secret behind and the next run could not parse what it wrote
def test_a_multiline_secret_is_replaced_whole(gm_module, tmp_path):
    destination = tmp_path / ".env"
    destination.write_text('NTFY_ACCESS_TOKEN="first line\nsecond line"\nOTHER=keep\n', encoding="utf-8")

    gm_module.update_dotenv_file(destination, {"NTFY_ACCESS_TOKEN": "replacement"})

    assert destination.read_text(encoding="utf-8") == 'NTFY_ACCESS_TOKEN="replacement"\nOTHER=keep\n'


# Verifies clearing such a value removes all of it, for the same reason
def test_a_cleared_multiline_secret_leaves_nothing_behind(gm_module, tmp_path):
    destination = tmp_path / ".env"
    destination.write_text('NTFY_ACCESS_TOKEN="first line\nsecond line"\nOTHER=keep\n', encoding="utf-8")

    gm_module.update_dotenv_file(destination, {"NTFY_ACCESS_TOKEN": ""})

    assert destination.read_text(encoding="utf-8") == "OTHER=keep\n"


# Verifies clearing a secret the file never held does not add an empty line for it
def test_clearing_an_absent_secret_writes_nothing(gm_module, tmp_path):
    destination = tmp_path / ".env-monitor"
    destination.write_text("UNRELATED=stay\n", encoding="utf-8")

    gm_module.update_dotenv_file(destination, {"NTFY_ACCESS_TOKEN": ""})

    assert destination.read_text(encoding="utf-8") == "UNRELATED=stay\n"


# Verifies an exported assignment is removed too, so a cleared secret cannot survive in the environment
def test_a_cleared_exported_secret_is_removed(gm_module, tmp_path):
    destination = tmp_path / ".env-monitor"
    destination.write_text('export NTFY_ACCESS_TOKEN="tk_old"\nUNRELATED=stay\n', encoding="utf-8")

    gm_module.update_dotenv_file(destination, {"NTFY_ACCESS_TOKEN": ""})

    assert destination.read_text(encoding="utf-8") == "UNRELATED=stay\n"


# Verifies an assignment the owner exported keeps its export, since dropping it changes what a shell sourcing the file exports
def test_an_exported_assignment_keeps_its_export(tmp_path, gm_module):
    destination = tmp_path / ".env"
    destination.write_text('export SMTP_PASSWORD="old"\nOTHER=keep\n', encoding="utf-8")

    gm_module.update_dotenv_file(destination, {"SMTP_PASSWORD": "new"})

    assert destination.read_text(encoding="utf-8") == 'export SMTP_PASSWORD="new"\nOTHER=keep\n'


# Verifies a line break inside a value is escaped rather than written through, since a raw one would split the assignment
def test_a_line_break_in_a_value_cannot_split_the_assignment(tmp_path, gm_module):
    destination = tmp_path / ".env"

    gm_module.update_dotenv_file(destination, {"SMTP_PASSWORD": "one\ntwo"})

    assert destination.read_text(encoding="utf-8") == 'SMTP_PASSWORD="one\\ntwo"\n'


# Verifies the writer refuses a key this tool does not ship, so a typo cannot put an unknown name in the private file
def test_the_writer_refuses_a_key_this_tool_does_not_ship(tmp_path, gm_module):
    with pytest.raises(ValueError):
        gm_module.update_dotenv_file(tmp_path / ".env", {"NOT_A_SECRET": "value"})


# Verifies the writer refuses a value that is not text, so a mistyped caller fails before the file is touched
def test_the_writer_refuses_a_value_that_is_not_text(tmp_path, gm_module):
    with pytest.raises(TypeError):
        gm_module.update_dotenv_file(tmp_path / ".env", {"SMTP_PASSWORD": 1234})
