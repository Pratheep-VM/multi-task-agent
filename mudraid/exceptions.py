"""SDK error hierarchy.

This file declares only the base `MudraIDError`. Specific subclasses
(`MudraIDAuthError`, `MudraIDRevokedError`, `MudraIDNetworkError`,
`MudraIDPlatformNotRegisteredError`, `MudraIDConfigError`) are added
in task M4.7 once the modules that raise them exist.

All SDK-raised exceptions must inherit from `MudraIDError` so callers
can write a single `except MudraIDError:` block that catches anything
the SDK throws on its own behalf.
"""

from __future__ import annotations


class MudraIDError(Exception):
    """Base class for every error raised by the MudraID SDK.

    Catching this base exception will catch every SDK-originated
    failure — credential, network, authorisation, configuration —
    without also catching the underlying `requests` errors that the
    SDK transparently surfaces from upstream platform calls.
    """


class MudraIDConfigError(MudraIDError):
    """Configuration error — missing or invalid SDK initialisation state.

    Raised at :class:`mudraid.Agent` construction when
    ``MUDRAID_API_KEY_ID`` or ``MUDRAID_SECRET`` cannot be resolved
    from explicit arguments, the OS environment, or a ``.env`` file.
    The message lists the missing variables so recovery is one step
    away.
    """


class MudraIDAuthError(MudraIDError):
    """MudraID rejected the SDK's credentials.

    Raised when the control-plane returns HTTP 401 — typically caused
    by a wrong ``MUDRAID_API_KEY_ID`` or ``MUDRAID_SECRET``. The error
    shape is intentionally generic; MudraID itself does not reveal
    whether the api_key_id is unknown or the secret is wrong, to
    resist enumeration.
    """


class MudraIDRevokedError(MudraIDError):
    """MudraID accepted the credentials but refused the operation.

    Raised on HTTP 403 from the control-plane. Covers agent
    revocation, missing platform permission, missing/invalid scopes,
    and similar authorisation denials. The exception message echoes
    the server's ``detail`` field so the caller can distinguish — but
    callers should not parse the message; catch the exception and
    surface it to the developer.

    Future versions may split this into more specific subclasses;
    callers that catch ``MudraIDRevokedError`` today will still catch
    those subclasses tomorrow.
    """


class MudraIDNetworkError(MudraIDError):
    """SDK could not reach or could not parse a response from MudraID.

    Raised on connection errors, timeouts, unexpected non-2xx
    statuses, and malformed JSON responses. The original exception
    (if any) is chained via ``__cause__`` so detailed diagnostics
    survive without leaking into the user-facing message.
    """


class MudraIDScopeError(MudraIDError):
    """The caller asked the SDK to request authority it must never request.

    Raised **client-side, before any network call**, by the V2 machine-authority
    path when a requested scope set would broaden authority rather than name a
    specific, bounded capability — most importantly a wildcard / "all" scope.

    This is the structural half of the story's first safety invariant: an
    *omitted* scope set is the empty (minimal) set and travels as no ``scope`` at
    all, while an *explicit* wildcard is refused here rather than being forwarded.
    There is deliberately no SDK API that turns "no scopes" into "every scope";
    the only way to obtain authority is to name each scope, and naming a wildcard
    is an error, not a shortcut.
    """


class MudraIDExecutionUnknownError(MudraIDError):
    """A consequential call was sent but its outcome is unknown — do NOT replay.

    Raised by the V2 consequence-safe request path when a request that may have
    side effects (a non-idempotent method, e.g. ``POST``/``PATCH``, carrying no
    server-dedupable idempotency key) fails *after* the bytes were put on the
    wire but *before* a response was read — a read timeout, a dropped
    connection mid-flight, a truncated response. In that window the server may
    have fully processed the action, so a blind retry could duplicate it.

    This is the second safety invariant made concrete: rather than silently
    replaying and risking a double-charge / double-send, the SDK surfaces this
    typed result and hands the decision back to the caller. The caller can then
    either check server-side state and reconcile, or re-issue the call with an
    idempotency key the server deduplicates (see
    :class:`mudraid.MachineAgent`). The triggering transport error is chained via
    ``__cause__`` for diagnostics; the message never echoes the request body.
    """


class MudraIDPlatformNotRegisteredError(MudraIDError):
    """The URL host does not map to any platform this agent is registered with.

    Raised by the agent SDK when the developer calls
    ``agent.get("https://example.com/...")`` but ``example.com`` is
    not in the agent's bootstrap response — either because the agent
    has not been granted access to that platform, the platform's
    verification has lapsed, or platform-integration-service was
    unavailable when the bootstrap built its host→platform_id map
    and the hostname enrichment came back ``null``.

    Recovery: grant the platform in the MudraID portal, then call
    :py:meth:`mudraid.Agent.refresh_platforms` (or recreate the
    Agent) to re-fetch the map.
    """
