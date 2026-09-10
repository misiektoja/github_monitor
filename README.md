# github_monitor

<p align="left">
  <img src="https://img.shields.io/github/v/release/misiektoja/github_monitor?style=flat-square&color=blue" alt="GitHub Release" />
  <img src="https://img.shields.io/pypi/v/github_monitor?style=flat-square&color=teal" alt="PyPI Version" />
  <img src="https://img.shields.io/github/stars/misiektoja/github_monitor?style=flat-square&color=magenta" alt="GitHub Stars" />
  <img src="https://img.shields.io/badge/python-3.10+-blueviolet?style=flat-square" alt="Python Versions" />
  <img src="https://img.shields.io/github/license/misiektoja/github_monitor?style=flat-square&color=blue" alt="License" />
  <img src="https://img.shields.io/github/last-commit/misiektoja/github_monitor?style=flat-square&color=green" alt="Last Commit" />
  <img src="https://img.shields.io/badge/maintenance-active-brightgreen?style=flat-square" alt="Maintenance" />
</p>

Powerful real-time GitHub OSINT tool that tracks everything from profile updates and contribution streaks to repository engagement and follower changes - even detecting when you've been blocked, all with instant email and webhook notifications.

<p align="center">
   <img src="https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/assets/github_monitor.png" alt="github_monitor_screenshot" width="100%"/>
</p>

**Full documentation: [misiektoja.github.io/github_monitor](https://misiektoja.github.io/github_monitor/)**

<a id="-quick-install-run"></a>
### 🚀 Quick Install & Run

New to Python or unsure what is installed? Follow the [Python install walkthrough](https://misiektoja.github.io/github_monitor/installation/#new-to-python-install-everything) first.

Install from PyPI:

```sh
pip install github_monitor
```

Run the setup wizard:

```sh
github_monitor --setup
```

The wizard asks for the target, authentication, polling intervals and optional notifications. Review the settings before saving them. See [Setup & First Run](https://misiektoja.github.io/github_monitor/setup-and-first-run/) for the service-specific steps.

For the manual single-file method, dependencies and upgrade commands, see [Installation](https://misiektoja.github.io/github_monitor/installation/).

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

## Common Commands

Use [Quick Install & Run](#-quick-install-run) for first-time setup. These examples use the PyPI command. See [Command Format by Installation Method](https://misiektoja.github.io/github_monitor/usage/#command-format) for manual-script equivalents.

Replace the target placeholders with a GitHub username or complete profile URL. Monitoring requires the [GitHub personal access token](https://misiektoja.github.io/github_monitor/setup-and-first-run/#github-personal-access-token) described in the setup guide.

| I want to... | Run this |
| --- | --- |
| Configure the target, credentials and alerts | `github_monitor --setup` |
| Start monitoring with saved credentials | `github_monitor <github_target>` |
| Check setup before monitoring | `github_monitor --doctor <github_target>` |
| Enter or replace credentials through hidden prompts | `github_monitor --set-github-token` |
| Use a specific configuration and secrets file | `github_monitor --config-file github_monitor.conf --env-file .env <github_target>` |
| List public repositories | `github_monitor <github_target> -r` |
| List every supported command-line option | `github_monitor --help` |

Monitoring runs until you press `Ctrl+C`. For email, Discord and ntfy alerts, CSV output and service-specific commands, see [Usage](https://misiektoja.github.io/github_monitor/usage/). If a run fails, start with [Doctor Preflight](https://misiektoja.github.io/github_monitor/troubleshooting/#doctor-preflight).

## Documentation

| Page | What it covers |
| --- | --- |
| [Installation](https://misiektoja.github.io/github_monitor/installation/) | Python walkthrough, PyPI or manual installation, upgrades |
| [Setup & First Run](https://misiektoja.github.io/github_monitor/setup-and-first-run/) | The guided wizard, the personal access token, the first monitoring run |
| [Configuration](https://misiektoja.github.io/github_monitor/configuration/) | Config file, events and repositories to monitor, SMTP, webhooks, TLS verification, storing secrets, check intervals |
| [Usage](https://misiektoja.github.io/github_monitor/usage/) | Monitoring mode, listing mode, notifications, CSV export, signals, terminal colours |
| [Troubleshooting](https://misiektoja.github.io/github_monitor/troubleshooting/) | `--doctor` preflight checks, what to do when something fails, `--verbose` and `--debug` output |
| [Testing](https://misiektoja.github.io/github_monitor/testing/) | Running the offline suite, the linter and the docs build |
| [About](https://misiektoja.github.io/github_monitor/about/) | Change log, contributing, security, license, support |

## Change Log

See [RELEASE_NOTES.md](https://github.com/misiektoja/github_monitor/blob/main/RELEASE_NOTES.md).

## Contributing

Bug reports, documentation fixes and code contributions are welcome. See [CONTRIBUTING.md](https://github.com/misiektoja/github_monitor/blob/main/CONTRIBUTING.md) for the development setup, the checks CI enforces and what a change needs before it is merged. Participation is covered by the [Code of Conduct](https://github.com/misiektoja/github_monitor/blob/main/CODE_OF_CONDUCT.md).

## Security

Report a suspected vulnerability privately through [GitHub security advisories](https://github.com/misiektoja/github_monitor/security/advisories/new), never as a public issue. [SECURITY.md](https://github.com/misiektoja/github_monitor/blob/main/SECURITY.md) covers the reporting process, the supported versions and the security posture of stored credentials and configuration loading.

## License

Licensed under GPLv3. See [LICENSE](https://github.com/misiektoja/github_monitor/blob/main/LICENSE). Dependency licenses are listed in [THIRD_PARTY_NOTICES.md](https://github.com/misiektoja/github_monitor/blob/main/THIRD_PARTY_NOTICES.md).

## Support

Questions, bug reports and vulnerability reports each have a place, listed in [SUPPORT.md](https://github.com/misiektoja/github_monitor/blob/main/SUPPORT.md).

If the project is useful to you, you can support its development through [GitHub Sponsors](https://github.com/sponsors/misiektoja) or [Buy Me a Coffee](https://buymeacoffee.com/misiektoja).
