"""Meldet, wenn ein Memo durch die Uhr fällig wird (Prüfdatum, Topic-Termin): die Oberfläche muss nicht fragen."""

from __future__ import annotations

from viewer.core.application.ports import Clock, Database, EventBus, Scheduler
from viewer.core.domain.events import Event
from viewer.plugins.memos.application.ports import MemoRepository, TopicRepository
from viewer.plugins.memos.domain.due import next_clock_due

DUE_TOPIC = "memos.due"
SCHEDULER_OWNER = "memos"


class DueWatch:
    """Genau ein Termin über den `Scheduler`: der nächste Zeitpunkt, zu dem ein Memo durch die Uhr fällig wird. Ist er
    erreicht, meldet der Dienst `memos.due`; danach setzt er den nächsten. Jedes andere Ereignis kann Prüfdaten oder
    Termine geändert haben und setzt den Termin neu. Fällig durch Auslöser oder Hinweise melden die Memos schon selbst
    (`memos.memo.changed`)."""

    def __init__(
        self,
        memos: MemoRepository,
        topics: TopicRepository,
        database: Database,
        clock: Clock,
        events: EventBus,
        scheduler: Scheduler,
    ) -> None:
        self._memos = memos
        self._topics = topics
        self._database = database
        self._clock = clock
        self._events = events
        self._scheduler = scheduler

    def start(self) -> None:
        self.reschedule()

    def reschedule(self) -> None:
        with self._database.transaction() as tx:
            at = next_clock_due(self._memos.list_in(tx, None), self._topics.list_in(tx, None), self._clock.now())
        self._scheduler.schedule(SCHEDULER_OWNER, at, self.fire)

    def fire(self) -> None:
        self._events.publish(Event(DUE_TOPIC, {}, public=True))
        self.reschedule()

    def on_event(self, event: Event) -> None:
        if event.topic != DUE_TOPIC:
            self.reschedule()
