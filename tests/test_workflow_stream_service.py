import json
from queue import Empty

import pytest

from services import workflow_stream_service


class DummyRequest:
    def __init__(self, states=None):
        self.states = list(states or [False])

    async def is_disconnected(self):
        if self.states:
            return self.states.pop(0)
        return True


def _decode_event(message):
    raw = message.encode().decode()
    lines = [line for line in raw.splitlines() if line]
    body = {}
    for line in lines:
        if line.startswith("event: "):
            body["event"] = line.removeprefix("event: ")
        if line.startswith("data: "):
            body["data"] = json.loads(line.removeprefix("data: "))
    return body


@pytest.mark.anyio
async def test_stream_emits_snapshot_frame(monkeypatch):
    monkeypatch.setattr(workflow_stream_service, "subscribe", lambda **kwargs: ("sub-1", object()))
    monkeypatch.setattr(workflow_stream_service, "unsubscribe", lambda _subscriber_id: None)
    monkeypatch.setattr(
        workflow_stream_service,
        "build_snapshot_event",
        lambda: {"type": "workflow.event", "event_type": "workflow.snapshot", "payload": {"profiles": []}},
    )

    stream = workflow_stream_service.stream_workflow_events(DummyRequest([False, True]))
    message = await anext(stream)
    await stream.aclose()

    decoded = _decode_event(message)
    assert decoded["event"] == "workflow.snapshot"
    assert decoded["data"]["type"] == "workflow.event"


@pytest.mark.anyio
async def test_stream_emits_heartbeat_frame(monkeypatch):
    class EmptyQueue:
        def get(self, *_args, **_kwargs):
            raise Empty

    monkeypatch.setattr(workflow_stream_service, "subscribe", lambda **kwargs: ("sub-2", EmptyQueue()))
    monkeypatch.setattr(workflow_stream_service, "unsubscribe", lambda _subscriber_id: None)
    monkeypatch.setattr(
        workflow_stream_service,
        "build_snapshot_event",
        lambda: {"type": "workflow.event", "event_type": "workflow.snapshot", "payload": {"profiles": []}},
    )

    stream = workflow_stream_service.stream_workflow_events(DummyRequest([False, True]))
    await anext(stream)
    message = await anext(stream)
    await stream.aclose()

    decoded = _decode_event(message)
    assert decoded["event"] == "heartbeat"
    assert decoded["data"]["type"] == "heartbeat"


@pytest.mark.anyio
async def test_stream_unsubscribes_on_close(monkeypatch):
    unsubscribed = []

    monkeypatch.setattr(workflow_stream_service, "subscribe", lambda **kwargs: ("sub-3", object()))
    monkeypatch.setattr(workflow_stream_service, "unsubscribe", lambda subscriber_id: unsubscribed.append(subscriber_id))
    monkeypatch.setattr(
        workflow_stream_service,
        "build_snapshot_event",
        lambda: {"type": "workflow.event", "event_type": "workflow.snapshot", "payload": {"profiles": []}},
    )

    stream = workflow_stream_service.stream_workflow_events(DummyRequest([False, True]))
    await anext(stream)
    await stream.aclose()

    assert unsubscribed == ["sub-3"]


@pytest.mark.anyio
async def test_stream_stops_after_disconnect(monkeypatch):
    class QueueWithEvent:
        def __init__(self):
            self.used = False

        def get(self, *_args, **_kwargs):
            if self.used:
                raise Empty
            self.used = True
            return {"type": "workflow.event", "event_type": "analysis.completed", "payload": {"profiles": []}}

    monkeypatch.setattr(workflow_stream_service, "subscribe", lambda **kwargs: ("sub-4", QueueWithEvent()))
    monkeypatch.setattr(workflow_stream_service, "unsubscribe", lambda _subscriber_id: None)
    monkeypatch.setattr(
        workflow_stream_service,
        "build_snapshot_event",
        lambda: {"type": "workflow.event", "event_type": "workflow.snapshot", "payload": {"profiles": []}},
    )

    stream = workflow_stream_service.stream_workflow_events(DummyRequest([False, True]))
    await anext(stream)
    event_message = await anext(stream)
    decoded = _decode_event(event_message)
    assert decoded["event"] == "analysis.completed"

    with pytest.raises(StopAsyncIteration):
        await anext(stream)