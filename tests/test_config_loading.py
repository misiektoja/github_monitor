"""Tests that a config file is read as data and never executed."""

import re
from pathlib import Path
import pytest

import github_monitor as monitor


HOSTILE_CONTENT = (
    "import os\n"
    "os.environ['GITHUB_CONFIG_EXEC_PROBE'] = 'yes'\n",
    "__import__('os').system('touch pwned')\n",
    "CHECK_INTERNET_TIMEOUT = __import__('os').getpid()\n",
    "def helper():\n    return 1\n",
    "for index in range(3):\n    pass\n",
)


# Returns a setting name the built-in configuration template actually defines
def first_allowed_setting():
    return sorted(monitor._config_allowed_names())[0]


@pytest.mark.parametrize("content", HOSTILE_CONTENT)
# Verifies executable content is refused without running, so a config in the working directory cannot run code
def test_executable_config_content_is_refused_without_running(tmp_path, monkeypatch, content):
    monkeypatch.delenv("GITHUB_CONFIG_EXEC_PROBE", raising=False)
    config = tmp_path / "hostile.conf"
    config.write_text(content, encoding="utf-8")
    namespace = {}

    assert monitor.load_config_file(config, namespace=namespace, report_errors=False) is False
    assert namespace == {}

    import os

    assert os.environ.get("GITHUB_CONFIG_EXEC_PROBE") is None
    assert not (tmp_path / "pwned").exists()


# Verifies a plain literal assignment still reaches the namespace
def test_literal_settings_are_applied(tmp_path):
    setting = first_allowed_setting()
    config = tmp_path / "good.conf"
    config.write_text(f"{setting} = 123\n", encoding="utf-8")
    namespace = {}

    assert monitor.load_config_file(config, namespace=namespace, report_errors=False) is True
    assert namespace[setting] == 123


# Verifies one setting may reuse another, which the built-in template relies on
def test_a_setting_may_reference_another_setting(tmp_path):
    allowed = sorted(monitor._config_allowed_names())
    source, target = allowed[0], allowed[1]
    config = tmp_path / "reference.conf"
    config.write_text(f'{source} = "shared"\n{target} = {source}\n', encoding="utf-8")
    namespace = {}

    assert monitor.load_config_file(config, namespace=namespace, report_errors=False) is True
    assert namespace[target] == "shared"


# Verifies a setting this version does not define is named instead of silently landing in the namespace
def test_unknown_setting_is_rejected(tmp_path):
    config = tmp_path / "unknown.conf"
    config.write_text("NOT_A_REAL_SETTING = 1\n", encoding="utf-8")
    namespace = {}

    assert monitor.load_config_file(config, namespace=namespace, report_errors=False) is False
    assert "NOT_A_REAL_SETTING" not in namespace


# Verifies a rejected file leaves the namespace untouched rather than applying the lines before the bad one
def test_a_rejected_config_applies_nothing(tmp_path):
    setting = first_allowed_setting()
    config = tmp_path / "partial.conf"
    config.write_text(f"{setting} = 5\nimport os\n", encoding="utf-8")
    namespace = {}

    assert monitor.load_config_file(config, namespace=namespace, report_errors=False) is False
    assert namespace == {}


# Verifies the built-in template and the config the tool generates both survive the parser
def test_generated_configuration_round_trips():
    monitor.validate_config_content(monitor.CONFIG_BLOCK, "<built-in>")


# Verifies a file that is not valid UTF-8 is reported rather than raising
def test_invalid_encoding_is_reported(tmp_path):
    config = tmp_path / "binary.conf"
    config.write_bytes(b"\xff\xfe\x00bad\n")

    assert monitor.load_config_file(config, namespace={}, report_errors=False) is False


# Verifies an existing config is never replaced without consent, since the tool's own advice names this command
def test_generated_config_refuses_to_replace_without_consent(tmp_path):
    config = tmp_path / "existing.conf"
    config.write_text("GITHUB_CHECK_INTERVAL = 1200\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="--force"):
        monitor.write_generated_config(config, "GITHUB_CHECK_INTERVAL = 60\n", interactive=False)
    assert config.read_text(encoding="utf-8") == "GITHUB_CHECK_INTERVAL = 1200\n"

    assert monitor.write_generated_config(config, "GITHUB_CHECK_INTERVAL = 60\n", interactive=True, input_func=lambda prompt: "n") == (None, False)
    assert config.read_text(encoding="utf-8") == "GITHUB_CHECK_INTERVAL = 1200\n"


# Verifies an approved replacement keeps the previous content in a backup instead of destroying it
def test_generated_config_backs_up_the_file_it_replaces(tmp_path):
    config = tmp_path / "existing.conf"
    config.write_text("GITHUB_CHECK_INTERVAL = 1200\n", encoding="utf-8")

    backup_path, written = monitor.write_generated_config(config, "GITHUB_CHECK_INTERVAL = 60\n", force=True)

    assert written is True
    assert config.read_text(encoding="utf-8") == "GITHUB_CHECK_INTERVAL = 60\n"
    assert backup_path is not None and Path(backup_path).read_text(encoding="utf-8") == "GITHUB_CHECK_INTERVAL = 1200\n"


# Verifies a fresh destination needs no approval and no backup
def test_generated_config_writes_a_new_destination_directly(tmp_path):
    config = tmp_path / "fresh.conf"

    backup_path, written = monitor.write_generated_config(config, "GITHUB_CHECK_INTERVAL = 60\n", interactive=False)

    assert (backup_path, written) == (None, True)
    assert config.read_text(encoding="utf-8") == "GITHUB_CHECK_INTERVAL = 60\n"


# The retired set is empty today, so these prove the mechanism works before the first real retirement needs it
def test_a_retired_setting_is_ignored_instead_of_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(monitor, "RETIRED_CONFIG_SETTINGS", frozenset(("OBSOLETE_TEST_SETTING",)))
    setting = first_allowed_setting()
    config = tmp_path / "retired.conf"
    config.write_text(f'OBSOLETE_TEST_SETTING = "gone"\n{setting} = 7\n', encoding="utf-8")
    namespace = {}
    retired_names = set()

    assert monitor.load_config_file(config, namespace=namespace, report_errors=False, retired_names_out=retired_names) is True
    assert namespace[setting] == 7
    assert "OBSOLETE_TEST_SETTING" not in namespace
    assert retired_names == {"OBSOLETE_TEST_SETTING"}
    assert "OBSOLETE_TEST_SETTING" in monitor.describe_retired_settings(retired_names, "'retired.conf'")


# Verifies a name that was never retired is still rejected, so the tolerance stays limited to the declared set
def test_an_unlisted_unknown_setting_is_still_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(monitor, "RETIRED_CONFIG_SETTINGS", frozenset(("OBSOLETE_TEST_SETTING",)))
    config = tmp_path / "unlisted.conf"
    config.write_text("SOME_OTHER_REMOVED_SETTING = 1\n", encoding="utf-8")

    assert monitor.load_config_file(config, namespace={}, report_errors=False) is False


# A parent path that is a file is a write failure, not an existing config, so the advice must not say --force
def test_a_file_in_the_way_of_the_parent_directory_is_not_an_existing_config(tmp_path):
    blocker = tmp_path / "configs"
    blocker.write_text("not a directory\n", encoding="utf-8")

    with pytest.raises(OSError) as raised:
        monitor.write_generated_config(blocker / "github_monitor.conf", "SMTP_PORT = 587\n", interactive=False)

    assert not isinstance(raised.value, monitor.ConfigExistsError)
    assert blocker.read_text(encoding="utf-8") == "not a directory\n"


# Refusing to replace a config without a terminal is its own error, so the generate-config path can tell it apart
def test_refusing_to_replace_a_config_without_a_terminal_raises_its_own_error(tmp_path):
    destination = tmp_path / "github_monitor.conf"
    destination.write_text("SMTP_PORT = 587\n", encoding="utf-8")

    with pytest.raises(monitor.ConfigExistsError):
        monitor.write_generated_config(destination, "SMTP_PORT = 465\n", interactive=False)

    assert destination.read_text(encoding="utf-8") == "SMTP_PORT = 587\n"


# The part of the configuration template every sibling monitor shares, in the order they all use
SHARED_SETTING_ORDER = ("WEBHOOK_HEADERS", "NTFY_ACCESS_TOKEN", "WEBHOOK_TEMPLATE", "WEBHOOK_TRANSFORMS", "DISABLE_LOGGING", "ASCII_LOG_SEPARATORS", "TRUNCATE_CHARS", "CLEAR_SCREEN", "COLORED_OUTPUT", "COLOR_THEME", "VERBOSE_MODE", "DEBUG_MODE", "DELIVERY_CONFIRMATIONS")


# Returns every setting the built-in template declares, in template order, including the commented theme block
def template_setting_order(module):
    order = []
    for line in module.CONFIG_BLOCK.split("\n"):
        match = re.match(r"^([A-Z][A-Z0-9_]*)\s*[:=]", line) or re.match(r"^# ([A-Z][A-Z0-9_]*)\s*=", line)
        if match and match.group(1) not in order:
            order.append(match.group(1))
    return order


# Verifies the template keeps the order shared with the sibling monitors, so one tool's config reads like the next
def test_the_template_keeps_the_shared_setting_order():
    order = template_setting_order(monitor)

    assert set(SHARED_SETTING_ORDER) <= set(order), f"the template no longer declares {sorted(set(SHARED_SETTING_ORDER) - set(order))}"
    assert [name for name in order if name in SHARED_SETTING_ORDER] == list(SHARED_SETTING_ORDER)


# Verifies the linter defaults below the template repeat it in the same order, so a setting cannot drift or be filed twice
def test_the_linter_defaults_follow_the_template_order():
    source = Path(monitor.__file__).read_text(encoding="utf-8").split("\n")
    start = next(index for index, line in enumerate(source) if line.startswith("# Do not change values below")) + 1
    end = next(index for index, line in enumerate(source) if line.startswith("exec(CONFIG_BLOCK"))
    order = template_setting_order(monitor)
    mirrored = [match.group(1) for match in (re.match(r"^([A-Z][A-Z0-9_]*)\s*[:=]", line) for line in source[start:end]) if match and match.group(1) in set(order)]

    assert len(mirrored) == len(set(mirrored)), "a setting is repeated in the linter defaults"
    assert mirrored == [name for name in order if name in set(mirrored)]
