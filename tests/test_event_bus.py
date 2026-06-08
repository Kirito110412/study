import asyncio
import pytest
from asta.core_engine.event_bus import EventBus, Event


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe() -> None:
    bus = EventBus()
    bus.start()

    received_events = []

    # Dummy Memory Domain handler
    async def memory_handler(event: Event) -> None:
        received_events.append(event)

    # Dummy Vision Domain handler
    async def vision_handler(event: Event) -> None:
        received_events.append(event)

    bus.subscribe("SCREEN_CAPTURED", vision_handler)
    bus.subscribe("CONTEXT_EVICTED", memory_handler)

    # Publish events from different domains
    await bus.publish(Event(type="SCREEN_CAPTURED", payload={"coords": [10, 20]}))
    await bus.publish(Event(type="CONTEXT_EVICTED", payload={"tokens": 1000}))

    # Wait for the queue to process
    await asyncio.sleep(0.1)

    assert len(received_events) == 2
    assert received_events[0].type == "SCREEN_CAPTURED"
    assert received_events[0].payload["coords"] == [10, 20]

    assert received_events[1].type == "CONTEXT_EVICTED"
    assert received_events[1].payload["tokens"] == 1000

    await bus.stop()


@pytest.mark.asyncio
async def test_multiple_subscribers() -> None:
    bus = EventBus()
    bus.start()

    handler_1_called = False
    handler_2_called = False

    async def handler_1(event: Event) -> None:
        nonlocal handler_1_called
        handler_1_called = True

    async def handler_2(event: Event) -> None:
        nonlocal handler_2_called
        handler_2_called = True

    bus.subscribe("SYSTEM_BOOT", handler_1)
    bus.subscribe("SYSTEM_BOOT", handler_2)

    await bus.publish(Event(type="SYSTEM_BOOT"))

    await asyncio.sleep(0.1)

    assert handler_1_called is True
    assert handler_2_called is True

    await bus.stop()
