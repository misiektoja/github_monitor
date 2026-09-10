# Setup & First Run

## Before You Start

Install the tool using [Installation](installation.md). You will need a GitHub username or complete profile URL and the [GitHub personal access token](#github-personal-access-token). The wizard collects credentials through hidden prompts.

Open a terminal in the directory where you want to keep the configuration and monitoring output. Later commands should use that directory or explicitly select the same `--config-file` and `--env-file` paths. Manual installations use the [command equivalents](usage.md#command-format).

<a id="setup-wizard"></a>
## Guided Setup

The easiest first run is the guided setup wizard:

```sh
github_monitor --setup
```

The wizard asks for the target, polling interval, GitHub token, optional email and webhook alerts and output files. Polling accepts seconds or durations such as `30s`, `2m`, `1.5h`, `1h 30m` and `1d`.

Review the summary and change any section before choosing **Save settings**. Regular settings go to `github_monitor.conf` and private values go to `.env`. Setup asks before replacing an existing configuration and keeps a timestamped backup. On a rerun, saved settings provide the defaults. Declining a section disables it, including any previously configured alerts. See [Storing Secrets](configuration.md#storing-secrets) for credential storage and backup details.

Setup validates your GitHub token and checks email sign-in without sending a message. After saving, it offers [Doctor Preflight](troubleshooting.md#doctor-preflight) when a target is available, then offers to start monitoring if the checks pass.

Use `--config-file PATH` and `--env-file PATH` or the summary's **File destinations** section to choose other files. Both paths must be writable. `--config-file none` and `--env-file none` are not supported by setup.

## Quick Start

The commands printed below match the installation method and quote selected paths containing spaces.

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

A PyPI install uses `github_monitor`. For manual installations, use `python3 github_monitor.py` on macOS or Linux and `python github_monitor.py` on Windows. Setup needs an interactive terminal. In scripts, use `--generate-config` instead.

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

Use the hidden prompt to validate your token with GitHub and save it to `.env`:

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

## Continue with Usage

Use [Usage](usage.md) for monitoring and output options or [Configuration](configuration.md) to adjust saved settings. If setup or monitoring fails, run [Doctor Preflight](troubleshooting.md#doctor-preflight) and follow the reported recovery steps.
