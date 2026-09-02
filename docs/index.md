# github_monitor

Powerful real-time GitHub OSINT tool that tracks everything from profile updates and contribution streaks to repository engagement and follower changes - even detecting when you've been blocked, all with instant email and webhook notifications.

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

## Get started

```sh
pip install github_monitor
```

The guided setup asks a few questions and writes a ready-to-run configuration:

```sh
github_monitor --setup
```

[Installation](installation.md) covers the requirements and the manual install. [Setup & First Run](setup-and-first-run.md) covers the wizard, the personal access token and the first monitoring run.

## Screenshots

<p align="center">
   <img src="https://raw.githubusercontent.com/misiektoja/github_monitor/refs/heads/main/assets/github_monitor.png" alt="github_monitor_screenshot" width="100%"/>
</p>
