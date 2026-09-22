# Usage

<a id="command-format-by-installation-method"></a>
## Command Format by Installation Method

Examples use the PyPI command. For a downloaded script, run commands from the directory containing `github_monitor.py` and keep the same arguments:

| Installation | Command |
| --- | --- |
| PyPI or pipx | `github_monitor [OPTIONS]` |
| Manual script on macOS or Linux | `python3 github_monitor.py [OPTIONS]` |
| Manual script on Windows | `python github_monitor.py [OPTIONS]` |

For example, `github_monitor --setup` becomes `python3 github_monitor.py --setup` on macOS or Linux. Use `python` on Windows. Replace placeholders such as `<github_target>` with a GitHub username or complete profile URL.

Activate the tool's virtual environment before running these commands. For a downloaded script, run them from the directory containing `github_monitor.py`.

For first-time configuration, follow [Setup & First Run](setup-and-first-run.md). Use [Doctor Preflight](troubleshooting.md#doctor-preflight) to check a setup before monitoring.

<a id="monitoring-mode"></a>
## Monitoring Mode

To monitor specific user activities and profile changes, simply enter the GitHub username as a command-line argument (`github_username` in the example below):

```sh
github_monitor github_username
```

It will track all user profile changes (e.g. changed followers, followings, starred repositories, username, email, bio, location, blog URL, number of repositories) and also all GitHub events (e.g. new pushes, PRs, issues, forks, releases etc.).

If you have not saved `GITHUB_TOKEN`, the `-t` flag remains available as a one-run fallback. The value may remain in shell history or process listings:

```sh
github_monitor github_username -t "your_github_classic_personal_access_token"
```

If you generated a configuration file as described in [Configuration File](configuration.md#configuration-file), but saved it under a different name or in a different directory, you can specify its location using the `--config-file` flag:

```sh
github_monitor <github_target> --config-file /path/github_monitor_new.conf
```

If you want to monitor changes to a user's public repositories (e.g. new stargazers, watchers, forks, issues, PRs, discussions, changed descriptions etc.) then use the `-j` flag:

```sh
github_monitor github_username -j
```

By default, missing issues, pull requests and discussions are reported as closed only after a separate lookup confirms their closed state. Verification uses at most five extra HTTP requests per monitoring cycle across all repositories, with no automatic retries or redirects. Pending items take turns across cycles. Title and author edits do not count as closures or additions.

Items that remain open, cannot be verified or exceed the budget stay in the previous snapshot, preventing false closure and addition alerts when they reappear. Deleted, transferred or inaccessible items are not reported as closed without confirmation, so their counts can remain unchanged. Set `VERIFY_REPOSITORY_CLOSURES = False` in the configuration file to restore immediate disappearance-based alerts without verification requests.

By default, only user-owned repos are tracked. To include forks and collaborations, set `GET_ALL_REPOS` to `True` or use the `-a` flag:

```sh
github_monitor github_username -j -a
```

If you want to monitor only specific repositories instead of all user-owned repositories, you can do it via the `--repos` command-line flag or the `REPOS_TO_MONITOR` configuration option (see [Repositories to Monitor](configuration.md#repositories-to-monitor)). Use the `--repos` flag with a comma-separated list of repository names:

```sh
github_monitor github_username -j --repos "repo1,repo2,repo3"
```

This will only monitor detailed changes (stargazers, watchers, forks, issues, PRs, discussions, etc.) for the specified repositories. The `--repos` flag requires the `-j` flag to be enabled and overrides the `REPOS_TO_MONITOR` configuration option.

Note: When using a specific list, newly created repositories will NOT be automatically monitored - only repositories explicitly listed will be monitored.

If you want to track a user's daily contributions then use the `-m` flag:

```sh
github_monitor github_username -m
```

Daily contribution checks read the requested day from a wider 30-day GitHub calendar window that ends at the following midnight. This avoids transient partial counts that narrow or farther-future GraphQL windows can return.

If for any reason you do not want to monitor GitHub events for the user (e.g. new pushes, PRs, issues, forks, releases etc.), then use the `-k` flag:

```sh
github_monitor github_username -k
```

The tool runs until interrupted (`Ctrl+C`). Use `tmux` or `screen` for persistence.

You can monitor multiple GitHub users by running multiple instances of the script.

The tool automatically saves its output to a `github_monitor_<github_target>.log` file. It can be changed in the settings via the `GITHUB_LOGFILE` configuration option or disabled completely via `DISABLE_LOGGING` / the `-d` flag.

Set `ASCII_LOG_SEPARATORS` to `"Auto"` (default) to use ASCII separator-only lines on Windows, `"On"` to use them on every operating system or `"Off"` to preserve Unicode separators in logs everywhere. Terminal separators stay Unicode. Log files and all other logged text remain UTF-8.

<a id="terminal-output"></a>
## Terminal Output

Use `--help` for examples grouped by task and matched to your installation.

Monitoring mode prints the settings that are actually in effect before the first check.

Optional features appear once you switch them on.

Use `--verbose` or `--debug` for the full startup summary, including output paths, notification settings, push event limits, secret sources and runtime information.

Use `--truncate N` or `TRUNCATE_CHARS` to limit screen line width. Set it to `999` to detect the terminal width automatically. Truncation does not change log files and is ignored when logging is disabled with `-d`.

Use `--push-commits-limit N` and `--push-files-limit N` to control how much of a large push is reported in full. See [Push Event Commits](configuration.md#push-event-commits).

The tool clears the terminal when monitoring starts. Set `CLEAR_SCREEN` to `False` to keep whatever is already on the screen.

The screen is never cleared when output is redirected to a file or a pipe, in debug mode or for a command that prints a result and exits, such as `--doctor`, `--help` and the test senders.

Two settings add detail to what a run prints. `VERBOSE_MODE` adds the decisions the run made and `DEBUG_MODE` adds timestamped technical traces. Both are off by default, both are independent of each other and both have a flag that wins over the file, `--verbose` and `--debug`. `DELIVERY_CONFIRMATIONS` is on by default and controls whether verbose mode confirms each delivered email and webhook alert. See [Verbose and Debug Output](troubleshooting.md#verbose-and-debug-output).

<a id="coloured-terminal-output"></a>
### Coloured Terminal Output

GitHub Monitor colours live terminal output and help by default. Saved log files stay plain text.

Turn colour off for one run with `--no-color` or permanently with `COLORED_OUTPUT = False`. Colour is also disabled for redirected output, `NO_COLOR` or an unsupported terminal. See [Terminal Colours](configuration.md#terminal-colours) for details and Windows support.

Override individual colours with `COLOR_THEME`. It is merged over the built-in theme, so you only name the parts you want to change:

```ini
COLOR_THEME = { "repository": "bright_magenta bold", "username": "green" }
```

See [Terminal Colours](configuration.md#terminal-colours) for every theme key and the accepted colour and style names.

<a id="listing-mode"></a>
## Listing Mode

There is another mode of the tool that displays various requested information (`-r`, `-g`, `-f` and `-l` flags).

If you want to display a list of public repositories (with some basic statistics) for the user then use the `-r` flag:

```sh
github_monitor github_username -r
```

<p align="center">
   <img src="https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/assets/github_list_of_repos.png" alt="github_list_of_repos" width="90%"/>
</p>

By default, only user-owned repos are listed. To include forks and collaborations, set `GET_ALL_REPOS` to `True` or use the `-a` flag:

```sh
github_monitor github_username -r -a
```

If you want to display a list of repositories starred by the user then use the `-g` flag:

```sh
github_monitor github_username -g
```

If you want to display a list of followers and followings for the user then use the `-f` flag:

```sh
github_monitor github_username -f
```

If you want to get the list of recent GitHub events for the user then use the `-l` flag. You can also add the `-n` flag to specify how many events should be displayed. By default, it shows the last 5 events.

```sh
github_monitor github_username -l -n 10
```

If you want to not only display, but also save the list of recent GitHub events to a CSV file, use the `-l` flag with `-b` indicating the CSV file. As before, you can add the `-n` flag to specify how many events should be displayed/saved:

```sh
github_monitor github_username -l -n 10 -b github_username.csv
```

<a id="email-notifications"></a>
## Email Notifications

To enable email notifications for all user profile changes (e.g. changes in followers, followings, starred repositories, username, email, bio, location, blog URL and number of repositories):

- set `PROFILE_NOTIFICATION` to `True`
- or use the `-p` flag

```sh
github_monitor github_username -p
```

To receive email notifications when new GitHub events appear for the user (e.g. new pushes, PRs, issues, forks, releases etc.):

- set `EVENT_NOTIFICATION` to `True`
- or use the `-s` flag

```sh
github_monitor github_username -s
```

To get email notifications when changes in user repositories are detected (e.g. changes in stargazers, watchers, forks, issues, PRs, discussions, descriptions, etc., except for the update date):

- set `REPO_NOTIFICATION` to `True`
- or use the `-q` flag

```sh
github_monitor github_username -j -q
```

To be informed whenever changes in the update date of user repositories are detected:

- set `REPO_UPDATE_DATE_NOTIFICATION` to `True`
- or use the `-u` flag

```sh
github_monitor github_username -j -u
```

The last two options (`-q` and `-u`) only work if tracking of repositories changes is enabled (`-j`).

To be informed about a user's daily contributions:

- set `CONTRIB_NOTIFICATION` to `True`
- or use the `-y` flag

```sh
github_monitor github_username -m -y
```

The `-y` flag only works if tracking of daily contributions is enabled (`-m`).

To disable sending an email on errors and the recovery alert that follows (both enabled by default):

- set `ERROR_NOTIFICATION` to `False`
- or use the `-e` / `--no-error-notify` flag

```sh
github_monitor github_username -e
```

Email and webhook error alerts are sent after **5 minutes** of a continuing failure. Problems that need your action, such as a rejected token, alert immediately. Each kind of failure alerts once per channel. Failed deliveries are retried after 5 minutes, with increasing waits up to an hour. A new outage after a recovery alerts again. A channel that could not receive the failure alert while the outage lasted is told about the failure and its recovery together, so a blocked channel is not left without any word of an outage.

A failure alert carries the subject `GitHub Monitor error: <what went wrong> (user: <username>)` and lists the fix, the guide link, how many checks failed in a row, since when and when the next retry is. When the failure clears, a matching `GitHub Monitor recovered: ...` alert goes to the channels the failure alert reached. `-e` / `--no-error-notify` switches both off for email and `--no-webhook-error-notify` switches both off for webhooks.

Missing optional details, such as a push event's file list, are reported on screen without triggering an error alert. When several checks fail, the alert shows the action to take and the number of other failures.

You can combine all email notifications flags together if needed.

Make sure you defined your SMTP settings first, as described in [SMTP Settings](configuration.md#smtp-settings).

Example email:

<p align="center">
   <img src="https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/assets/github_monitor_email_notifications.png" alt="github_monitor_email_notifications" width="90%"/>
</p>

<a id="webhook-notifications"></a>
## Webhook Notifications

Webhook event controls mirror the email categories but work independently:

| Event | Config setting | CLI override |
| --- | --- | --- |
| Profile changes | `WEBHOOK_PROFILE_NOTIFICATION` | `--webhook-profile` |
| New GitHub events | `WEBHOOK_EVENT_NOTIFICATION` | `--webhook-events` |
| Repository changes | `WEBHOOK_REPO_NOTIFICATION` | `--webhook-repo-changes` |
| Repository update date changes | `WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION` | `--webhook-repo-update-date` |
| Daily contribution changes | `WEBHOOK_CONTRIB_NOTIFICATION` | `--webhook-daily-contribs` |
| Monitoring errors and recoveries | `WEBHOOK_ERROR_NOTIFICATION` | Enable with `--webhook-errors` or disable with `--no-webhook-error-notify` |

A monitoring error webhook carries the same title and fields as the error email, without the timestamp the webhook service shows itself, and the matching recovery alert follows on the same channel. `--no-webhook-error-notify` switches both off.

Use `--webhook` or `--no-webhook` to turn all configured webhook alerts on or off for one run. A category override also enables the master webhook switch. For example:

```sh
github_monitor github_username --webhook-profile --webhook-events
```

Repository webhook categories only work with `-j` or `--track-repos-changes`. Contribution webhooks only work with `-m` or `--track-contribs-changes`. Event webhooks are disabled when `-k` or `--no-monitor-events` is used.

The provider and destination can also be overridden for one run:

```sh
github_monitor github_username --webhook-provider ntfy --webhook-url "https://ntfy.sh/your-private-topic" --webhook-events
```

See [Webhook Settings](configuration.md#webhook-settings) for private URL setup, ntfy authentication and advanced payload customization.

<a id="csv-export"></a>
## CSV Export

If you want to save all GitHub user events, profile changes and repository updates to a CSV file, set `CSV_FILE` or use the `-b` flag:

```sh
github_monitor <github_target> -b github_username.csv
```

The file will be automatically created if it does not exist.

<a id="check-intervals"></a>
## Check Intervals

If you want to customize the polling interval, use the `-c` flag (or the `GITHUB_CHECK_INTERVAL` configuration option):

```sh
github_monitor <github_target> -c 900
```

It is generally not recommended to use values lower than 10 minutes as new events are very often delayed by the GitHub API.

`NET_MAX_RETRIES` defaults to 5 and counts the first request as an attempt. `NET_BASE_BACKOFF_SEC` sets the base retry delay and defaults to 5 seconds. GitHub rate-limit headers can specify a different wait. If a monitored feed remains unavailable after its attempts, its previous snapshot is kept and monitoring tries again on the next check.

`VERIFY_REPOSITORY_CLOSURES` defaults to `True`. Missing issues, pull requests and discussions require confirmation of their closed state, with a separate fixed limit of five extra HTTP requests per monitoring cycle across all repositories. These lookups do not use `NET_MAX_RETRIES` or follow redirects. Unverified items stay in the previous snapshot and are checked again on later cycles. Set `VERIFY_REPOSITORY_CLOSURES = False` to restore immediate disappearance-based alerts without verification requests. The verbose/debug startup summary shows the setting and shared budget. The budget shows `Inactive` when repository tracking or verification is disabled. See [Monitoring Mode](usage.md#monitoring-mode).

An interval below 30 seconds invites the GitHub rate limiter, which stops the tool seeing anything. `--doctor` warns when the configured interval is that short.
<a id="liveness-reminder"></a>
### Liveness Reminder

While nothing changes, the tool prints one reminder that it is still running:

```
* Monitoring healthy for <github_target>. No tracked change since the last check
Liveness check, timestamp:	Mon 08 Sep 2026, 09:15:05
```

Set `LIVENESS_CHECK_INTERVAL` to change it (default: 86400, i.e. 24 hours) or to 0 to switch it off.

Anything the tool prints about the target restarts the countdown, so a busy run stays quiet.

<a id="signal-controls-macoslinuxunix"></a>
## Signal Controls (macOS/Linux/Unix)

The tool has several signal handlers implemented which allow to change behavior of the tool without a need to restart it with new configuration options / flags.

List of supported signals:

| Signal | Description |
| ----------- | ----------- |
| USR1 | Toggle email notifications for all user's profile changes (-p) |
| USR2 | Toggle email notifications for new GitHub events (-s) |
| CONT | Toggle email notifications for user's repositories changes (except for update date) (-q) |
| PIPE | Toggle email notifications for user's repositories update date changes (-u) |
| URG | Toggle email notifications for user's daily contributions changes (-y) |
| TRAP | Increase the user check interval (by 1 min) |
| ABRT | Decrease the user check interval (by 1 min) |
| HUP | Reload secrets from .env file |

`SIGHUP` keeps command-line credentials and nonempty environment values exported before startup. Change those values and restart to replace them.

Send signals with `kill` or `pkill`, e.g.:

```sh
pkill -USR1 -f "github_monitor <github_target>"
```

As Windows supports limited number of signals, this functionality is available only on Linux/Unix/macOS.

<a id="coloring-log-output-with-grc"></a>
## Coloring Log Output with GRC

You can use [GRC](https://github.com/garabik/grc) to color logs.

The bundled recipe follows the same colors as the live output. It also covers the other monitors in the family, so one copy in `~/.grc/` colors every tool's logs.

Add to your GRC config (`~/.grc/grc.conf`):

```text
# monitoring log file
.*_monitor_.*\.log
conf.monitor_logs
```

Now copy the [conf.monitor_logs](https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/grc/conf.monitor_logs) to your `~/.grc/` and log files should be nicely colored when using the `grc` tool.

Example:

```sh
grc tail -F -n 100 github_monitor_<github_target>.log
```
