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

- **Real-time tracking** of GitHub users' activities, including profile and repository changes:
   - **new GitHub events** for the user like new pushes, PRs, issues, forks, releases, reviews etc.
   - **repository changes** such as updated stargazers, watchers, forks, issues, PRs, discussions, description and repo update dates
   - added/removed **followings and followers**
   - added/removed **starred repositories**
   - added/removed **public repositories**
   - detection whether a removal was caused by a **deleted account or repository**, flagged in the alert
   - changes in **user name, email, location, company, bio and blog URL**
   - changes in **profile visibility** (public to private and vice versa)
   - changes in **user's daily contributions**
   - detection when a **user blocks or unblocks you**
   - detection of **account metadata** changes (such as account update date)
- **Email and webhook notifications** through **Discord**, **ntfy** and custom Discord-format integrations for different events
- **Guided setup** with `--setup`, and **preflight diagnostics** with `--doctor`
- **Saving all user activities** with timestamps to the **CSV file**
- **Clickable GitHub URLs** printed in the console and included in email notifications (repos, PRs, commits, issues, releases etc.)
- **Coloured terminal output** with a configurable theme, switched off automatically when the output is redirected
- **Flexible configuration** through config files, dotenv files, environment variables and command-line arguments
- **Control of the running copy** through signals
- Support for **Public Web GitHub** and **GitHub Enterprise**
- **Functional, procedural Python** (minimal OOP)

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
