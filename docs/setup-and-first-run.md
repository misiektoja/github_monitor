# Setup & First Run

<a id="run-the-setup-wizard"></a>
## Run the setup wizard

Already installed? Run the setup command below for your installation and follow the prompts. Otherwise, start with [Installation](installation.md).

Setup asks who to monitor, the GitHub token, how often to check and which alerts and output files you want. You can review your answers before saving. Regular settings go in `github_monitor.conf` and private values go in `.env`. Keep `.env` private.

Press Enter to accept a default or Ctrl+C to cancel. Cancelling before saving leaves your files untouched. Cancelling after saving keeps the saved settings. For changes to an existing setup, see [Configuration File](configuration.md#configuration-file).

After saving, follow the offered Doctor checks and monitoring steps.

=== "PyPI"

    ```sh
    github_monitor --setup
    ```

=== "Manual Python script on macOS or Linux"

    ```sh
    python3 github_monitor.py --setup
    ```

=== "Manual Python script on Windows"

    ```powershell
    python github_monitor.py --setup
    ```

A **target** is the GitHub user whose activity you want to monitor. The wizard asks for a GitHub personal access token and validates it. See [GitHub Personal Access Token](#github-personal-access-token) for how to create one.

The polling prompts accept plain seconds or the `s`, `m`, `h` and `d` units. They show both the seconds and a readable form of the default.

With a saved target, running GitHub Monitor without a target starts monitoring that user. If no target is saved, an interactive no-argument run offers setup.

<a id="before-you-start"></a>
## Before you start

You need two things before the first monitoring run:

1. A GitHub target. Either a username or a complete profile URL works.
2. A GitHub personal access token with the access needed for the accounts and repositories you monitor. See [GitHub Personal Access Token](#github-personal-access-token).

<a id="github-personal-access-token"></a>
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

<a id="not-sure-which-command-you-need"></a>
## Not sure which command you need?

| I want to... | Run this |
| --- | --- |
| Set up GitHub Monitor for the first time | Use the setup command for your installation above |
| Start monitoring with existing authentication | `github_monitor <github_target>`, where the target is a username or complete profile URL |
| Start the target saved in `TARGET_GITHUB_USERNAME` | `github_monitor --config-file github_monitor.conf` |
| Check the token, connectivity and one target | `github_monitor --doctor <github_target>` |
| Most securely enter or replace `GITHUB_TOKEN` | Run `github_monitor --set-github-token` and enter the token at the hidden prompt |
| Save an SMTP password for email alerts | Run `github_monitor --set-smtp-password` |
| Send a test email | Run `github_monitor --send-test-email` |
| Set up webhook alerts | Run the setup wizard and choose webhook alerts |
| Save a new webhook URL | Run `github_monitor --set-webhook-url` |
| Send a test webhook | Run `github_monitor --send-test-webhook` |
| List the user's repositories with stats | `github_monitor <github_target> -r` |
| List the user's starred repositories | `github_monitor <github_target> -g` |
| List followers and followings | `github_monitor <github_target> -f` |
| List recent events | `github_monitor <github_target> -l -n 10` |
| Write every change to a CSV file | `github_monitor <github_target> -b changes.csv` |
| List every supported command-line flag | `github_monitor --help` |

<a id="run-individual-commands"></a>
## Run Individual Commands

The examples below use PyPI. For a manual script, replace `github_monitor` with `python3 github_monitor.py` on macOS or Linux. Use `python github_monitor.py` on Windows and run it from the directory holding the script or give its full path. See [Command Format by Installation Method](usage.md#command-format-by-installation-method).

Throughout this page `<github_target>` means a GitHub username or a complete profile URL.

<a id="save-the-github-token"></a>
### Save the GitHub token

To configure authentication without the wizard, `--set-github-token` is the recommended and most secure entry method. It reads the token through a hidden prompt, so the value does not appear on screen or in the command line. It validates the token with GitHub before updating only `GITHUB_TOKEN`. If validation fails, it does not change the `.env` file.

```sh
github_monitor --set-github-token
```

The `-t` and `--github-token` options still work, but their values may appear in shell history or process listings.

<a id="save-notification-credentials"></a>
### Save notification credentials

The SMTP password is entered through a hidden prompt, checked against the mail server and saved as `SMTP_PASSWORD` in `.env`:

```sh
github_monitor --set-smtp-password
```

A webhook URL is the private address used to deliver notifications. Treat it like a password because anyone who has it may be able to post through it. Follow the [webhook setup steps](configuration.md#webhook-settings) then save the link:

```sh
github_monitor --set-webhook-url
```

The link is entered through a hidden prompt and saved as `WEBHOOK_URL` in `.env`. This command only saves the link. It does not turn on webhook alerts or send a message. See [Webhook Settings](configuration.md#webhook-settings) to choose your alerts then run `github_monitor --send-test-webhook` to test them.

<a id="start-monitoring"></a>
### Start monitoring

The first example uses a positional target. The second uses a saved `TARGET_GITHUB_USERNAME`:

```sh
github_monitor <github_target>
github_monitor --config-file github_monitor.conf
```

For a [manual script](installation.md#install-the-manual-script):

```sh
python3 github_monitor.py <github_target>
```

To check the setup before the first run, without writing anything:

```sh
github_monitor --doctor <github_target>
```

See [Doctor Preflight](troubleshooting.md#doctor-preflight) for what it reports.

To see all supported command-line arguments and flags:

```sh
github_monitor --help
```

<a id="next-step"></a>
## Next Step

Run [Doctor](troubleshooting.md#doctor-preflight) before an unattended run to confirm the token, connectivity and notification settings.

With the token saved and a first run working, continue to [Configuration](configuration.md) for targets, SMTP, webhooks and secrets. See [Usage](usage.md) for command formats, monitoring, listing commands, notifications and output files.
