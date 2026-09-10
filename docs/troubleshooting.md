# Troubleshooting

## Doctor Preflight

Run the comprehensive preflight before monitoring a new target or when a working setup starts failing:

```sh
github_monitor --doctor <github_target>
```

Doctor is read-only by default. It checks the effective configuration after config, dotenv, environment and command-line precedence without creating logs, CSV files or directories. It opens with the detected install method, then reports these fixed sections:

* **Environment**: Python support, required dependencies and optional dependencies.
* **Configuration**: selected files, secret names and sources, [TLS verification](configuration.md#tls-verification), GitHub URLs, timezone, the timing and count settings, log separator mode and the log and CSV files monitoring would write.
* **Authentication** and **Connectivity**: live token validation plus the configured connectivity endpoint. The connectivity row reports whether that endpoint answers at all, the same test monitoring runs at startup, so a temporary error returned by the server is not reported as a broken setup.
* **Target** and **Monitoring**: target access, repository, starred repository and event feeds and optional contribution tracking.
* **Notifications**: whether email and webhook alerts are disabled, unusable or ready.

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

Commands printed after setup or inside recovery guidance automatically match a PyPI install or downloaded script with platform-correct quoting. They also carry the `--config-file` or `--env-file` you started with, so they can be pasted as they are.

Monitoring failures are classified the same way, so a rejected token, a refused request, a rate limit and an unreachable network each get their own summary and fix instead of the raw exception text. The banner that says nothing changed prints in any mode: `* Monitoring healthy for <github_target>` with what was checked, followed by `Liveness check, timestamp:`. It is timed rather than counted in checks, so it appears once per `LIVENESS_CHECK_INTERVAL` of quiet, measured from the last thing the run printed. That setting defaults to 86400 seconds, a day. Set it to 0 to switch the banner off. A monitoring failure is reported as `* Error: <what failed> (retrying in <time>)`, with the `To fix:` paragraph under it the first time that category appears. Every monitor in this family prints that same line. During a long outage the failure is reported in full once, then the tool stays quiet and reminds you once an hour with `* Monitoring degraded for <github_target>`, the summary of what is still failing, when it started and how many checks have failed so far, so a two-day outage is a handful of lines rather than one block per check. The reminder has its own clock and does not depend on `LIVENESS_CHECK_INTERVAL`, so it keeps coming when the banner is off. When the failure clears, `* Monitoring recovered for <github_target>` reports how long it lasted. An outage that starts failing differently is still one outage: a lost connection that reads as a timeout on one check and as an unreachable host on the next prints nothing new, a change to another kind of failure that clears on its own is one line, `* Monitoring failure changed for <github_target>. <what fails now>`, and a change to a failure that needs you is reported in full.

A run that has neither a username nor a token reports the missing username first, since that is the simpler of the two to supply.

## Verbose and Debug Output

Verbose mode answers "what did the tool decide?" It expands the startup summary and states when missing data prevents a specific alert from firing during the current check. The expanded summary names the webhook service alerts go to and whether that channel is switched on, the mail server that sends them with the recipient address masked, whether the delivery confirmations are printed and the process id, Python version and operating system the run is on, with each channel's own settings indented under it:

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

`VERBOSE_MODE` and `DEBUG_MODE` provide the same controls in the configuration file. Set `DELIVERY_CONFIRMATIONS = False` to keep verbose mode without the `* Email delivered` and `* Webhook delivered` lines, which is worth doing when alerts are frequent. An explicit command-line flag takes precedence even when the selected config disables that mode, including while the config is being loaded. Both printers sanitize internally so loaded secrets plus common GitHub token, authorization and Discord webhook shapes are redacted before terminal or log output.

## Installation and Command Problems

If Python or `pip` is missing, use the [Python install walkthrough](installation.md#new-to-python-install-everything).

If `github_monitor` is not found after installation, close the terminal and open it again. On Windows with Python Install Manager, run `py install --refresh` to refresh command aliases. For a pipx installation, run `pipx ensurepath` then reopen the terminal. If you downloaded the script, use the [manual command](usage.md#command-format) from its directory.

If `pip` reports an externally managed environment, follow the pipx steps in [Installation](installation.md#install-github-monitor-after-python-check). Use `pipx upgrade github_monitor` for later upgrades.

If the tool cannot import a dependency, install the dependencies with the same Python interpreter that runs the script. On macOS or Linux use `python3 -m pip install -r requirements.txt`. On Windows use `python -m pip install -r requirements.txt`. Match the requirements file to your downloaded script.

If a new terminal cannot find your saved settings, return to the directory used during setup or pass both `--config-file` and `--env-file` explicitly. Run `github_monitor --doctor <github_target>` to see which settings are loaded.
