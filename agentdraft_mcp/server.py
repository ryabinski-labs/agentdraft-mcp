"""The MCP server proper.

Tools mirror the AgentDraft REST surface 1:1 and reuse the official
Python SDK so the wire-level behavior, auth, errors, and retries match
everything else built on AgentDraft. A losing booking attempt surfaces
as a typed ``Conflict`` exception inside the SDK; we re-shape that into
a structured MCP error result so calling agents can branch on it
without parsing strings.

Authentication is via the standard ``AGENTDRAFT_API_KEY`` environment
variable (an ``avs_live_…`` agent key issued from the AgentDraft
dashboard). Optionally point at a non-prod backend with
``AGENTDRAFT_BASE_URL``.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from agentdraft import Client, Conflict
from agentdraft import __version__ as _agentdraft_version
from agentdraft.errors import AgentDraftError, AuthError, RateLimited, RuleViolation

from . import __version__ as _mcp_version

# Composite User-Agent so the backend sees both the wrapper version and
# the underlying Python SDK version this MCP server is built on.
_USER_AGENT = (
    f"agentdraft-mcp/{_mcp_version} "
    f"agentdraft-python/{_agentdraft_version}"
)


def _client() -> Client:
    """Build a fresh Client for each tool invocation.

    MCP tools may be called from independent agent sessions, and Client
    holds an httpx connection that we want released between calls. The
    SDK is cheap to instantiate — it does not block on the network at
    construction.
    """
    api_key = os.environ.get("AGENTDRAFT_API_KEY")
    if not api_key:
        raise RuntimeError(
            "AGENTDRAFT_API_KEY is not set. Issue an agent key from the "
            "AgentDraft dashboard and export it before starting the MCP "
            "server."
        )
    base_url = os.environ.get("AGENTDRAFT_BASE_URL")
    return Client(api_key=api_key, base_url=base_url, user_agent=_USER_AGENT)


def _parse_dt(s: str) -> datetime:
    """Accept any ISO 8601 string MCP clients are likely to pass.

    Python's ``fromisoformat`` is strict pre-3.11 about the ``Z`` suffix;
    normalize it manually so 3.10 clients work too.
    """
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _conflict_payload(e: Conflict) -> dict[str, Any]:
    return {
        "error": "outranked",
        "winning_booking_id": e.winning_booking_id,
        "winning_agent_id": e.winning_agent_id,
        "winning_agent_priority": e.winning_agent_priority,
        "your_priority": getattr(e, "your_priority", None),
        "message": (
            "Your booking was outranked. Read the winner's identity from "
            "winning_agent_id and propose an alternate slot to your user."
        ),
    }


def _error_payload(e: Exception) -> dict[str, Any]:
    kind = type(e).__name__
    body = getattr(e, "body", None) or {}
    return {
        "error": kind,
        "message": str(e),
        "detail": body,
    }


def build_server() -> FastMCP:
    """Return a configured FastMCP instance, ready to ``run()``."""

    mcp = FastMCP(
        "agentdraft",
        instructions=(
            "AgentDraft is the coordination layer for AI scheduling "
            "agents. Call get_availability before proposing a slot, "
            "create_hold to reserve it tentatively, commit_booking to "
            "make it final. A losing booking returns a structured "
            "outranked payload — read winning_agent_id and propose an "
            "alternate slot rather than retrying."
        ),
    )

    @mcp.tool()
    def whoami() -> dict[str, Any]:
        """Confirm the configured AGENTDRAFT_API_KEY is valid and return
        the calling agent's identity, priority, scopes, and the owner's
        timezone (so a client can render slots in the owner's zone)."""
        with _client() as c:
            me = c.agents.me()
            return {
                "agent_id": me.agent_id,
                "user_id": getattr(me, "user_id", None),
                "priority": me.priority,
                "scopes": list(me.scopes),
                "timezone": getattr(me, "timezone", "UTC"),
            }

    @mcp.tool()
    def get_availability(
        start: str,
        end: str,
        duration_minutes: int = 30,
        granularity_minutes: int = 15,
        include_holds: bool = True,
    ) -> dict[str, Any]:
        """List slots open to the calling agent within [start, end).

        Times are ISO 8601 strings (`2026-06-01T14:00:00Z`). The result
        is filtered through the user's focus blocks, buffer rules, and
        any currently-active holds across sibling agents.
        """
        with _client() as c:
            slots = c.availability.list(
                start=_parse_dt(start),
                end=_parse_dt(end),
                duration_minutes=duration_minutes,
                granularity_minutes=granularity_minutes,
                include_holds=include_holds,
            )
            return {
                "slots": [
                    {
                        "start": s.start.isoformat(),
                        "end": s.end.isoformat(),
                    }
                    for s in slots
                ]
            }

    @mcp.tool()
    def create_hold(
        start: str,
        end: str,
        idempotency_key: Optional[str] = None,
        metadata: Optional[dict] = None,
        title: Optional[str] = None,
        invitee: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Reserve a slot tentatively. Holds expire automatically (30s
        TTL by default). A subsequent commit_booking on the same slot
        promotes the hold to a final booking.

        Optional ``title`` and ``invitee`` (``{name, email, notes}``) record
        who the slot is for; both carry through to the eventual commit.

        Returns an outranked payload if a higher-priority agent already
        holds or has committed the slot inside the bump window.
        """
        try:
            with _client() as c:
                b = c.bookings.hold(
                    start=_parse_dt(start),
                    end=_parse_dt(end),
                    idempotency_key=idempotency_key,
                    metadata=metadata,
                    title=title,
                    invitee=invitee,
                )
                return {
                    "booking_id": b.booking_id,
                    "status": b.status,
                    "start": b.start.isoformat() if hasattr(b, "start") else start,
                    "end": b.end.isoformat() if hasattr(b, "end") else end,
                }
        except Conflict as e:
            return _conflict_payload(e)
        except (AuthError, RateLimited, RuleViolation, AgentDraftError) as e:
            return _error_payload(e)

    @mcp.tool()
    def release_hold(hold_id: str) -> dict[str, Any]:
        """Release a previously-created hold so other agents can claim
        the slot before the TTL expires."""
        try:
            with _client() as c:
                c.bookings.release(hold_id)
                return {"released": True, "hold_id": hold_id}
        except (AuthError, RateLimited, AgentDraftError) as e:
            return _error_payload(e)

    @mcp.tool()
    def commit_booking(
        start: str,
        end: str,
        idempotency_key: Optional[str] = None,
        metadata: Optional[dict] = None,
        with_conferencing: bool = False,
        title: Optional[str] = None,
        invitee: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Finalize a booking. This is the atomic compare-and-swap at
        the slot level — exactly one agent succeeds per slot in any
        race window. Returns an outranked payload on 409.

        Optional ``title`` and ``invitee`` (``{name, email, notes}``) record
        who the slot is for; both are echoed back and shown to the owner in
        the dashboard.

        Set ``with_conferencing=True`` to attach a video meeting link to
        the committed booking; the link is returned under ``conferencing``."""
        try:
            with _client() as c:
                b = c.bookings.commit(
                    start=_parse_dt(start),
                    end=_parse_dt(end),
                    idempotency_key=idempotency_key,
                    metadata=metadata,
                    with_conferencing=with_conferencing,
                    title=title,
                    invitee=invitee,
                )
                out = {
                    "booking_id": b.booking_id,
                    "status": b.status,
                    "start": b.start.isoformat() if hasattr(b, "start") else start,
                    "end": b.end.isoformat() if hasattr(b, "end") else end,
                }
                if getattr(b, "title", None):
                    out["title"] = b.title
                if getattr(b, "invitee", None):
                    out["invitee"] = b.invitee
                if getattr(b, "conferencing_url", None):
                    out["conferencing"] = {
                        "provider": b.conferencing_provider,
                        "url": b.conferencing_url,
                    }
                return out
        except Conflict as e:
            return _conflict_payload(e)
        except (AuthError, RateLimited, RuleViolation, AgentDraftError) as e:
            return _error_payload(e)

    @mcp.tool()
    def cancel_booking(booking_id: str) -> dict[str, Any]:
        """Cancel a previously-committed booking owned by the calling
        agent. The slot becomes available to other agents immediately."""
        try:
            with _client() as c:
                c.bookings.cancel(booking_id)
                return {"cancelled": True, "booking_id": booking_id}
        except (AuthError, RateLimited, AgentDraftError) as e:
            return _error_payload(e)

    return mcp
