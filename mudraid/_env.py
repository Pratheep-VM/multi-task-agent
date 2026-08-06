"""Environment + .env credential loading.

Reads:

  - ``MUDRAID_API_KEY_ID``  (required)
  - ``MUDRAID_SECRET``      (required)
  - ``MUDRAID_BASE_URL``    (optional; falls back to the production default)

Convention: integrators store these in a ``.env`` file in their project
root. python-dotenv loads that file into ``os.environ`` on first access;
explicit arguments to :class:`mudraid.Agent` always win.

The dotenv load uses ``override=False`` so values set by CI, container
orchestrators, or the developer's shell take precedence over whatever
``.env`` says — that matches established Python conventions and prevents
a stale local ``.env`` from leaking into production.
"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv

from mudraid.exceptions import MudraIDConfigError

_logger = logging.getLogger("mudraid.env")

DEFAULT_BASE_URL = "https://api.staging.mudraid.ai"

_ENV_API_KEY_ID = "MUDRAID_API_KEY_ID"
_ENV_SECRET = "MUDRAID_SECRET"  # nosec B105 - env-var NAME, not the secret value
_ENV_BASE_URL = "MUDRAID_BASE_URL"

# Lazy one-time dotenv load. Filesystem walks are cheap but not free; we
# pay the cost the first time any Agent() is constructed and never again.
# A lock guards the flag against torn writes in multi-threaded apps.
_dotenv_lock = threading.Lock()
_dotenv_loaded = False


def _ensure_dotenv_loaded() -> None:
    """Idempotent ``.env`` discovery + load.

    Safe to call from any entry point. Walks up from the current working
    directory looking for ``.env``; a missing file is not an error (env
    may be provided entirely from the OS, e.g. in a container).

    The search is rooted at ``os.getcwd()``, not at the SDK's installed
    file path. python-dotenv's ``find_dotenv()`` defaults to the latter,
    which would point at site-packages and never find an integrator's
    project ``.env``.
    """
    global _dotenv_loaded
    if _dotenv_loaded:
        return
    with _dotenv_lock:
        if _dotenv_loaded:
            return
        path = find_dotenv(usecwd=True)
        if path:
            # Log the path (safe — it's a file location) but never the
            # contents. python-dotenv handles the load silently; we
            # don't echo what got set.
            _logger.debug("loaded environment from %s", path)
            load_dotenv(dotenv_path=path, override=False)
        else:
            _logger.debug("no .env file found; relying on OS environment only")
        _dotenv_loaded = True


@dataclass(frozen=True)
class SdkConfig:
    """Resolved SDK configuration.

    Frozen so downstream modules treat it as a value object — nothing in
    the SDK should ever mutate credentials after Agent construction.
    """

    api_key_id: str
    secret: str
    base_url: str


def load_config(
    api_key_id: str | None = None,
    secret: str | None = None,
    base_url: str | None = None,
) -> SdkConfig:
    """Resolve SDK configuration with kwarg > env precedence.

    Precedence (highest first):
      1. Explicit keyword arguments
      2. ``os.environ`` (already populated by the OS / container)
      3. Values from a ``.env`` file in the project tree

    Raises:
        MudraIDConfigError: when ``api_key_id`` or ``secret`` cannot be
            resolved after consulting both kwargs and the environment.
            The error message lists the missing variables so the
            developer doesn't have to guess.
    """
    _ensure_dotenv_loaded()

    # ``Optional[str] or str`` evaluates to str at runtime but mypy
    # widens it back to Optional[str]; the ``or ""`` tail pins the
    # type so ``.strip()`` is callable. The behaviour is unchanged.
    resolved_id: str = (api_key_id or os.environ.get(_ENV_API_KEY_ID) or "").strip()
    resolved_secret: str = (secret or os.environ.get(_ENV_SECRET) or "").strip()
    resolved_url = base_url or os.environ.get(_ENV_BASE_URL, "").strip() or DEFAULT_BASE_URL

    missing: list[str] = []
    if not resolved_id:
        missing.append(_ENV_API_KEY_ID)
    if not resolved_secret:
        missing.append(_ENV_SECRET)
    if missing:
        raise MudraIDConfigError(
            "Missing MudraID credentials: "
            + ", ".join(missing)
            + ". Set them in your .env file or pass api_key_id= / secret= to Agent()."
        )

    config = SdkConfig(
        api_key_id=resolved_id,
        secret=resolved_secret,
        base_url=resolved_url.rstrip("/"),
    )
    # api_key_id is the *public* half of the credential pair — safe to
    # log. The secret is referenced only by presence, never by value.
    _logger.info(
        "SDK credentials resolved: api_key_id=%s base_url=%s",
        config.api_key_id,
        config.base_url,
    )
    return config
