# Getting help

Start with the [documentation](https://misiektoja.github.io/github_monitor/). [Installation](https://misiektoja.github.io/github_monitor/installation/) and [Setup & First Run](https://misiektoja.github.io/github_monitor/setup-and-first-run/) cover most first-run problems, [Configuration](https://misiektoja.github.io/github_monitor/configuration/) explains every setting the tool reads and [Troubleshooting](https://misiektoja.github.io/github_monitor/troubleshooting/) covers what to do when a check fails.

For a new install, run `github_monitor --setup`. Review the complete summary before saving. The wizard keeps private values in a separate dotenv file then offers the read-only doctor preflight after authentication is complete. If no interactive terminal is available, run `github_monitor --generate-config github_monitor.conf` and follow the manual setup steps in [Setup & First Run](https://misiektoja.github.io/github_monitor/setup-and-first-run/).

## Check your setup first

Confirm which version you are running then run the complete read-only preflight for the affected target:

```sh
github_monitor --version
github_monitor --doctor <github_username>
```

Most reports come down to an expired or under-scoped GitHub token, an unreachable target, invalid output permissions, an SMTP setup that cannot deliver or a webhook destination the provider no longer accepts. Doctor tells those apart in one report.

When an error includes a recovery code, include that code in the report. Re-run the failing command with `--verbose` to show decisions and unavailable alerts. Use `--debug` when the report also needs request, delivery, file, retry or poll timing details. Technical detail is sanitized but you should still review copied output before posting it publicly.

## Doctor preflight

Doctor checks Environment, Configuration, Authentication, Connectivity, Target, Monitoring and Notifications in a fixed order. It writes no files. Each check has a stable `[PASS]`, `[WARN]`, `[FAIL]` or `[SKIP]` marker plus a fix and guide for every non-pass result.

The Configuration section resolves `LOCAL_TIMEZONE`. It reports the detected zone when the setting is `Auto` and fails when the zone is invalid or cannot be detected.

The Notifications section signs in to the configured SMTP server and validates webhook settings without sending anything. Each ready row lists the alert categories that channel would deliver.

## Terminal output

Live colour is enabled by `COLORED_OUTPUT` and can be disabled with `--no-color` or `NO_COLOR=1`. It is also disabled for redirected output, piped stdin and terminals with an unset or `dumb` `TERM`. Saved log files never contain ANSI colour sequences.

The terminal sanitizer preserves SGR colour sequences so the tool's own styles survive the output wrapper. It removes cursor movement, screen clearing, title changes, carriage returns and other controls. A remote string that contains a bare SGR sequence may still affect styling until the next reset, but it cannot move the cursor or change terminal state outside SGR styling. Use `--no-color` when collecting output for a parser that rejects every escape byte.

`TRUNCATE_CHARS` and `--truncate` measure plain visible text before colour is added. Install `wcwidth` when exact width matters for emoji or other wide Unicode characters.

A normal non-interactive run sends no messages. When a configured channel is ready and stdin is interactive, doctor offers a separate default-no prompt for one real email and one real webhook. Declining records `[SKIP]`. An approved delivery failure records `[FAIL]` and makes the command exit with status `1`.

Include the complete sanitized doctor report in a bug report. Review target names, paths and recipient addresses before posting even though credential values are redacted.

## Where to ask

| You want to | Go to |
| --- | --- |
| Ask a question or discuss an idea | [Discussions](https://github.com/misiektoja/github_monitor/discussions) |
| Report something broken | [Bug report](https://github.com/misiektoja/github_monitor/issues/new?template=bug_report.yml) |
| Request a capability | [Feature request](https://github.com/misiektoja/github_monitor/issues/new?template=feature_request.yml) |
| Report a vulnerability | [Private security advisory](https://github.com/misiektoja/github_monitor/security/advisories/new), never a public issue |
| Contribute a change | [CONTRIBUTING.md](CONTRIBUTING.md) |

## Before you post

Include the version, recovery code, how you installed it (PyPI or manual script), your operating system, the monitored user or repository form you passed and what you expected instead. Attach the relevant part of the monitoring log file, which the tool writes unless you pass `--disable-logging`.

Never post your GitHub personal access token, SMTP passwords, webhook URLs or a complete configuration file. Redact monitored usernames and private repository names if they matter to you.

## What to expect

This is a project maintained in spare time, so replies are best effort with no response time attached. Only the latest release receives fixes, so reproduce the problem on the current version before reporting it.

If the project is useful to you, you can support its development through [GitHub Sponsors](https://github.com/sponsors/misiektoja) or [Buy Me a Coffee](https://buymeacoffee.com/misiektoja).
