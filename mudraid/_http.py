"""Internal HTTP client for MudraID's control-plane endpoints.

This module is the *single* place inside the SDK that talks to MudraID
itself (as opposed to the platforms the agent calls). Both
:mod:`mudraid._token_manager` and :mod:`mudraid._platform_resolver`
route their HTTP traffic through here so:

  - base-URL joining is consistent
  - status-code → exception mapping is consistent (resists drift)
  - timeouts have one default
  - the underlying ``requests.Session`` is reused (connection pooling)
  - a future addition of correlation IDs / metrics / TLS pinning
    has exactly one site to touch.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from mudraid._env import SdkConfig
from mudraid.exceptions import MudraIDAuthError, MudraIDNetworkError, MudraIDRevokedError

_logger = logging.getLogger("mudraid.http")

_DEFAULT_TIMEOUT_SEC = 10.0


def _safe_detail(response: requests.Response) -> str | None:
    """Best-effort extraction of the server's `detail` field.

    Errors and non-JSON bodies are swallowed — we never let detail
    extraction itself raise. Returns ``None`` when no usable detail
    is available; callers should fall back to their own default
    message.
    """
    try:
        body = response.json()
    except ValueError:
        return None
    if isinstance(body, dict):
        detail = body.get("detail") or body.get("message")
        if isinstance(detail, str) and detail:
            return detail
    return None


class MudraIDHttpClient:
    """Thin HTTP client for MudraID's own API surface.

    Not for use against the platforms the agent calls — those go
    through ``requests`` directly (with the Bearer JWT attached) in
    :mod:`mudraid._agent`.
    """

    def __init__(self, config: SdkConfig, timeout: float = _DEFAULT_TIMEOUT_SEC) -> None:
        self._config = config
        self._timeout = timeout
        # A Session lets us reuse the TCP connection across the
        # bootstrap call and the per-platform token mints — meaningful
        # latency saving on agents that talk to multiple platforms.
        self._session = requests.Session()

    @property
    def base_url(self) -> str:
        return self._config.base_url

    @property
    def api_key_id(self) -> str:
        return self._config.api_key_id

    @property
    def secret(self) -> str:
        # Module-internal. Never logged; never exposed via Agent.
        return self._config.secret

    def post_json(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        """POST a JSON body to ``base_url + path`` and return the parsed response.

        Maps responses to SDK exceptions:

          * 2xx with valid JSON → parsed dict returned.
          * 401 → :class:`MudraIDAuthError`.
          * 403 → :class:`MudraIDRevokedError`, message taken from the
            server's ``detail`` when present.
          * Network failure / timeout / non-JSON / other non-2xx →
            :class:`MudraIDNetworkError`.

        The request body is *not* echoed into any exception message —
        it contains the agent's plaintext secret.
        """
        url = f"{self._config.base_url}{path}"
        # `path` is logged; `body` is NOT. The MudraID request body
        # contains the agent's plaintext secret — it must never appear
        # in logs, exception messages, or any other diagnostic output.
        _logger.debug("POST %s", path)
        try:
            response = self._session.post(url, json=body, timeout=self._timeout)
        except requests.RequestException as exc:
            # Chain the underlying transport error for debuggability,
            # but keep the surfaced message generic so it never echoes
            # the request body.
            raise MudraIDNetworkError(
                f"could not reach MudraID at {self._config.base_url}"
            ) from exc

        _logger.debug("MudraID returned %d for %s", response.status_code, path)

        if response.status_code == 401:
            raise MudraIDAuthError("invalid credentials")
        if response.status_code == 403:
            detail = _safe_detail(response) or (
                "agent not authorized for this MudraID call; check platform "
                "grants in the MudraID portal"
            )
            raise MudraIDRevokedError(detail)
        if not 200 <= response.status_code < 300:
            raise MudraIDNetworkError(f"unexpected status {response.status_code} from MudraID")

        try:
            return response.json()
        except ValueError as exc:
            raise MudraIDNetworkError("MudraID returned a non-JSON response") from exc

    def close(self) -> None:
        self._session.close()
