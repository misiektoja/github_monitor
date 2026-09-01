"""Terminal colour contract tests for the coloured output layer."""

import io
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

import github_monitor as monitor


CHANGE_REPORT_LINES = ("* Daily contributions changed for user octocat from 98 to 100 (+2)!", "* Repo 'hello world': number of stars changed from 10 to 12 (+2)", "* Repo 'emoji tools 🛠️' update date changed after 2 days")


# Enables colour with a deterministic style map
@pytest.fixture
def colored(monkeypatch):
    styles = {name: monitor._build_ansi_sequence(value) for name, value in monitor.DEFAULT_COLOR_THEME.items() if monitor._build_ansi_sequence(value)}
    monkeypatch.setattr(monitor, "COLOR_ENABLED", True)
    monkeypatch.setattr(monitor, "_COLOR_STYLES", styles)
    return styles


# Verifies the config template matches the built-in theme
def test_config_template_theme_matches_the_built_in_theme():
    values = monitor.parse_config_content(monitor.CONFIG_BLOCK, "<built-in-config>")
    assert values["COLORED_OUTPUT"] is True
    assert values["COLOR_THEME"] == monitor.DEFAULT_COLOR_THEME


# Verifies every shipped style resolves or is deliberately empty
def test_default_theme_styles_all_resolve():
    for name, value in monitor.DEFAULT_COLOR_THEME.items():
        assert monitor._build_ansi_sequence(value) or value == "", name


# Verifies the timestamp label stays plain while its value is cyan
def test_timestamp_label_is_uncolored(colored):
    result = monitor._colorize_line("Timestamp:\t\t\tWed 26 Aug 2026, 20:23:03")
    assert monitor.DEFAULT_COLOR_THEME["timestamp_label"] == ""
    assert "timestamp_label" not in colored
    assert result == f"Timestamp:\t\t\t{colored['timestamp']}Wed 26 Aug 2026, 20:23:03{monitor.ANSI_RESET}"


# Verifies startup summary labels do not trigger whole-line styles
def test_startup_summary_rows_are_not_block_colored(colored):
    for line in ("* Target:                       octocat", "* Track repository changes:     True", "* Monitor GitHub events:        True"):
        result = monitor._colorize_line(line)
        assert monitor.ANSI_ESCAPE_RE.sub("", result) == line
        assert not result.startswith(colored["info"])


# Verifies startup durations do not become problem lines
def test_startup_summary_timer_rows_are_not_error_colored(colored):
    for line in ("* Polling interval:             30 minutes", "* Liveness output:              12 hours"):
        result = monitor._colorize_line(line)
        assert colored["error"] not in result
        assert colored["duration"] in result


# Verifies debug failures and fallback notices stay outside the error block
@pytest.mark.parametrize("line", ["[DEBUG 15:57:30] GitHub request failed status=403", "* Repository details are unavailable so count-only monitoring will continue"])
def test_diagnostic_details_and_fallback_notices_are_not_error_colored(colored, line):
    assert not monitor._colorize_line(line).startswith(colored["error"])


# Verifies real problem lines keep the error block style
@pytest.mark.parametrize("line", ["* Error: request timeout after 15 seconds", "* Cannot fetch repository details"])
def test_real_problem_lines_stay_error_colored(colored, line):
    assert monitor._colorize_line(line).startswith(colored["error"])


# Verifies static counts stay plain while changes get counter colours
def test_static_counts_stay_plain_and_changes_are_colored(colored):
    for line in ("Followers:\t\t\t98", "Followings:\t\t\t302", "Repositories:\t\t\t41", "Available events:\t\t7"):
        assert monitor._colorize_line(line) == line
    changed = monitor._colorize_line("* Followers changed for user octocat from 98 to 100 (+2)")
    assert f"{colored['count_up']}98{monitor.ANSI_RESET}" in changed
    assert f"{colored['count_up']}(+2){monitor.ANSI_RESET}" in changed


# Verifies line colouring changes only ANSI spans
@pytest.mark.parametrize("line", ["Username:\t\t\tOcto Cat", "Event ID:\t\t\t12345", "Repo name:\t\t\toctocat/Hello World", "Event type:\t\t\tPushEvent", "Repo URL:\t\t\thttps://github.com/octocat/repo", "Timestamp:\t\t\tSun 21 Apr 2024, 15:08:45"])
def test_colorize_line_never_rewrites_the_text(colored, line):
    assert monitor.ANSI_ESCAPE_RE.sub("", monitor._colorize_line(line)) == line


# Verifies each banner line uses only banner colours
def test_startup_banner_uses_only_its_own_colours(colored, capsys):
    monitor.print_startup_banner()
    rendered = monitor.apply_color_to_text(capsys.readouterr().out)
    assert set(monitor.SGR_SEQUENCE_RE.findall(rendered)) <= {colored["header"], colored["info"], monitor.ANSI_RESET}
    for line in monitor.STARTUP_BANNER.splitlines():
        if line:
            assert f"{colored['header']}{line}{monitor.ANSI_RESET}" in rendered


# Verifies banner colouring preserves every character
def test_startup_banner_art_is_unchanged(colored):
    rendered = monitor.apply_color_to_text(monitor.STARTUP_BANNER)
    assert monitor.ANSI_ESCAPE_RE.sub("", rendered) == monitor.STARTUP_BANNER


# Verifies labelled GitHub rows use their expected theme parts
@pytest.mark.parametrize(("line", "part"), [("Username:\tOcto Cat", "username"), ("Event ID:\t12345", "id"), ("Repo name:\toctocat/Hello World", "repository"), ("Event type:\tPushEvent", "event"), ("Commit message:\t'Fix setup'", "commit"), ("Object name:\tfeature/colour", "branch"), ("Email:\talerts@example.test", "email")])
def test_labelled_rows_use_the_expected_theme_part(colored, line, part):
    assert colored[part] in monitor._colorize_line(line)


# Verifies each real listing row colours its complete identity token
@pytest.mark.parametrize(("line", "token", "part"), (("🔸 hello-world (fork) ", "hello-world", "repository"), ("- octocat/hello-world [ https://github.com/octocat/hello-world/ ]", "octocat/hello-world", "repository"), ("- hello-world [ https://github.com/octocat/hello-world/ ]", "hello-world", "repository"), ("- octocat [ https://github.com/octocat/ ]", "octocat", "username"), ("- octocat (Octo Cat 🐙)", "octocat (Octo Cat 🐙)", "username")))
def test_listing_rows_use_their_domain_colour(colored, line, token, part):
    result = monitor._colorize_line(line)
    assert f"{colored[part]}{token}{monitor.ANSI_RESET}" in result
    if "https://" in line:
        assert colored["url"] in result


# Verifies doctor markers are coloured without colouring their details
@pytest.mark.parametrize(("marker", "part"), [("PASS", "boolean_true"), ("WARN", "warning"), ("FAIL", "error"), ("SKIP", "info")])
def test_doctor_status_markers_are_colored(colored, marker, part):
    line = f"[{marker}] GitHub token is configured"
    assert monitor._colorize_line(line) == f"{colored[part]}[{marker}]{monitor.ANSI_RESET} GitHub token is configured"


# Verifies presence values use distinct online and offline styles
def test_presence_keywords_pick_the_matching_style(colored):
    assert monitor.colorize_status("public").startswith(colored["status_online"])
    assert monitor.colorize_status("private").startswith(colored["status_offline"])
    assert monitor.colorize_status("unknown").startswith(colored["status_other"])


# Verifies visibility and block values use their actual sentence context
@pytest.mark.parametrize(("line", "token", "part"), (("Public profile:\t\t\tYes", "Yes", "status_online"), ("Public profile:\t\t\tNo", "No", "status_offline"), ("Blocked by the user:\t\tNo", "No", "status_online"), ("Blocked by the user:\t\tYes", "Yes", "status_offline"), ("Blocked by the user:\t\tUnknown", "Unknown", "status_other"), ("* User octocat has changed profile visibility to 'private' !", "private", "status_offline"), ("* User octocat has changed profile visibility to 'public' !", "public", "status_online"), ("* User octocat has blocked you!", "blocked", "status_offline"), ("* User octocat has unblocked you!", "unblocked", "status_online"), ("Repository is now public", "public", "status_online")))
def test_emitted_status_values_use_contextual_status_colours(monkeypatch, line, token, part):
    status_styles = {"status_online": "\x1b[94m", "status_offline": "\x1b[95m", "status_other": "\x1b[97m"}
    monkeypatch.setattr(monitor, "COLOR_ENABLED", True)
    monkeypatch.setattr(monitor, "_COLOR_STYLES", {**monitor._COLOR_STYLES, **status_styles})
    result = monitor._colorize_line(line)
    assert f"{status_styles[part]}{token}{monitor.ANSI_RESET}" in result


# Verifies clock matching rejects ports and partial times
@pytest.mark.parametrize("value", ["00:00", "23:59", "21:07:39", "~21:07:39", "09:15 PM"])
def test_time_color_regex_accepts_only_complete_clock_values(value):
    assert monitor._TIME_ONLY_RE.fullmatch(value)
    for invalid in ("24:00", "12:60", "8000:8000", "abc12:30", "1:12:30"):
        assert monitor._TIME_ONLY_RE.search(invalid) is None


# Verifies hostile controls cannot drive the terminal
@pytest.mark.parametrize(("hostile", "expected"), [("repo\x1b[2Jcleared", "repo[2Jcleared"), ("repo\x1b]0;title\x07", "repo]0;title"), ("visible\rhidden", "visiblehidden"), ("bell\x07 null\x00", "bell null"), ("delete\x7f c1\x1b[3J", "delete c1[3J")])
def test_sanitize_terminal_text_removes_control_sequences(hostile, expected):
    assert monitor.sanitize_terminal_text(hostile) == expected


# Verifies SGR colours and whitespace survive sanitizing
def test_sanitize_terminal_text_keeps_colours_and_layout():
    coloured = "\033[36mInfo\033[0m\tvalue\nnext line"
    assert monitor.sanitize_terminal_text(coloured) == coloured


# Verifies controls between valid SGR spans are removed
def test_sanitize_terminal_text_cleans_between_colour_codes():
    smuggled = "\033[36mlabel\033[0m \x1b[2J\033[31mvalue\033[0m"
    assert monitor.sanitize_terminal_text(smuggled) == "\033[36mlabel\033[0m [2J\033[31mvalue\033[0m"


# Builds one in-memory logger
def make_logger():
    terminal = io.StringIO()
    logfile = io.StringIO()
    logger = monitor.Logger.__new__(monitor.Logger)
    logger.__dict__.update(terminal=terminal, logfile=logfile)
    return logger, terminal, logfile


# Verifies terminal colour and ANSI-free file output
def test_logger_colors_the_terminal_and_keeps_the_log_plain(colored, monkeypatch):
    monkeypatch.setattr(monitor, "TRUNCATE_CHARS", 0)
    logger, terminal, logfile = make_logger()
    logger.write("Username:\t\t\tOcto Cat\n")
    logger.log_only(f"{colored['error']}failure{monitor.ANSI_RESET}\n")
    assert colored["username"] in terminal.getvalue()
    assert monitor.ANSI_ESCAPE_RE.search(logfile.getvalue()) is None


# Verifies truncation measures plain text before colouring
def test_truncation_runs_before_colour_is_applied(colored, monkeypatch):
    monkeypatch.setattr(monitor, "TRUNCATE_CHARS", 20)
    logger, terminal, _ = make_logger()
    logger.write("Username:\tOcto Cat The Very Long Display Name\n")
    plain = monitor.ANSI_ESCAPE_RE.sub("", terminal.getvalue()).rstrip("\n")
    assert len(plain.expandtabs(8)) == 20
    assert colored["username"] in terminal.getvalue()


# Verifies the early stream colours after removing controls
def test_terminal_stream_colors_and_sanitizes(colored):
    terminal = io.StringIO()
    monitor.TerminalStream(terminal).write("Username:\tOcto\x1b[2J Cat\n")
    assert colored["username"] in terminal.getvalue()
    assert "\x1b[2J" not in terminal.getvalue()


# Verifies doctor progress has no ANSI and erases visible width
def test_doctor_progress_line_is_never_colored(colored, monkeypatch):
    terminal = type("Stream", (), {"isatty": lambda self: True, "write": lambda self, text: self.values.append(text), "flush": lambda self: None, "values": []})()
    monkeypatch.setattr(monitor, "VERBOSE_MODE", False)
    monkeypatch.setattr(monitor, "DEBUG_MODE", False)
    progress = monitor.DoctorProgress(terminal)
    progress.show(f"{colored['error']}authentication{monitor.ANSI_RESET}")
    progress.clear()
    assert "\x1b" not in "".join(terminal.values)
    assert terminal.values[-1] == " " * len("* Checking authentication ...") + "\r"


# Verifies doctor progress unwraps all output wrappers
def test_doctor_terminal_stream_unwraps_output_wrappers():
    real_terminal = io.StringIO()
    logger, _, _ = make_logger()
    logger.__dict__["terminal"] = monitor.TerminalStream(real_terminal)
    assert monitor.DoctorProgress(logger).terminal is real_terminal


# Verifies support detection honours environment contracts
def test_stream_support_detection_honours_environment(monkeypatch):
    monkeypatch.setattr(monitor.sys, "stdin", type("Stdin", (), {"isatty": lambda self: True})())
    interactive = type("Stream", (), {"isatty": lambda self: True})()
    monkeypatch.setenv("TERM", "xterm-256color")
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert monitor._stream_supports_color(interactive) is True
    assert monitor._stream_supports_color(type("Stream", (), {"isatty": lambda self: False})()) is False
    monkeypatch.setenv("NO_COLOR", "1")
    assert monitor._stream_supports_color(interactive) is False
    monkeypatch.delenv("NO_COLOR")
    monkeypatch.setenv("TERM", "dumb")
    assert monitor._stream_supports_color(interactive) is False


# Verifies piped stdin disables colours
def test_piped_stdin_disables_color(monkeypatch):
    monkeypatch.setenv("TERM", "xterm-256color")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr(monitor.sys, "stdin", type("Stdin", (), {"isatty": lambda self: False})())
    assert monitor._stream_supports_color(type("Stream", (), {"isatty": lambda self: True})()) is False


# Verifies partial themes merge over built-in values
def test_config_theme_overrides_only_named_parts(monkeypatch):
    monkeypatch.setattr(monitor, "COLORED_OUTPUT", True)
    monkeypatch.setattr(monitor, "COLOR_THEME", {"username": "red bold"})
    monkeypatch.setattr(monitor, "_stream_supports_color", lambda stream: True)
    monitor.init_color_output(io.StringIO())
    assert monitor._COLOR_STYLES["username"] == "\033[31;1m"
    assert monitor._COLOR_STYLES["repository"] == monitor._build_ansi_sequence(monitor.DEFAULT_COLOR_THEME["repository"])


# Verifies disabled output clears all styles
def test_disabled_color_output_clears_the_style_map(monkeypatch):
    monkeypatch.setattr(monitor, "COLORED_OUTPUT", False)
    monkeypatch.setattr(monitor, "_stream_supports_color", lambda stream: True)
    monitor.init_color_output(io.StringIO())
    assert monitor.COLOR_ENABLED is False
    assert monitor._COLOR_STYLES == {}
    assert monitor.apply_color_to_text("Username:\tOcto Cat\n") == "Username:\tOcto Cat\n"


# Verifies early config applies appearance before argparse
def test_early_output_config_reads_terminal_appearance(monkeypatch, tmp_path):
    config = tmp_path / "github_monitor.conf"
    config.write_text("CLEAR_SCREEN = False\nCOLORED_OUTPUT = False\n", encoding="utf-8")
    monkeypatch.setattr(monitor.sys, "argv", ["github_monitor.py", "--config-file", str(config)])
    monkeypatch.setattr(monitor, "CLEAR_SCREEN", True)
    monkeypatch.setattr(monitor, "COLORED_OUTPUT", True)
    monitor.apply_early_output_config()
    assert monitor.CLEAR_SCREEN is False
    assert monitor.COLORED_OUTPUT is False


# Verifies broken early config leaves defaults unchanged
def test_early_output_config_ignores_a_broken_config(monkeypatch, tmp_path):
    config = tmp_path / "github_monitor.conf"
    config.write_text("import os\n", encoding="utf-8")
    monkeypatch.setattr(monitor.sys, "argv", ["github_monitor.py", "--config-file", str(config)])
    monkeypatch.setattr(monitor, "COLORED_OUTPUT", True)
    monitor.apply_early_output_config()
    assert monitor.COLORED_OUTPUT is True


# Verifies the none sentinel skips discovery
def test_early_output_config_skips_disabled_discovery(monkeypatch):
    calls = []
    monkeypatch.setattr(monitor.sys, "argv", ["github_monitor.py", "--config-file", "none"])
    monkeypatch.setattr(monitor, "find_config_file", lambda path=None: calls.append(path))
    monitor.apply_early_output_config()
    assert calls == []


# Verifies both config flag spellings are scanned
@pytest.mark.parametrize(("arguments", "expected"), [(["--config-file", "/tmp/one.conf"], "/tmp/one.conf"), (["--config-file=/tmp/two.conf"], "/tmp/two.conf"), (["--verbose"], None), (["--config-file"], None)])
def test_early_config_file_argument_scan(arguments, expected):
    assert monitor.early_config_file_argument(arguments) == expected


# Verifies the CLI disable wins over configuration
def test_no_color_flag_disables_colored_output(monkeypatch):
    monkeypatch.setattr(monitor, "COLORED_OUTPUT", False)
    monkeypatch.setattr(monitor, "_stream_supports_color", lambda stream: True)
    monitor.init_color_output(io.StringIO())
    assert monitor.COLOR_ENABLED is False


# Verifies Logger bypasses the early colour stream
def test_logger_unwraps_the_early_terminal_stream(colored, monkeypatch, tmp_path):
    raw = io.StringIO()
    monkeypatch.setattr(monitor.sys, "stdout", monitor.TerminalStream(raw))
    monkeypatch.setattr(monitor, "TRUNCATE_CHARS", 0)
    logger = monitor.Logger(str(tmp_path / "monitor.log"))
    try:
        logger.write("Timestamp:\t\t\tWed 26 Aug 2026, 20:23:03\n")
    finally:
        logger.logfile.close()
    assert logger.terminal is raw
    assert raw.getvalue() == f"Timestamp:\t\t\t{colored['timestamp']}Wed 26 Aug 2026, 20:23:03{monitor.ANSI_RESET}\n"


# Verifies nested early streams reach the terminal
def test_unwrap_terminal_stream_reaches_the_real_terminal():
    raw = io.StringIO()
    assert monitor.unwrap_terminal_stream(raw) is raw
    assert monitor.unwrap_terminal_stream(monitor.TerminalStream(monitor.TerminalStream(raw))) is raw


# Verifies later rules cannot reclaim a coloured span
def test_inline_rules_do_not_reclaim_already_colored_text(colored):
    result = monitor._colorize_line("[ date: Sun 16 Feb 2025, 14:34:06 - 1 year ago ]")
    assert result.count(colored["date"]) == 1
    assert result == f"[ date: {colored['date']}Sun 16 Feb 2025, 14:34:06{monitor.ANSI_RESET} - {colored['duration']}1 year{monitor.ANSI_RESET} ago ]"


# Verifies repository names keep spaces and punctuation
@pytest.mark.parametrize("name", ["3 AM Sessions", "BDSM (dark tools)", "Tools / Actions / Hooks", "Tomorrowland (TML) 🛠️", "Nocturne_Rewired"])
def test_names_with_slashes_and_brackets_are_still_colored(colored, name):
    result = monitor._colorize_line(f"* Repo '{name}' changed")
    assert f"{colored['repository']}{name}{monitor.ANSI_RESET}" in result


# Verifies quoted paths stay plain
@pytest.mark.parametrize("value", ["monitor_state.json", "/data/github.log", "~/logs/output.txt", "C:\\Users\\me\\state.json"])
def test_quoted_file_and_path_values_stay_plain(colored, value):
    line = f"* Repo '{value}' loaded"
    assert monitor._colorize_line(line) == line


# Verifies downloaded-script descriptions stay plain
def test_downloaded_script_quoted_description_stays_plain(colored):
    line = "'A repository description with spaces / punctuation.'"
    assert monitor._colorize_line(line) == line


# Verifies change reports are not painted end to end
@pytest.mark.parametrize("line", CHANGE_REPORT_LINES)
def test_change_reports_are_not_painted_end_to_end(colored, line):
    result = monitor._colorize_line(line)
    assert monitor.ANSI_ESCAPE_RE.sub("", result) == line
    assert not result.startswith("\x1b")


# Verifies only problems get whole-line styles
def test_only_problem_lines_are_painted_end_to_end(colored):
    for line, part in (("* Error: could not reach GitHub", "error"), ("* Warning: something odd", "warning")):
        assert monitor._colorize_line(line).startswith(colored[part])


# Verifies every theme key has a source consumer
def test_every_theme_part_is_used():
    source = Path(monitor.__file__).read_text(encoding="utf-8")
    looked_up = set(re.findall(r"""colorize\(\s*["']([a-z_]+)["']""", source))
    looked_up |= set(re.findall(r"""_apply_style_nested\([^,]+,\s*["']([a-z_]+)["']""", source))
    looked_up |= set(re.findall(r"""(?:style_name|key) = ["']([a-z_]+)["']""", source))
    looked_up |= set(re.findall(r""",\s*["']([a-z_]+)["']\),?\s*$""", source, re.M))
    marks = re.search(r"_DOCTOR_MARK_STYLES = \{(.*?)\}", source, re.S)
    assert marks is not None
    looked_up |= set(re.findall(r""":\s*["']([a-z_]+)["']""", marks.group(1)))
    assert not set(monitor.DEFAULT_COLOR_THEME) - looked_up


# Verifies the README theme table lists every shipped key once
def test_documented_theme_keys_match_the_built_in_theme():
    readme = Path(monitor.__file__).with_name("README.md").read_text(encoding="utf-8")
    section = readme.split('<a id="terminal-colours"></a>', 1)[1].split('<a id="github-personal-access-token"></a>', 1)[0]
    documented = re.findall(r"^\| `([a-z_]+)` \|", section, re.M)
    assert len(documented) == len(set(documented))
    assert set(documented) == set(monitor.DEFAULT_COLOR_THEME)


# Verifies the target uses username colour everywhere
@pytest.mark.parametrize("line", ["Monitoring GitHub user octocat", "User 'octocat' not found", "Getting repositories for user 'octocat'", "Username:\t\t\toctocat"])
def test_target_username_uses_the_username_colour_everywhere(colored, line):
    result = monitor._colorize_line(line)
    assert monitor.ANSI_ESCAPE_RE.sub("", result) == line
    assert f"{colored['username']}octocat{monitor.ANSI_RESET}" in result
    assert colored["repository"] not in result


# Verifies display names with spaces are complete
def test_display_name_still_uses_the_name_colour(colored):
    result = monitor._colorize_line("Username:\t\t\tOcto Cat 🐙")
    assert f"{colored['username']}Octo Cat 🐙{monitor.ANSI_RESET}" in result


# Verifies setup destinations and commands are coloured
def test_setup_surface_is_coloured(colored):
    output = io.StringIO()
    context = SimpleNamespace(install_method="pip")
    state = SimpleNamespace(config_path=Path("monitor.conf"), dotenv_path=Path(".env"))
    monitor._wizard_print_setup_destinations(output, context, state)
    monitor._wizard_print_command(output, "Check setup again:", "github_monitor --doctor GITHUB_USERNAME")
    rendered = output.getvalue()
    assert f"Detected install method: {colored['username']}pip{monitor.ANSI_RESET}" in rendered
    assert f"{colored['section']}github_monitor --doctor GITHUB_USERNAME{monitor.ANSI_RESET}" in rendered


# Verifies wizard prompts and menus are coloured
def test_wizard_prompt_and_menu_are_coloured(colored):
    output = io.StringIO()
    monitor.wizard_ask_choice("Pick one", (("first", "First", "Use the first choice."), ("second", "Second", "Use the second choice.")), "second", lambda: "1", output)
    rendered = output.getvalue()
    assert f"{colored['section']}Pick one{monitor.ANSI_RESET}" in rendered
    assert f"{colored['username']}1{monitor.ANSI_RESET}. First" in rendered
    assert f"{colored['info']} (default){monitor.ANSI_RESET}" in rendered
    assert f"{colored['info']}Choose [1-2]: {monitor.ANSI_RESET}" in rendered


# Verifies doctor headings and verdicts are coloured
def test_doctor_report_headings_are_coloured(colored):
    report = monitor.DoctorReport()
    report.add("Environment", "PASS", "Python is supported", "Plain detail 30 seconds")
    output = io.StringIO()
    output.write(monitor.colorize("header", "Doctor") + "\n")
    monitor.render_doctor_sections(report, output)
    monitor.render_doctor_summary(report, output)
    rendered = output.getvalue()
    assert f"{colored['header']}Doctor{monitor.ANSI_RESET}" in rendered
    assert f"{colored['header']}Summary{monitor.ANSI_RESET}" in rendered
    assert f"{colored['section']}Environment{monitor.ANSI_RESET}" in rendered
    assert f"{colored['duration']}30 seconds" not in rendered


# Verifies explicit surfaces bypass the general line colouriser in the real wrapper stack
def test_explicit_surface_stream_avoids_a_second_colour_pass(colored):
    raw = io.StringIO()
    wrapped = monitor.TerminalStream(raw)
    destination = monitor.terminal_surface_stream(wrapped)
    destination.write(monitor.colorize("header", "Doctor") + "\n")
    destination.write("  Detail: 30 seconds\n")
    rendered = raw.getvalue()
    assert rendered.count(colored["header"]) == 1
    assert f"{colored['duration']}30 seconds" not in rendered


# Verifies recovery advice uses info and URL colours
def test_recovery_guidance_uses_the_info_colour(colored):
    result = monitor._colorize_line(f"To fix: Retry at {monitor.CONFIG_GUIDE_URL}")
    assert result.startswith(colored["info"])
    assert colored["url"] in result


# Verifies names remain visible inside whole-line styles
def test_name_palette_differs_from_every_whole_line_style():
    for name in ("username", "id", "repository", "event", "commit", "branch"):
        for block in ("info", "warning", "error", "signal", "email", "webhook"):
            assert monitor.DEFAULT_COLOR_THEME[name] != monitor.DEFAULT_COLOR_THEME[block], f"{name} matches {block}"


# Verifies repository progress contains no ANSI escapes
def test_repository_progress_line_has_no_ansi_escapes(colored, monkeypatch):
    terminal = type("Stream", (), {"write": lambda self, text: self.values.append(text), "flush": lambda self: None, "values": []})()
    monkeypatch.setattr(monitor, "stdout_bck", terminal)
    monkeypatch.setattr(monitor.shutil, "get_terminal_size", lambda fallback=(80, 20): type("Size", (), {"columns": 80})())
    monkeypatch.setattr(monitor._display_progress, "width", 0, raising=False)
    monitor._display_progress(1, 2, f"{colored['repository']}repo{monitor.ANSI_RESET}")
    assert "\x1b" not in "".join(terminal.values)
    assert terminal.values[-1].startswith("\rRepos [")
