# Troubleshooting

## Doctor Preflight

Run the comprehensive preflight before monitoring a new target or when a working setup starts failing:

```sh
github_monitor --doctor <github_target>
```

Doctor checks the active settings without writing files. The report covers:

* **Environment**: Python and dependencies
* **Configuration**: settings, secret sources, [TLS verification](configuration.md#tls-verification) and output files
* **Authentication** and **Connectivity**: token validation and network access
* **Target** and **Monitoring**: profile access and tracked feeds
* **Notifications**: email and webhook readiness

Results use `[PASS]`, `[WARN]`, `[FAIL]` or `[SKIP]`. Warnings and failures include a `To fix:` action and relevant guide links. Doctor exits `1` if a check or approved delivery test fails and `0` otherwise.

When stdin is interactive and a notification channel is ready, doctor offers a separate default-no approval for one real email and one real webhook. A piped or non-interactive run never sends messages. Review the sanitized report before posting it because targets, paths and recipient addresses can still identify your setup.

Follow the report's **Next steps** after correcting any failed checks. The printed start command uses the configuration and dotenv files you checked.

## Error Messages and Recovery

Failures that stop an action use one consistent shape:

```text
* Error: What failed
To fix: The next action to take
Guide: A relevant documentation link
```

Commands printed after setup or inside recovery guidance automatically match a PyPI install or downloaded script with platform-correct quoting. They also carry the `--config-file` or `--env-file` you started with, so they can be pasted as they are.

During quiet monitoring, `* Monitoring healthy for <github_target>` confirms the tool is still running. `LIVENESS_CHECK_INTERVAL` defaults to 86400 seconds (24 hours). Set it to `0` to disable this reminder.

Failures show an error and a `To fix:` action. A continuing outage produces a `* Monitoring degraded` reminder once an hour, even when liveness reminders are disabled. `* Monitoring recovered` marks recovery. Follow any new instructions if the failure changes.

A run that has neither a username nor a token reports the missing username first, since that is the simpler of the two to supply.

## Verbose and Debug Output

Verbose mode expands the startup summary with notification settings and runtime information. It also reports when missing data prevents an alert:

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

`VERBOSE_MODE` and `DEBUG_MODE` provide the same controls in the configuration file. Set `DELIVERY_CONFIRMATIONS = False` to keep verbose mode without the `* Email sent to ...` and `* Webhook sent through ...` lines, which is worth doing when alerts are frequent. An explicit command-line flag takes precedence even when the selected config disables that mode, including while the config is being loaded. Both printers sanitize internally so loaded secrets plus common GitHub token, authorization and Discord webhook shapes are redacted before terminal or log output.

Delivery confirmations name the email recipient or webhook provider without repeating the subject or message body. `DELIVERY_CONFIRMATIONS = False` hides those optional success receipts. Event output, send attempts and errors remain visible. Explicit notification tests report their result once. Generated email subjects and webhook titles use readable service names without a program-name prefix.

## Installation and Command Problems

If Python or `pip` is missing, use the [Python install walkthrough](installation.md#new-to-python-install-everything).

If `github_monitor` is not found after installation, close the terminal and open it again. On Windows with Python Install Manager, run `py install --refresh` to refresh command aliases. For a pipx installation, run `pipx ensurepath` then reopen the terminal. If you downloaded the script, use the [manual command](usage.md#command-format) from its directory.

If `pip` reports an externally managed environment, follow the pipx steps in [Installation](installation.md#install-github-monitor-after-python-check). Use `pipx upgrade github_monitor` for later upgrades.

If the tool cannot import a dependency, install the dependencies with the same Python interpreter that runs the script. On macOS or Linux use `python3 -m pip install -r requirements.txt`. On Windows use `python -m pip install -r requirements.txt`. Match the requirements file to your downloaded script.

If a new terminal cannot find your saved settings, return to the directory used during setup or pass both `--config-file` and `--env-file` explicitly. Run `github_monitor --doctor <github_target>` to see which settings are loaded.

## Invalid saved settings and state

If setup fails while saving, the configuration may already have changed. Correct the reported destination problem, rerun `--setup` with the same `--config-file` and `--env-file` paths then run `--doctor` before monitoring. The configuration backup restores non-secret settings only.

Timing values must be finite and within the documented range. Normal startup checks effective timing settings before monitoring. A configuration syntax error reports its file, line number and parser message without echoing source text that may contain credentials.

Malformed path settings and color-theme values are reported by Doctor with the setting name. Invalid color values are ignored while rendering help so you can still find the configuration commands.
