# Usage

<a id="command-format"></a>
## Command Format by Installation Method

Examples use the PyPI command. For a downloaded script, run commands from the directory containing `github_monitor.py` and keep the same arguments:

| Installation | Command |
| --- | --- |
| PyPI or pipx | `github_monitor [OPTIONS]` |
| Manual script on macOS or Linux | `python3 github_monitor.py [OPTIONS]` |
| Manual script on Windows | `python github_monitor.py [OPTIONS]` |

For example, `github_monitor --setup` becomes `python3 github_monitor.py --setup` on macOS or Linux. Use `python` on Windows. Replace placeholders such as `<github_target>` with a GitHub username or complete profile URL.

The manual-script prefix names the file rather than its path, so run it from the directory holding `github_monitor.py`. From another directory, use the full path instead, for example `python3 /opt/github-monitor/github_monitor.py --setup`. The commands the tool prints after setup and Doctor use the same short form.

For first-time configuration, follow [Setup & First Run](setup-and-first-run.md). Use [Doctor Preflight](troubleshooting.md#doctor-preflight) to check a setup before monitoring.

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

The tool automatically saves its output to a `github_monitor_<username>.log` file. It can be changed in the settings via the `GITHUB_LOGFILE` configuration option or disabled completely via `DISABLE_LOGGING` / the `-d` flag.

Set `ASCII_LOG_SEPARATORS` to `"Auto"` (default) to use ASCII separator-only lines on Windows, `"On"` to use them on every operating system or `"Off"` to preserve Unicode separators in logs everywhere. Terminal separators stay Unicode. Log files and all other logged text remain UTF-8.

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

To disable sending an email on errors (enabled by default):

- set `ERROR_NOTIFICATION` to `False`
- or use the `-e` flag

```sh
github_monitor github_username -e
```

An error alert goes out once the same failure has lasted **5 minutes**, so a short outage or one lost request reaches nobody, while a failure that cannot clear on its own, such as a rejected token, is alerted at once. Each kind of failure alerts once per channel. A channel that could not deliver is tried again on a later failing check, after **5 minutes** at first and then after twice the previous wait, up to an hour. A run that recovered alerts again when it fails later. The same rule governs the webhook error alert.

You can combine all email notifications flags together if needed.

Make sure you defined your SMTP settings first, as described in [SMTP Settings](configuration.md#smtp-settings).

Example email:

<p align="center">
   <img src="https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/assets/github_monitor_email_notifications.png" alt="github_monitor_email_notifications" width="90%"/>
</p>

## Webhook Notifications

Webhook event controls mirror the email categories but work independently:

| Event | Config setting | CLI override |
| --- | --- | --- |
| Profile changes | `WEBHOOK_PROFILE_NOTIFICATION` | `--webhook-profile` |
| New GitHub events | `WEBHOOK_EVENT_NOTIFICATION` | `--webhook-events` |
| Repository changes | `WEBHOOK_REPO_NOTIFICATION` | `--webhook-repo-changes` |
| Repository update date changes | `WEBHOOK_REPO_UPDATE_DATE_NOTIFICATION` | `--webhook-repo-update-date` |
| Daily contribution changes | `WEBHOOK_CONTRIB_NOTIFICATION` | `--webhook-daily-contribs` |
| Monitoring errors | `WEBHOOK_ERROR_NOTIFICATION` | Enable with `--webhook-errors` or disable with `--no-webhook-error-notify` |

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

## CSV Export

If you want to save all GitHub user events, profile changes and repository updates to a CSV file, set `CSV_FILE` or use the `-b` flag:

```sh
github_monitor <github_target> -b github_username.csv
```

The file will be automatically created if it does not exist.

## Signal Controls (macOS/Linux/Unix)

The tool has several signal handlers implemented which allow changing the behavior of the tool without a need to restart it with new configuration options / flags.

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

Send signals with `kill` or `pkill`, e.g.:

```sh
pkill -USR1 -f "github_monitor <github_target>"
```

As Windows supports a limited number of signals, this functionality is available only on Linux/Unix/macOS.

## Terminal Colours

`COLORED_OUTPUT` controls whether live terminal output is coloured. It defaults to `True` and is read before the startup banner is printed, so a configured value applies to the first line. `--no-color` disables colour for one run. Colour also switches itself off when output is redirected or piped, when `TERM` is unset or `dumb` and when the standard [`NO_COLOR`](https://no-color.org/) environment variable is set. Log files always remain plain text with ANSI escape sequences stripped.

The `--help` screen is coloured too. Group headings, option names, the values those options take, the example commands and the comments above them each get their own colour, so the screen can be scanned instead of read.

`COLOR_THEME` overrides individual colours. It is merged over the built-in theme, so name only the parts you want to change:

Generated configuration files ship this block commented out, so the built-in defaults apply and a later change to them reaches you. A configuration file written by an earlier version sets every colour explicitly and therefore keeps the old ones: delete its `COLOR_THEME` block to follow the current defaults, or edit the values you want to keep. Such a file still loads unchanged.

```ini
COLOR_THEME = { "repository": "bright_magenta bold", "username": "green" }
```

A value combines one colour with any number of style attributes separated by spaces or `+`. Examples include `"bright_cyan bold"`, `"red underline"` and `"bright_magenta bold underline"`. An empty string leaves that part uncoloured.

| Colours | Styles |
| --- | --- |
| `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white` and the matching `bright_` variants such as `bright_red` | `bold`, `dim`, `underline`, `blink` |

| Theme key | Colours |
| --- | --- |
| `header` | The startup banner plus Setup Wizard and Doctor headings |
| `section` | Commands the wizard tells you to run and Doctor section names |
| `username` | GitHub usernames, display names and user context values |
| `id` | Event, review and commit identifiers |
| `status_online` | Public, online, available and unblocked states, including `Public profile: Yes` and `Blocked by the user: No` |
| `status_offline` | Private, blocked and offline states, including `Public profile: No` and `Blocked by the user: Yes` |
| `status_other` | Unknown or any other reported status value |
| `repository` | Repository names |
| `event` | Event types plus release, issue and discussion titles |
| `commit` | Commit messages |
| `branch` | Branches, refs and target commitish values |
| `duration` | Polling intervals and elapsed times |
| `timestamp_label` | The `Timestamp:` label. Empty by default so the label stays plain |
| `timestamp_value` | Timestamp values |
| `info` | Informational lines, prompts and recovery actions |
| `warning` | Warning lines and wizard validation notices |
| `error` | Error lines and failed verdicts |
| `signal` | Received-signal lines |
| `email` | Email addresses and email delivery lines |
| `webhook` | Webhook delivery lines |
| `date` | Single dates and times |
| `date_range` | Date and hour ranges |
| `boolean_true` | `True`, `Enabled`, `On` and Doctor PASS values |
| `boolean_false` | `False`, `Disabled`, `Off` and Doctor FAIL values |
| `count_up` | Values in reported increases such as `from 10 to 12` and `(+2)` |
| `count_down` | Values in reported decreases such as `from 12 to 10` and `(-2)` |
| `link` | HTTP and HTTPS links |
| `help_heading` | The `--help` group headings and example task names |
| `help_usage` | The `usage:` label |
| `help_option` | Option names such as `--doctor` |
| `help_metavar` | The value each option takes, such as a path or a number of seconds |
| `help_placeholder` | Values to replace in the help examples |
| `help_command` | The commands in the help examples |
| `help_comment` | The `#` comment above each help example |
| `help_default` | The `(default: ...)` notes |

Static counts stay plain. Only values that report a change receive `count_up` or `count_down`.

`TRUNCATE_CHARS` limits visible terminal width without shortening log lines. `--truncate N` overrides it for one run. Use `999` to detect the current terminal width. Truncation is ignored when logging is disabled. Install the optional `wcwidth` package for correct display widths with wide Unicode characters.

On Windows install the optional `colorama` package for the best results in classic Command Prompt. Windows Terminal needs no additional package.

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
grc tail -F -n 100 github_monitor_<username>.log
```
