# Troubleshooting

Examples on this page use the PyPI command `github_monitor`. If you installed the manual script, replace that command with the matching [command prefix](usage.md#command-format-by-installation-method).

<a id="doctor-preflight"></a>
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

<a id="common-problems"></a>
## Common Problems

Every failure is reported in the same three-part shape: what went wrong, a `To fix:` action and a `Guide:` link to the page that covers it. The fix command matches how you installed the tool and carries the `--config-file` or `--env-file` you started with, so it can be pasted as it is. `--debug` appends a `Technical detail:` line for bug reports. Secrets are redacted from all three.

| Symptom | Likely cause | Where to look |
| --- | --- | --- |
| The token is rejected | The personal access token expired or was revoked | [GitHub Personal Access Token](setup-and-first-run.md#github-personal-access-token) then run `--set-github-token` |
| A run reports a missing username | Neither a positional target nor `TARGET_GITHUB_USERNAME` is set | [Configuration File](configuration.md#configuration-file) |
| Rate limit warnings | The polling intervals are too short for the token's quota | [Check Intervals](usage.md#check-intervals) |
| The run stops naming a file and a line number | A configuration line is not a plain `SETTING = value` assignment | [Configuration File](configuration.md#configuration-file) |
| Emails never arrive | Incomplete SMTP settings | [SMTP Settings](configuration.md#smtp-settings) then run `github_monitor --send-test-email` |
| Webhook alerts never arrive | Provider mismatch or a stale destination | [Webhook Settings](configuration.md#webhook-settings) then run `github_monitor --send-test-webhook` |
| `github_monitor` is not found after installation | The shell has not picked up the new command | [Installation and Command Problems](#installation-and-command-problems) |
| Escape sequences such as `[36m` printed as text or no colour at all | The terminal cannot display ANSI colour or colour was switched off | [Terminal Colours Look Wrong](#terminal-colours-look-wrong) |

A continuing outage produces a `* Monitoring degraded` reminder once an hour, even when the [liveness reminder](usage.md#liveness-reminder) is switched off. `* Monitoring recovered` marks recovery. Use `--verbose` to see the first failed check.

<a id="terminal-colours-look-wrong"></a>
## Terminal Colours Look Wrong

If escape sequences such as `[36m` appear as literal text, the terminal does not understand ANSI colour. Start the tool with `--no-color` or set `COLORED_OUTPUT = False` in the configuration file. On Windows, `pip install colorama` fixes the classic Command Prompt.

If colour is missing where you expect it, check in this order: `--no-color` on the command line, `COLORED_OUTPUT` in the configuration file, a `NO_COLOR` environment variable and whether output is redirected or piped. Colour is switched off in all of those cases and also when `TERM` is unset or set to `dumb`.

Log files never contain colour by design. To colour a saved log while reading it, see [Coloring Log Output with GRC](usage.md#coloring-log-output-with-grc).

To change which colours are used, see [Terminal Colours](configuration.md#terminal-colours).

<a id="choosing-the-right-logging-level"></a>
## Choosing the Right Logging Level

- **Default mode** reports activity changes and important errors
- **Verbose mode (`--verbose`)** adds occasional state changes, a line naming where each delivered alert went and a complete startup summary without private values. Set `DELIVERY_CONFIRMATIONS = False` to keep verbose mode without those delivery lines
- **Debug mode (`--debug`)** adds sanitized request flow, scheduling details and internal diagnostics

Delivery confirmations name the recipient or webhook provider. `DELIVERY_CONFIRMATIONS = False` hides these optional success messages. Monitoring events, send attempts and errors remain visible.

Both `--verbose` and `--debug` show the complete startup summary, including notification settings and credential sources. Use it to check which configuration is active without displaying private values.

Start with `--doctor`. If the suggested fix does not resolve the issue, retry with `--debug` and include only sanitized output when opening a GitHub issue.

<a id="verbose-and-debug-output"></a>
## Verbose and Debug Output

`--verbose` adds the decisions a run made, in the same `*` lines as the rest of the output:

```sh
github_monitor <github_target> --verbose
```

`--debug` traces what the tool is doing in timestamped `[DEBUG HH:MM:SS]` lines:

```sh
github_monitor <github_target> --debug
```

Lines with details read `Operation: key=value, key=value`. Fields depend on the operation. Some results report `outcome=OK`, `failed`, `degraded` or `skipped`.

<a id="installation-and-command-problems"></a>
## Installation and Command Problems

If Python or `pip` is missing, use the [Python install walkthrough](installation.md#new-to-python-check-and-install).

If `github_monitor` is not found after installation, close the terminal and open it again. On Windows with Python Install Manager, run `py install --refresh` to refresh command aliases. For a pipx installation, run `pipx ensurepath` then reopen the terminal. If you downloaded the script, use the [manual command](usage.md#command-format-by-installation-method) from its directory.

If `pip` reports an externally managed environment, follow the pipx steps in [Installation](installation.md#install-github-monitor). Use `pipx upgrade github_monitor` for later upgrades.

If the tool cannot import a dependency, install the dependencies with the same Python interpreter that runs the script. On macOS or Linux use `python3 -m pip install -r requirements.txt`. On Windows use `python -m pip install -r requirements.txt`. Match the requirements file to your downloaded script.

If a new terminal cannot find your saved settings, return to the directory used during setup or pass both `--config-file` and `--env-file` explicitly. Run `github_monitor --doctor <github_target>` to see which settings are loaded.

<a id="invalid-saved-settings-and-state"></a>
## Invalid saved settings and state

If setup fails while saving, the configuration may already have changed. Correct the reported destination problem, rerun `--setup` with the same `--config-file` and `--env-file` paths then run `--doctor` before monitoring. The configuration backup restores non-secret settings only.

Timing values must be finite and within the documented range. Normal startup checks effective timing settings before monitoring. A configuration syntax error reports its file, line number and parser message without echoing source text that may contain credentials.

Malformed path settings and color-theme values are reported by Doctor with the setting name. Invalid color values are ignored while rendering help so you can still find the configuration commands.
