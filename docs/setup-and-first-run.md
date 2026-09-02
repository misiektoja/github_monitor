# Setup & First Run

## Guided Setup

The easiest first run is the guided setup wizard:

```sh
github_monitor --setup
```

It asks for the target, whether to save it, the polling interval, GitHub authentication, optional email and webhook alerts and output destinations. Polling accepts seconds or values such as `30s`, `2m`, `1.5h`, `1h 30m` and `1d`. The existing automatic timezone setting is retained instead of adding another setup question. Answers stay in memory until the complete summary is reviewed. Choose **Save settings** to write non-secret settings to `github_monitor.conf` and private values to a separate mode-0600 `.env` file. Existing destinations receive timestamped mode-0600 backups before replacement.

The wizard links to GitHub's token settings then validates a newly entered token before saving it. Every answer the wizard cannot use offers a way out, so one value you cannot produce right now does not cost you the answers already given: a blank answer asks whether to continue without it and names what stops working, a rejected one offers to enter it again and declining a webhook destination leaves that channel and its alerts off. Email setup signs in to the mail server before saving, so a wrong password or an unreachable host is caught during setup instead of at the first alert. No email is sent. A refused sign-in offers the mail server questions again, and if the server was only unreachable the answers are kept so `--doctor` can check them later. After saving, the wizard offers the read-only Doctor preflight then monitoring. Both prompts default to yes when the saved setup is ready. Commands after setup match a PyPI install or downloaded script and include the selected config plus dotenv paths.

`--setup --config-file PATH --env-file PATH` selects custom wizard destinations. Setup parses an existing config as data and preserves its supported settings. It moves usable secrets found there into the dotenv output. Nothing is written during questioning or section edits. **Save settings** validates the complete generated config then prepares both files before replacing either destination.

## Quick Start

Run the tool without arguments to see the same first-run screen used across the monitor tools. It uses short portable commands instead of the active interpreter and absolute script paths:

```text
For <github_target>, use a GitHub username or complete profile URL.

Quickest start (already configured):
    python3 github_monitor.py <github_target>

Easiest start (guided setup wizard):
    python3 github_monitor.py --setup

Check setup before monitoring:
    python3 github_monitor.py --doctor <github_target>

Full options: python3 github_monitor.py --help
```

A PyPI install prints `github_monitor` instead of `python3 github_monitor.py`. Windows prints `python github_monitor.py`. An interactive terminal offers the setup wizard with a default-yes prompt. A non-interactive `--setup` run explains how to use `--generate-config` instead.

When setup saves the target, later runs can omit it. A positional target still overrides `TARGET_GITHUB_USERNAME` for one run. If no target is saved, running the tool without arguments shows the first-run screen above.

For manual setup, create a [GitHub personal access token](#github-personal-access-token) then validate and save it through the hidden prompt:

```sh
github_monitor --set-github-token
```

Start monitoring `github_username`:

```sh
github_monitor github_username
```

Or if you installed [manually](installation.md#manual-installation):

```sh
python3 github_monitor.py --setup
python3 github_monitor.py <github_username>
```

To get the list of all supported command-line arguments / flags:

```sh
github_monitor --help
```

## GitHub Personal Access Token

Go to your GitHub token settings: [https://github.com/settings/tokens](https://github.com/settings/tokens)

Then create a personal access token with the access needed for the accounts and repositories you monitor.

The preferred method validates the token against the configured GitHub API before saving it to `.env`. Input is hidden and the dotenv file is changed only after GitHub returns the authenticated login:

```sh
github_monitor --set-github-token
```

Use `--env-file` to select another private settings file:

```sh
github_monitor --set-github-token --env-file /path/.env-github_monitor
```

GitHub Enterprise users can validate against their HTTPS API URL in the same step:

```sh
github_monitor --set-github-token --github-url "https://github.example/api/v3"
```

Fallback methods are:

- Set `GITHUB_TOKEN` as an [environment variable](configuration.md#storing-secrets)
- Add `GITHUB_TOKEN=...` manually to a [dotenv file](configuration.md#storing-secrets)
- Pass it for one run with `-t` or `--github-token`, which may leave it in shell history or process listings
- Hard-code it in the configuration file or source code

If you update `GITHUB_TOKEN` in the active dotenv file, send a `SIGHUP` signal to reload it without restarting the tool. More information is available in [Storing Secrets](configuration.md#storing-secrets) and [Signal Controls](usage.md#signal-controls-macoslinuxunix).
