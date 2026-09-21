"""Tests for documented event configuration and retry behavior."""

from unittest.mock import Mock

import requests


# Confirms the configured event list matches documented Events API types
def test_event_configuration_uses_supported_types(gm_module):
    assert "DiscussionEvent" in gm_module.EVENTS_TO_MONITOR
    assert "DeploymentEvent" not in gm_module.EVENTS_TO_MONITOR
    assert "CheckRunEvent" not in gm_module.EVENTS_TO_MONITOR
    assert "WorkflowRunEvent" not in gm_module.EVENTS_TO_MONITOR


# Locks the intentional single-page user event monitoring limit
def test_event_window_remains_one_page(gm_module):
    assert gm_module.EVENTS_NUMBER == 30


# Confirms exhausted retries return the caller supplied safe default
def test_gh_call_returns_configured_default(gm_module):
    failure = Mock(side_effect=requests.RequestException("offline"))
    failure.__name__ = "offline_request"
    marker = object()
    result = gm_module.gh_call(failure, retries=2, backoff=0, default=marker)()
    assert result is marker
    assert failure.call_count == 2


# Confirms a retry line names the work and the classified failure rather than the wrapped lambda and a raw library message
def test_gh_call_retry_line_names_the_operation(gm_module, capsys):
    failure = Mock(side_effect=requests.exceptions.ConnectTimeout("HTTPSConnectionPool(host='api.github.com', port=443): Read timed out."))

    gm_module.gh_call(failure, retries=2, backoff=0, operation="Public repository list")()

    output = capsys.readouterr().out
    assert "* Public repository list failed: GitHub did not answer in time (retry 1/2)" in output
    assert "<lambda>" not in output
    assert "HTTPSConnectionPool" not in output
