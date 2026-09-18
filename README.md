# github_monitor

[![GitHub Release](https://img.shields.io/github/v/release/misiektoja/github_monitor?style=flat-square&color=blue)](https://github.com/misiektoja/github_monitor/releases)
[![PyPI Version](https://img.shields.io/pypi/v/github_monitor?style=flat-square&color=teal)](https://pypi.org/project/github-monitor/)
[![GitHub Stars](https://img.shields.io/github/stars/misiektoja/github_monitor?style=flat-square&color=magenta)](https://github.com/misiektoja/github_monitor)
[![Python Versions](https://img.shields.io/badge/python-3.10+-blueviolet?style=flat-square)](https://pypi.org/project/github-monitor/)
[![License](https://img.shields.io/github/license/misiektoja/github_monitor?style=flat-square&color=blue)](https://github.com/misiektoja/github_monitor/blob/main/LICENSE)
[![OpenSSF Scorecard](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.scorecard.dev%2Fprojects%2Fgithub.com%2Fmisiektoja%2Fgithub_monitor&query=%24.score&label=openssf%20scorecard&style=flat-square)](https://scorecard.dev/viewer/?uri=github.com/misiektoja/github_monitor)
[![Last Commit](https://img.shields.io/github/last-commit/misiektoja/github_monitor?style=flat-square&color=green)](https://github.com/misiektoja/github_monitor/commits/main)
[![Maintenance](https://img.shields.io/badge/maintenance-active-brightgreen?style=flat-square)](https://github.com/misiektoja/github_monitor)

Powerful real-time GitHub OSINT tool that tracks everything from profile updates and contribution streaks to repository engagement and follower changes - even detecting when you've been blocked, all with instant email and webhook notifications.

<p align="center">
   <img src="https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/assets/github_monitor.png" alt="github_monitor_screenshot" width="100%"/>
</p>

<a id="quick-install-run"></a>
### 🚀 Quick Install & Run

New to Python or unsure what is installed? Follow the [Python install walkthrough](https://misiektoja.github.io/github_monitor/installation/#new-to-python-check-and-install) first.

Install from PyPI:

```sh
pip install github_monitor
```

Run the setup wizard:

```sh
github_monitor --setup
```

The wizard asks for the target, the GitHub token and optional notifications. Review the settings before saving them. See [Setup & First Run](https://misiektoja.github.io/github_monitor/setup-and-first-run/) for how to create the GitHub personal access token.

For the manual single-file method, dependencies and upgrade commands, see [Installation](https://misiektoja.github.io/github_monitor/installation/).

<a id="features"></a>
## Features

### 🔍 Activity and Profile Tracking

* **GitHub events**: Track pushes, pull requests, issues, forks, releases and reviews.
* **Profile changes**: Detect changes to names, email, location, company, bio, blog URL, visibility and account metadata.
* **Connections and contributions**: Track followers, followed accounts, daily contributions and blocking or unblocking.

### 📊 Repository Insights

* **Repository lists**: Track added or removed public and starred repositories.
* **Repository changes**: Monitor stars, watchers, forks, issues, pull requests, discussions, descriptions and update dates.
* **Removal context**: Flag deleted accounts or repositories when reporting removals.
* **GitHub links**: Open repositories, commits, issues and other activity from console and email links.

### 🔔 Notifications and History

* **Event alerts**: Send email, Discord and ntfy notifications with event-specific controls.
* **CSV history**: Save detected activity and profile changes with timestamps.
* **Terminal colours**: Customize the theme, with colours disabled when output is redirected.

### ⚙️ Setup and Configuration

* **Guided setup**: Configure a target, credentials and alerts with `--setup`, then check them with `--doctor`.
* **Flexible settings**: Use configuration files, dotenv files, environment variables and command-line options.
* **Runtime controls**: Adjust the running monitor through supported signals.
* **GitHub deployments**: Connect to public GitHub or GitHub Enterprise.

<a id="common-commands"></a>
## Common Commands

Use [Quick Install & Run](#-quick-install--run) above for first-time setup. The table uses PyPI commands. For the manual script equivalents, see [Run Individual Commands](https://misiektoja.github.io/github_monitor/setup-and-first-run/#run-individual-commands).

Replace the target placeholders with a GitHub username or complete profile URL. Monitoring requires the [GitHub personal access token](https://misiektoja.github.io/github_monitor/setup-and-first-run/#github-personal-access-token) described in the setup guide.

| I want to... | Run this |
| --- | --- |
| Configure the target, credentials and alerts | `github_monitor --setup` |
| Start monitoring with existing authentication | `github_monitor <github_target>` |
| Check authentication, connectivity and one target | `github_monitor --doctor <github_target>` |
| Enter or replace securely the GitHub personal access token | `github_monitor --set-github-token` |
| Configure and test webhook alerts | Use the setup wizard or follow [Webhook Settings](https://misiektoja.github.io/github_monitor/configuration/#webhook-settings) |
| Save an SMTP password for email alerts | `github_monitor --set-smtp-password` |
| Send a test email | `github_monitor --send-test-email` |
| Save a new webhook URL | `github_monitor --set-webhook-url` |
| Send a test webhook | `github_monitor --send-test-webhook` |
| List public repositories | `github_monitor <github_target> -r` |
| List starred repositories | `github_monitor <github_target> -g` |
| List followers and followings | `github_monitor <github_target> -f` |
| List the ten most recent events | `github_monitor <github_target> -l -n 10` |
| Write every change to a CSV file | `github_monitor <github_target> -b changes.csv` |
| Use a specific configuration and secrets file | `github_monitor --config-file github_monitor.conf --env-file .env <github_target>` |
| List every supported command-line flag | `github_monitor --help` |

Running the tool with no arguments offers the wizard if you have not saved a target. If a target is already saved, it starts monitoring that target.

The tool runs until interrupted (`Ctrl+C`). Use `tmux` or `screen` for persistence and run multiple copies to monitor several targets.

For the personal access token, saved targets and notification setup, see the [full Setup & First Run guide](https://misiektoja.github.io/github_monitor/setup-and-first-run/).

For the events and repositories to monitor, TLS verification, email and webhook setup, see [Configuration](https://misiektoja.github.io/github_monitor/configuration/). For notification choices, listing commands and output files, see [Usage](https://misiektoja.github.io/github_monitor/usage/).

If a run fails, start with [Doctor Preflight](https://misiektoja.github.io/github_monitor/troubleshooting/#doctor-preflight).

<a id="documentation"></a>
## Documentation

Full documentation is available at **[misiektoja.github.io/github_monitor](https://misiektoja.github.io/github_monitor/)**:

| Page | What it covers |
| --- | --- |
| [Installation](https://misiektoja.github.io/github_monitor/installation/) | Python walkthrough, PyPI or manual installation, upgrades |
| [Setup & First Run](https://misiektoja.github.io/github_monitor/setup-and-first-run/) | Setup wizard, the personal access token, the first monitoring run |
| [Configuration](https://misiektoja.github.io/github_monitor/configuration/) | Config file, events and repositories to monitor, SMTP, webhooks, TLS verification, storing secrets, check intervals |
| [Usage](https://misiektoja.github.io/github_monitor/usage/) | Monitoring mode, listing mode, notifications, CSV export, signals, terminal output |
| [Troubleshooting](https://misiektoja.github.io/github_monitor/troubleshooting/) | `--doctor` preflight checks, what to do when something fails, `--verbose` and `--debug` output |
| [Testing](https://misiektoja.github.io/github_monitor/testing/) | Running the offline suite, the linter and the docs build |
| [About](https://misiektoja.github.io/github_monitor/about/) | Change log, contributing, security, license, support |

<a id="change-log"></a>
## Change Log

See [RELEASE_NOTES.md](https://github.com/misiektoja/github_monitor/blob/main/RELEASE_NOTES.md).

<a id="contributing"></a>
## Contributing

Bug reports, documentation fixes and code contributions are welcome. See [CONTRIBUTING.md](https://github.com/misiektoja/github_monitor/blob/main/CONTRIBUTING.md) for the development setup, the checks CI enforces and what a change needs before it is merged. Participation is covered by the [Code of Conduct](https://github.com/misiektoja/github_monitor/blob/main/CODE_OF_CONDUCT.md).

<a id="security"></a>
## Security

Report a suspected vulnerability privately through [GitHub security advisories](https://github.com/misiektoja/github_monitor/security/advisories/new), never as a public issue. [SECURITY.md](https://github.com/misiektoja/github_monitor/blob/main/SECURITY.md) covers the reporting process, the supported versions and the security posture of stored credentials and configuration loading.

<a id="maintainers"></a>
## Maintainers

- **misiektoja** ([@misiektoja](https://github.com/misiektoja))

<a id="license"></a>
## License

Licensed under GPLv3. See [LICENSE](https://github.com/misiektoja/github_monitor/blob/main/LICENSE). Dependency licenses are listed in [THIRD_PARTY_NOTICES.md](https://github.com/misiektoja/github_monitor/blob/main/THIRD_PARTY_NOTICES.md).

<a id="support"></a>
## Support

Questions, bug reports and vulnerability reports each have a place, listed in [SUPPORT.md](https://github.com/misiektoja/github_monitor/blob/main/SUPPORT.md).

If the project is useful to you, you can support its development through [GitHub Sponsors](https://github.com/sponsors/misiektoja) or [Buy Me a Coffee](https://buymeacoffee.com/misiektoja).
