import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Coroutine, List
from loguru import logger
import time


@dataclass
class Event:
    """Standard Event class for inter-module communication in ASTA."""
    type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class EventBus:
    """Asynchronous Event Bus acting as the Central Nervous System of ASTA."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[Event], Coroutine[Any, Any, None]]]] = {}
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._task: asyncio.Task[None] | None = None
        self._running: bool = False

    def subscribe(self, event_type: str, handler: Callable[[Event], Coroutine[Any, Any, None]]) -> None:
        """Subscribe an async handler to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed handler {handler.__name__} to event '{event_type}'")

    async def publish(self, event: Event) -> None:
        """Publish an event to the bus."""
        await self._queue.put(event)
        logger.debug(f"Published event '{event.type}' with payload {event.payload}")

    async def _process_events(self) -> None:
        """Background task to process events from the queue."""
        while self._running:
            event = await self._queue.get()
            handlers = self._subscribers.get(event.type, [])

            if handlers:
                # Run all handlers concurrently for this event
                tasks = [asyncio.create_task(handler(event)) for handler in handlers]
                await asyncio.gather(*tasks, return_exceptions=True)
            else:
                logger.warning(f"No subscribers for event type '{event.type}'")

            self._queue.task_done()

    def start(self) -> None:
        """Start the background event processing loop."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._process_events())
            logger.info("Event Bus started")

    async def stop(self) -> None:
        """Stop the event bus and wait for pending events to be processed."""
        if self._running:
            # Wait until the queue is fully processed before shutting down the loop
            await self._queue.join()
            self._running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            logger.info("Event Bus stopped")
