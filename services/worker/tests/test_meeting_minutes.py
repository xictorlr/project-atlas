"""Tests for atlas_worker.compiler.meeting_minutes.

Coverage:
  - generate_meeting_minutes: valid JSON → correct MeetingMinutes fields
  - generate_meeting_minutes: decisions parsed correctly (description, made_by, context)
  - generate_meeting_minutes: action items parsed correctly (all fields)
  - generate_meeting_minutes: malformed JSON → MeetingMinutes with empty collections
  - generate_meeting_minutes: empty transcript raises ValueError (no LLM call)
  - generate_meeting_minutes: model name preserved from GenerateResult
  - generate_meeting_minutes: known_entities passed into prompt
  - Decision and ActionItem are frozen dataclasses
  - _parse_action_item: invalid priority falls back to "medium"
  - _parse_action_item: invalid status falls back to "open"
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from atlas_worker.compiler.meeting_minutes import (
    ActionItem,
    Decision,
    MeetingMinutes,
    _parse_action_item,
    _parse_minutes_json,
    generate_meeting_minutes,
)
from atlas_worker.inference.models import GenerateResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_router(response_payload: dict | str, model: str = "test-model") -> MagicMock:
    if isinstance(response_payload, dict):
        text = json.dumps(response_payload)
    else:
        text = response_payload
    result = GenerateResult(
        text=text,
        model=model,
        backend="ollama",
        tokens_used=80,
        duration_ms=200,
    )
    router = MagicMock()
    router.generate = AsyncMock(return_value=result)
    return router


_VALID_MINUTES_PAYLOAD = {
    "title": "Product Sync Apr 6",
    "date": "2026-04-06",
    "attendees": ["Alice", "Bob", "Carol"],
    "agenda_items": ["API migration", "Q2 roadmap"],
    "decisions": [
        {
            "description": "Adopt REST v2 for the public API.",
            "made_by": "Alice",
            "context": "Previous REST v1 is deprecated.",
        }
    ],
    "action_items": [
        {
            "description": "Write migration guide for REST v2.",
            "owner": "Bob",
            "deadline": "2026-04-20",
            "priority": "high",
            "status": "open",
            "source_quote": "Bob will write the migration guide by April 20.",
        }
    ],
    "next_steps": "Review migration guide at next meeting.",
}


# ---------------------------------------------------------------------------
# Tests — generate_meeting_minutes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_returns_meeting_minutes_instance() -> None:
    router = _make_router(_VALID_MINUTES_PAYLOAD)
    result = await generate_meeting_minutes("Alice: Let's meet.", [], router)
    assert isinstance(result, MeetingMinutes)


@pytest.mark.asyncio
async def test_generate_title_parsed() -> None:
    router = _make_router(_VALID_MINUTES_PAYLOAD)
    result = await generate_meeting_minutes("Transcript here.", [], router)
    assert result.title == "Product Sync Apr 6"


@pytest.mark.asyncio
async def test_generate_date_parsed() -> None:
    router = _make_router(_VALID_MINUTES_PAYLOAD)
    result = await generate_meeting_minutes("Transcript here.", [], router)
    assert result.date == "2026-04-06"


@pytest.mark.asyncio
async def test_generate_attendees_parsed() -> None:
    router = _make_router(_VALID_MINUTES_PAYLOAD)
    result = await generate_meeting_minutes("Transcript here.", [], router)
    assert result.attendees == ["Alice", "Bob", "Carol"]


@pytest.mark.asyncio
async def test_generate_decisions_parsed() -> None:
    router = _make_router(_VALID_MINUTES_PAYLOAD)
    result = await generate_meeting_minutes("Transcript here.", [], router)
    assert len(result.decisions) == 1
    d = result.decisions[0]
    assert d.description == "Adopt REST v2 for the public API."
    assert d.made_by == "Alice"
    assert "deprecated" in d.context


@pytest.mark.asyncio
async def test_generate_action_items_parsed() -> None:
    router = _make_router(_VALID_MINUTES_PAYLOAD)
    result = await generate_meeting_minutes("Transcript here.", [], router)
    assert len(result.action_items) == 1
    a = result.action_items[0]
    assert a.description == "Write migration guide for REST v2."
    assert a.owner == "Bob"
    assert a.deadline == "2026-04-20"
    assert a.priority == "high"
    assert a.status == "open"
    assert "April 20" in a.source_quote


@pytest.mark.asyncio
async def test_generate_model_name_preserved() -> None:
    router = _make_router(_VALID_MINUTES_PAYLOAD, model="gemma4:27b")
    result = await generate_meeting_minutes("Transcript here.", [], router)
    assert result.model == "gemma4:27b"


@pytest.mark.asyncio
async def test_generate_known_entities_in_prompt() -> None:
    router = _make_router(_VALID_MINUTES_PAYLOAD)
    await generate_meeting_minutes("Transcript.", ["Alice Smith", "Bob Jones"], router)
    call_args = router.generate.call_args
    prompt = call_args.args[0]
    assert "Alice Smith" in prompt
    assert "Bob Jones" in prompt


@pytest.mark.asyncio
async def test_generate_malformed_json_returns_empty_minutes() -> None:
    router = _make_router("NOT JSON {{{{ broken")
    result = await generate_meeting_minutes("Transcript.", [], router)
    assert isinstance(result, MeetingMinutes)
    assert result.decisions == []
    assert result.action_items == []
    assert result.attendees == []


@pytest.mark.asyncio
async def test_generate_empty_transcript_raises_value_error() -> None:
    router = _make_router(_VALID_MINUTES_PAYLOAD)
    with pytest.raises(ValueError, match="transcript must not be empty"):
        await generate_meeting_minutes("", [], router)
    router.generate.assert_not_called()


# ---------------------------------------------------------------------------
# Tests — _parse_minutes_json (unit)
# ---------------------------------------------------------------------------


def test_parse_minutes_json_invalid_priority_fallback() -> None:
    payload = {
        "title": "Test",
        "date": "",
        "attendees": [],
        "agenda_items": [],
        "decisions": [],
        "action_items": [
            {
                "description": "Do something.",
                "priority": "URGENT",  # invalid → should fall back to medium
                "status": "open",
                "source_quote": "quote",
            }
        ],
        "next_steps": "",
    }
    result = _parse_minutes_json(json.dumps(payload), model="test")
    assert result.action_items[0].priority == "medium"


def test_parse_minutes_json_invalid_status_fallback() -> None:
    payload = {
        "title": "Test",
        "date": "",
        "attendees": [],
        "agenda_items": [],
        "decisions": [],
        "action_items": [
            {
                "description": "Do something.",
                "priority": "low",
                "status": "BLOCKED",  # invalid → should fall back to open
                "source_quote": "quote",
            }
        ],
        "next_steps": "",
    }
    result = _parse_minutes_json(json.dumps(payload), model="test")
    assert result.action_items[0].status == "open"


def test_parse_minutes_json_missing_decision_description() -> None:
    payload = {
        "title": "Test",
        "date": "",
        "attendees": [],
        "agenda_items": [],
        "decisions": [{"made_by": "Alice"}],  # missing description
        "action_items": [],
        "next_steps": "",
    }
    # Should not crash — description defaults to empty string.
    result = _parse_minutes_json(json.dumps(payload), model="test")
    assert len(result.decisions) == 1
    assert result.decisions[0].description == ""


# ---------------------------------------------------------------------------
# Tests — frozen dataclasses
# ---------------------------------------------------------------------------


def test_decision_is_frozen() -> None:
    d = Decision(description="Test decision.")
    with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
        d.description = "changed"  # type: ignore[misc]


def test_action_item_is_frozen() -> None:
    a = ActionItem(description="Test action.")
    with pytest.raises(Exception):
        a.description = "changed"  # type: ignore[misc]
