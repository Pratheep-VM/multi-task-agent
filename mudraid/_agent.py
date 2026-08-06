"""Agent — public entry point of the MudraID SDK.

M4.5 wires the HTTP methods. Each call now:

  1. Resolves the URL's host to a ``platform_id`` via
     :class:`mudraid._platform_resolver.PlatformResolver`.
  2. Asks :class:`mudraid._token_manager.TokenManager` for a current
     JWT for that platform (cache hit, or mint on miss).
  3. Injects ``Authorization: Bearer <jwt>`` into the outgoing
     ``requests`` call, preserving every other ``requests`` kwarg.
  4. Returns the unmodified :class:`requests.Response`.

The 401-retry path (refresh + replay) lands in M4.6 — for now a
platform-side 401 surfaces to the developer as the response object,
the same as the underlying ``requests`` library would.

The class mirrors :class:`requests.Session` so an integrator's diff
is "``import requests``" → "``from mudraid import Agent``".
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from mudraid._env import SdkConfig, load_config
from mudraid._http import MudraIDHttpClient
from mudraid._platform_resolver import PlatformResolver
from mudraid._token_manager import TokenManager

_logger = logging.getLogger("mudraid.agent")


class Agent:
    """Authenticated HTTP client that speaks for one MudraID agent.

    .. note:: **Legacy machine-authority profile.**

        This class is the *legacy* auth profile: it authenticates with an
        api_key_id/secret pair against ``POST /api/v1/auth/token`` and — by
        design — lets an empty ``scopes`` request expand to the agent's *full*
        permitted set on the platform. EP-120-US-04 introduces the V2
        machine-authority profile (:class:`mudraid.MachineAgent` /
        :class:`mudraid.MachineIdentity`), where a ``private_key_jwt`` assertion
        carries explicit audience + scopes and an omitted scope set means the
        *empty* (minimal) set, never "everything."

        The legacy profile stays fully supported and reachable — additively, so
        existing integrations do not break — and can be selected explicitly via
        :meth:`Agent.legacy` to make the choice visible at call sites.

        **Retirement policy:** the legacy profile is retained through the V2
        transition and is scheduled for removal in a future major SDK release
        once V2 machine authority is generally available; it will be deprecated
        (with a runtime warning and a migration window) before any removal. New
        integrations should adopt :class:`mudraid.MachineAgent`.

    Construction resolves credentials with the following precedence:

      1. Explicit keyword arguments (``api_key_id=``, ``secret=``,
         ``base_url=``)
      2. The OS environment (``MUDRAID_API_KEY_ID``, ``MUDRAID_SECRET``,
         ``MUDRAID_BASE_URL``)
      3. A ``.env`` file in the project tree (auto-discovered)

    Raises:
        MudraIDConfigError: when ``api_key_id`` or ``secret`` cannot
            be resolved from any of the above. ``base_url`` always has a
            sensible production default and never raises on its own.

    The first outgoing request triggers a one-time bootstrap call to
    MudraID to learn which platforms this agent is registered with.
    Subsequent calls are cache-warm.
    """

    def __init__(
        self,
        api_key_id: str | None = None,
        secret: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self._config: SdkConfig = load_config(
            api_key_id=api_key_id,
            secret=secret,
            base_url=base_url,
        )
        # api_key_id is public; base_url is public. Logging both is
        # safe and useful for "which agent did this?" debugging.
        _logger.info(
            "Agent created: api_key_id=%s base_url=%s",
            self._config.api_key_id,
            self._config.base_url,
        )
        self._mudraid_http = MudraIDHttpClient(self._config)
        self._tokens = TokenManager(self._mudraid_http)
        self._platforms = PlatformResolver(self._mudraid_http)
        # A separate Session for outgoing platform calls. We do NOT
        # share the MudraID session because the two have different
        # security properties: MudraID requests carry the agent's
        # plaintext secret in the body; platform requests carry the
        # short-lived JWT in a header. Keeping the sessions distinct
        # makes it impossible to accidentally send one's headers on
        # the other's connection.
        self._platform_session = requests.Session()

    @classmethod
    def legacy(
        cls,
        api_key_id: str | None = None,
        secret: str | None = None,
        base_url: str | None = None,
    ) -> "Agent":
        """Explicitly construct the legacy api_key_id/secret auth profile.

        Behaviourally identical to calling ``Agent(...)`` directly — the default
        constructor *is* the legacy profile — but naming it at the call site
        documents the choice now that the V2 profile
        (:class:`mudraid.MachineAgent`) exists. Provided so integrations can pin
        themselves to the legacy behaviour intentionally rather than by default,
        and so a future deprecation can target this explicit entry point. See the
        class docstring for the retirement policy.
        """
        _logger.info("Agent.legacy() — constructing the legacy auth profile explicitly")
        return cls(api_key_id=api_key_id, secret=secret, base_url=base_url)

    # ---- public, safe-to-read accessors ---------------------------------

    @property
    def api_key_id(self) -> str:
        """The public agent identifier (``muid_kid_...``).

        Safe to log and display — this is the public half of the
        credential pair. The secret is intentionally not exposed via
        any property.
        """
        return self._config.api_key_id

    @property
    def base_url(self) -> str:
        """Resolved MudraID API base URL.

        Useful for diagnostics and dev tooling that need to confirm
        the SDK is pointed at the right backend.
        """
        return self._config.base_url

    # ---- maintenance ----------------------------------------------------

    def refresh_platforms(self) -> None:
        """Force a fresh bootstrap of the platform map.

        Call this after granting a new platform to the agent in the
        portal, or after removing one. The next outgoing request
        triggers a re-fetch of ``/auth/agents/me/platforms`` and
        rebuilds the host→platform_id map. Cached JWTs are also
        dropped so a now-revoked platform cannot serve a stale token.
        """
        _logger.info("Agent.refresh_platforms() — clearing resolver + token caches")
        self._platforms.refresh()
        self._tokens.clear()

    def close(self) -> None:
        """Release the underlying HTTP connection pools.

        Optional — both sessions garbage-collect cleanly. Provided for
        scripts that want deterministic shutdown.
        """
        self._platform_session.close()
        self._mudraid_http.close()

    # ---- HTTP surface ---------------------------------------------------

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        return self._request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> requests.Response:
        return self._request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> requests.Response:
        return self._request("DELETE", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> requests.Response:
        return self._request("PATCH", url, **kwargs)

    def head(self, url: str, **kwargs: Any) -> requests.Response:
        return self._request("HEAD", url, **kwargs)

    def options(self, url: str, **kwargs: Any) -> requests.Response:
        return self._request("OPTIONS", url, **kwargs)

    # ---- internals ------------------------------------------------------

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """The single point through which every HTTP method flows.

        Behaviour:

          - Resolves the URL host → platform_id. Failure here raises
            ``MudraIDPlatformNotRegisteredError`` BEFORE any outbound
            HTTP call.
          - Asks TokenManager for a JWT for the platform. Failure
            here raises ``MudraIDAuthError`` / ``MudraIDRevokedError``
            / ``MudraIDNetworkError`` BEFORE the platform is contacted.
          - Sends the request with ``Authorization: Bearer <jwt>``.
          - **M4.6 retry:** if the upstream platform returns ``401``,
            we treat it as token expiry / mid-flight rotation, refresh
            the JWT via TokenManager.refresh(), and replay the request
            EXACTLY ONCE. The retry uses the freshly-minted token, the
            caller's original headers, and the same body. A second
            401 is surfaced to the caller as the response — we never
            loop. Any other status code (200, 4xx, 5xx) is returned
            unmodified after the first attempt.

        Idempotency note: replaying a POST/PUT/PATCH on 401 is the
        same convention used by every major auth-aware HTTP SDK
        (AWS, GCP, Stripe, etc.). The standard rationale: if the
        platform's middleware rejected the JWT, it rejected the
        request *before* processing — a retry with a valid token is
        the first time the platform actually sees the call. A platform
        that returns 401 *after* mutating state is misimplemented;
        the SDK can't compensate for that.
        """
        platform_id = self._platforms.resolve(url)

        # Pop the caller's headers exactly once so the retry sees a
        # clean copy each time. Without this, ``kwargs.pop`` in a
        # naive retry would silently drop the caller's headers on
        # the second attempt.
        caller_headers = dict(kwargs.pop("headers", None) or {})

        response = self._send(platform_id, method, url, caller_headers, kwargs)
        if response.status_code != 401:
            return response

        # Token rejected by the platform. Force-mint a new one and
        # replay the request exactly once. A failed refresh propagates
        # (the developer needs to know auth is broken); a second 401
        # is returned as-is so the caller can decide what to do —
        # don't loop, ever.
        _logger.warning(
            "platform returned 401 for %s %s; refreshing token and retrying once",
            method,
            url,
        )
        self._tokens.refresh(platform_id)
        return self._send(platform_id, method, url, caller_headers, kwargs)

    def _send(
        self,
        platform_id: str,
        method: str,
        url: str,
        caller_headers: dict[str, str],
        kwargs: dict[str, Any],
    ) -> requests.Response:
        """Attach a current JWT and dispatch one HTTP request.

        Header merge policy: caller-supplied entries come first, then
        the SDK's ``Authorization`` last so it always wins. A
        developer who passes their own ``Authorization`` header is
        almost certainly trying to use a different auth mechanism —
        silently overriding here is correct because attaching the
        MudraID bearer token is what the SDK is for.
        """
        token = self._tokens.get_token(platform_id)
        headers = {**caller_headers, "Authorization": f"Bearer {token}"}
        return self._platform_session.request(
            method=method,
            url=url,
            headers=headers,
            **kwargs,
        )
