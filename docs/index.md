# github_monitor

Powerful real-time GitHub OSINT tool that tracks everything from profile updates and contribution streaks to repository engagement and follower changes - even detecting when you've been blocked, all with instant email and webhook notifications.

<a id="-quick-install"></a>
<a id="-quick-install-run"></a>
### 🚀 Quick Install & Run

New to Python or unsure what is installed? Follow the [Python install walkthrough](installation.md#new-to-python-install-everything) first.

Install from PyPI:

```sh
pip install github_monitor
```

Run the setup wizard:

```sh
github_monitor --setup
```

The wizard asks for the target, authentication, polling intervals and optional notifications. Review the settings before saving them. See [Setup & First Run](setup-and-first-run.md) for the service-specific steps.

For the manual single-file method, dependencies and upgrade commands, see [Installation](installation.md).

## Features

### Activity and Profile Tracking

* **GitHub events**: Track pushes, pull requests, issues, forks, releases and reviews.
* **Profile changes**: Detect changes to names, email, location, company, bio, blog URL, visibility and account metadata.
* **Connections and contributions**: Track followers, followed accounts, daily contributions and blocking or unblocking.

### Repository Insights

* **Repository lists**: Track added or removed public and starred repositories.
* **Repository changes**: Monitor stars, watchers, forks, issues, pull requests, discussions, descriptions and update dates.
* **Removal context**: Flag deleted accounts or repositories when reporting removals.
* **GitHub links**: Open repositories, commits, issues and other activity from console and email links.

### Notifications and History

* **Event alerts**: Send email, Discord and ntfy notifications with event-specific controls.
* **CSV history**: Save detected activity and profile changes with timestamps.
* **Terminal colours**: Customize the theme, with colours disabled when output is redirected.

### Setup and Configuration

* **Guided setup**: Configure a target, credentials and alerts with `--setup`, then check them with `--doctor`.
* **Flexible settings**: Use configuration files, dotenv files, environment variables and command-line options.
* **Runtime controls**: Adjust the running monitor through supported signals.
* **GitHub deployments**: Connect to public GitHub or GitHub Enterprise.

## Screenshots

<p align="center">
   <img src="https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/assets/github_monitor.png" alt="github_monitor_screenshot" width="100%"/>
</p>

<a id="common-commands"></a>
## Common Commands

Use [Quick Install & Run](#-quick-install-run) for first-time setup. These examples use the PyPI command. See [Command Format by Installation Method](usage.md#command-format) for manual-script equivalents.

Replace the target placeholders with a GitHub username or complete profile URL. Monitoring requires the [GitHub personal access token](setup-and-first-run.md#github-personal-access-token) described in the setup guide.

| I want to... | Run this |
| --- | --- |
| Configure the target, credentials and alerts | `github_monitor --setup` |
| Start monitoring with saved credentials | `github_monitor <github_target>` |
| Check setup before monitoring | `github_monitor --doctor <github_target>` |
| Enter or replace credentials through hidden prompts | `github_monitor --set-github-token` |
| Use a specific configuration and secrets file | `github_monitor --config-file github_monitor.conf --env-file .env <github_target>` |
| List public repositories | `github_monitor <github_target> -r` |
| List every supported command-line option | `github_monitor --help` |

Monitoring runs until you press `Ctrl+C`. For email, Discord and ntfy alerts, CSV output and service-specific commands, see [Usage](usage.md). If a run fails, start with [Doctor Preflight](troubleshooting.md#doctor-preflight).

## Documentation

* [Installation](installation.md) - Python setup, package or manual install and upgrades
* [Setup & First Run](setup-and-first-run.md) - credentials, target selection and the setup wizard
* [Configuration](configuration.md) - settings, notifications and secret storage
* [Usage](usage.md) - monitoring, output and command options
* [Troubleshooting](troubleshooting.md) - Doctor checks and recovery steps
