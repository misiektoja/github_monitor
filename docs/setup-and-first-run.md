# Setup & First Run

## Guided Setup

The easiest first run is the guided setup wizard:

```sh
github_monitor --setup
```

It asks for the target, whether to save it, the polling interval, GitHub authentication, optional email and webhook alerts and output destinations. Polling accepts seconds or values such as `30s`, `2m`, `1.5h`, `1h 30m` and `1d`. The existing automatic timezone setting is retained instead of adding another setup question. Answers stay in memory until the complete summary is reviewed. Choose **Save settings** to write non-secret settings to `github_monitor.conf` and private values to a separate mode-0600 `.env` file. The dotenv file is created only when a private value was entered, so a run that saves no secret leaves the config on its own. An existing configuration file receives a timestamped mode-0600 backup before replacement. The dotenv file is replaced without a backup, so a secret you replace is not left behind in a `.bak` file. A rebuilt file starts from the settings already in place with your answers applied over them. A section you decline is cleared rather than carried over, so declining email leaves no mail server behind.

The wizard links to GitHub's token settings then validates a newly entered token before saving it. Every answer the wizard cannot use offers a way out, so one value you cannot produce right now does not cost you the answers already given: a blank answer asks whether to continue without it and names what stops working, a rejected one offers to enter it again and declining a webhook destination leaves that channel and its alerts off. Email setup signs in to the mail server before saving, so a wrong password or an unreachable host is caught during setup instead of at the first alert. No email is sent. A refused sign-in offers the mail server questions again, and if the server was only unreachable the answers are kept so `--doctor` can check them later. After saving, the wizard offers the read-only Doctor preflight whenever a target was given, so a setup that still has no token can see what is missing, then offers monitoring. Both prompts default to yes when the saved setup is ready. Commands after setup match a PyPI install or downloaded script and name the selected config plus the dotenv file when one was written.

`--setup --config-file PATH --env-file PATH` selects custom wizard destinations. Both destinations are checked before the first question, so an unwritable path or a directory given by mistake is reported straight away rather than after you have answered everything. When the configuration file already exists it asks whether to replace it and offers to write somewhere else instead. Setup parses an existing config as data and preserves its supported settings. It moves usable secrets found there into the dotenv output. Nothing is written during questioning or section edits. The summary's **File destinations** section changes where the configuration and dotenv files are written. Moving the dotenv file asks the authentication and notification questions again, since a secret you chose to keep was never going to reach the new file. **Save settings** validates the complete generated config then prepares every file it writes before replacing any destination.

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

A PyPI install prints `github_monitor` instead of `python3 github_monitor.py`. Windows prints `python github_monitor.py`. An interactive terminal offers the setup wizard with a default-yes prompt. A non-interactive `--setup` run explains how to use `--generate-config` instead. `--setup` needs somewhere to put both files, so it refuses `--config-file none` and `--env-file none`.

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
python3 github_monitor.py <github_target>
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
