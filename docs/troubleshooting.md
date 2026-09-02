# Troubleshooting

## Doctor Preflight

Run the comprehensive preflight before monitoring a new target or when a working setup starts failing:

```sh
github_monitor --doctor <github_target>
```

Doctor is read-only by default. It checks the effective configuration after config, dotenv, environment and command-line precedence without creating logs, CSV files or directories. It opens with the detected install method, then reports these fixed sections:

* Environment: Python support, required dependencies and optional dependencies.
* Configuration: selected files, secret names and sources, [TLS verification](configuration.md#tls-verification), GitHub URLs, timezone, the timing and count settings, log separator mode and the log and CSV files monitoring would write.
* Authentication and connectivity: live token validation plus the configured connectivity endpoint. The connectivity row reports whether that endpoint answers at all, the same test monitoring runs at startup, so a temporary error returned by the server is not reported as a broken setup.
* Target and monitoring: target access, repository, starred repository and event feeds and optional contribution tracking.
* Notifications: whether email and webhook alerts are disabled, unusable or ready.

Every check uses one of four stable markers: `[PASS]`, `[WARN]`, `[FAIL]` or `[SKIP]`, colour-coded by status when colour output is on. Every `[WARN]` and `[FAIL]` row carries an indented `To fix:` line under its marker, plus a `Guide:` link when a documentation page covers that row specifically. A `[SKIP]` row names a check that could not run and says why. Warnings keep exit status `0`. Any failed check or approved delivery test returns exit status `1`, so doctor can be used in a container healthcheck or CI smoke test.

When stdin is interactive and a notification channel is ready, doctor offers a separate default-no approval for one real email and one real webhook. A piped or non-interactive run never sends messages. Review the sanitized report before posting it because targets, paths and recipient addresses can still identify your setup.

The report ends with a **Next steps** block naming the command that starts monitoring, carrying the same `--config-file` and `--env-file` this run checked. It carries the target this run used, leaves it out when the configuration file already supplies one and otherwise shows `<github_target>` for you to replace. While a check is failing it asks for the failures first.

## Error Messages and Recovery

Failures that stop an action use one consistent shape:

```text
* Error: What failed
To fix: The next action to take
Guide: A relevant documentation link
```

Recovery codes are stable identifiers such as `config.invalid`, `auth.github_token_invalid`, `network.timeout`, `github.rate_limited` and `file.unwritable`. Include the code when asking for help. Commands printed after setup or inside recovery guidance automatically match a PyPI install or downloaded script with platform-correct quoting. They also carry the `--config-file` or `--env-file` you started with, so they can be pasted as they are.

Monitoring failures are classified the same way, so a rejected token, a refused request, a rate limit and an unreachable network each get their own summary and fix instead of the raw exception text. The banner that says nothing changed prints in any mode: `* Monitoring healthy for <github_target>` with what was checked, followed by `Liveness check, timestamp:`. It is timed rather than counted in checks, so it appears once per `LIVENESS_CHECK_INTERVAL` of quiet, measured from the last thing the run printed. A monitoring failure is reported as `* Error: <what failed> (retrying in <time>)`, with the `To fix:` paragraph under it the first time that category appears. Every monitor in this family prints that same line. During a long outage the failure is reported in full once, then the liveness banner takes over with `* Monitoring degraded for <github_target>` and the summary of what is still failing, so a broken run keeps saying it is alive without repeating the same paragraph. The reminder follows the same clock, so an outage that retries faster than the normal polling interval does not report more often. When the failure clears, `* Monitoring recovered for <github_target>` reports how long it lasted. Setting `LIVENESS_CHECK_INTERVAL` to 0 removes the banner that carries the reminder, so the one-line summary goes back to printing on every check.

A run that has neither a username nor a token reports the missing username first, since that is the simpler of the two to supply.

## Verbose and Debug Output

Verbose mode answers "what did the tool decide?" It expands the startup summary, includes stable recovery codes and states when missing data prevents a specific alert from firing during the current check:

```sh
github_monitor <github_target> --verbose
```

Debug mode answers "what did the tool do?" Every line is timestamped, names the operation, then lists its details as comma-separated `key=value` fields:

```text
[DEBUG 23:53:52] Webhook delivery: channel=discord, host=https://discord.com, attempt=1/2, timeout=10s
[DEBUG 23:53:52] Webhook delivery: channel=discord, outcome=OK, attempt=2/2
```

A `--debug` run leaves the terminal as it was instead of clearing it, so the output you are comparing against stays on screen. `--verbose` clears it like an ordinary run.

The fields carry the endpoint, timeout, masked credential, response status, retry decision, file path and monitoring timing used by the relevant operation:

```sh
github_monitor <github_target> --debug
```

The modes cover the full runtime path:

* Direct HTTP, PyGithub and SMTP operations report their destination and timeout. Every configured credential is rendered as the fixed `<redacted>` marker inside the printer.
* Exceptions that would otherwise be swallowed name the failed operation and exception type in debug output.
* Degraded profile, repository, contribution and event checks state which alert cannot fire in verbose output, once when the lookup starts failing and once when it works again.
* Email and webhook deliveries report the attempt, response, retryability, wait and confirmed outcome as `outcome=OK` or `outcome=failed`.
* Config, dotenv, CSV, log and private-setting file operations report both success and failure branches.
* Retries and monitoring sleeps report their reason, interval and next timestamp.
* Config loading reports its file and applied setting count. Private-setting resolution reports each setting name and source without printing its value.

`VERBOSE_MODE` and `DEBUG_MODE` provide the same controls in the configuration file. An explicit command-line flag takes precedence even when the selected config disables that mode, including while the config is being loaded. Both printers sanitize internally so loaded secrets plus common GitHub token, authorization and Discord webhook shapes are redacted before terminal or log output.
