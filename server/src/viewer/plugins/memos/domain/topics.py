"""Der Topic-Baum: Tiefe, Verschieben, und was beim Löschen, Archivieren und Reaktivieren eines Topics geschieht.

Die Pläne sagen, welche Topics und Memos betroffen sind und wohin Memos umgehängt werden; der Dienst führt sie in
einer Transaktion aus. Gelöschte Topics und Memos zählen nirgends mit.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal

from viewer.plugins.memos.domain.model import FINISHED_STATUSES, Memo, MemosViolation, Topic

#: Ziel einer umgehängten Memo: das neutrale Topic „Archiviert“ des Projekts (der Dienst legt es bei Bedarf an).
ARCHIVE_TARGET = "@archive"

ActiveChoice = Literal["delete", "move", "archive"]


def _live(topics: Sequence[Topic]) -> dict[str, Topic]:
    return {t.uid: t for t in topics if t.deleted_at is None}


def depth(topics: Mapping[str, Topic], uid: str) -> int:
    """Ebenen von der Wurzel bis `uid` (ein Topic ohne Parent hat Tiefe 1)."""
    level, seen = 0, set()
    current: str | None = uid
    while current is not None and current in topics:
        if current in seen:
            raise MemosViolation("topic_loop", "Die Topics bilden einen Kreis", topic=topics[current].label)
        seen.add(current)
        level += 1
        current = topics[current].parent_uid
    return level


def subtree(topics: Sequence[Topic], uid: str) -> list[Topic]:
    """Das Topic und alle seine Nachkommen (nicht gelöschte), das Topic zuerst, sonst nach Label."""
    live = _live(topics)
    if uid not in live:
        return []
    found = [live[uid]]
    queue = [uid]
    while queue:
        current = queue.pop(0)
        for topic in sorted(live.values(), key=lambda t: t.label):
            if topic.parent_uid == current:
                found.append(topic)
                queue.append(topic.uid)
    return found


def height(topics: Sequence[Topic], uid: str) -> int:
    """Ebenen des Teilbaums ab `uid` (ein Topic ohne Unter-Topics hat Höhe 1)."""
    live = _live(topics)
    levels = {uid: 1}
    for topic in subtree(topics, uid)[1:]:
        levels[topic.uid] = levels[topic.parent_uid] + 1 if topic.parent_uid in levels else 1
    return max(levels.values()) if uid in live else 0


def check_parent(
    topics: Sequence[Topic], project_uid: str, parent_uid: str | None, below: str | None, max_depth: int
) -> None:
    """Darf ein Topic (neu, oder `below` wird verschoben) unter `parent_uid` hängen?

    Das Topic gehört in dasselbe Projekt, der Parent darf nicht das Topic selbst oder sein Nachkomme sein, und der
    ganze Teilbaum muss in die Tiefe passen.
    """
    if parent_uid is None:
        needed = height(topics, below) if below else 1
        if needed > max_depth:
            raise MemosViolation(
                "topic_too_deep", f"Der Teilbaum ist mit {needed} Ebenen tiefer als erlaubt ({max_depth})"
            )
        return
    live = _live(topics)
    parent = live.get(parent_uid)
    if parent is None:
        raise MemosViolation("topic_parent_missing", "Das Parent-Topic gibt es nicht", parent=parent_uid)
    if parent.project_uid != project_uid:
        raise MemosViolation("topic_other_project", "Das Parent-Topic gehört zu einem anderen Projekt")
    if parent.archived_at is not None:
        raise MemosViolation("topic_archived", f"Das Topic {parent.name} ist archiviert", topic=parent.label)
    if below is not None and parent_uid in {t.uid for t in subtree(topics, below)}:
        raise MemosViolation("topic_loop", "Ein Topic lässt sich nicht unter sich selbst hängen", topic=below)
    needed = depth(live, parent_uid) + (height(topics, below) if below else 1)
    if needed > max_depth:
        raise MemosViolation(
            "topic_too_deep",
            f"Das Topic läge auf Ebene {needed}; erlaubt sind {max_depth}",
            depth=needed,
            max_depth=max_depth,
        )


@dataclass(frozen=True)
class Content:
    """Was in einem Topic samt Unter-Topics liegt."""

    topics: int
    active: int
    archived: int

    @property
    def empty(self) -> bool:
        return not (self.topics or self.active or self.archived)


def _memos_in(memos: Sequence[Memo], uids: set[str]) -> list[Memo]:
    return [n for n in memos if n.deleted_at is None and n.topic_uid in uids]


def content(topics: Sequence[Topic], memos: Sequence[Memo], uid: str) -> Content:
    tree = subtree(topics, uid)
    inside = _memos_in(memos, {t.uid for t in tree})
    return Content(len(tree) - 1, sum(1 for n in inside if not n.archived), sum(1 for n in inside if n.archived))


@dataclass(frozen=True)
class Choice:
    """Die Wahl des Auswahldialogs beim Löschen oder Archivieren eines Topics mit Inhalt."""

    #: Archivierte Memos behalten: sie wandern ins Topic „Archiviert“ (statt mit dem Topic zu verschwinden).
    keep_archived: bool = False
    #: Aktive Memos: `delete` mit dem Topic, `move` zu `move_to`, `archive` (nur Archivieren) mit dem Topic.
    active: ActiveChoice | None = None
    #: Ziel für `move` (ein Topic oder `None` für „Ohne Topic“).
    move_to: str | None = None


@dataclass(frozen=True)
class TopicPlan:
    """`topics`: die betroffenen Topics (das Topic zuerst); `memos`: die Memos, die mit ihnen den Zustand ändern
    (löschen oder archivieren); `moves`: Memo → neues Topic (`ARCHIVE_TARGET`, eine `uid` oder `None`)."""

    topics: tuple[str, ...]
    memos: tuple[str, ...] = ()
    moves: dict[str, str | None] = field(default_factory=dict)


def _check_target(topics: Sequence[Topic], tree: set[str], move_to: str | None) -> None:
    if move_to is None:
        return
    live = _live(topics)
    target = live.get(move_to)
    if target is None or target.archived_at is not None:
        raise MemosViolation(
            "topic_parent_missing", "Das Zieltopic gibt es nicht oder es ist archiviert", target=move_to
        )
    if move_to in tree:
        raise MemosViolation("topic_target_inside", "Das Zieltopic liegt im Topic selbst", target=move_to)


def _plan(
    topics: Sequence[Topic], memos: Sequence[Memo], uid: str, choice: Choice | None, *, archiving: bool
) -> TopicPlan:
    tree = subtree(topics, uid)
    if not tree:
        raise MemosViolation("topic_deleted", "Das Topic gibt es nicht oder es liegt im Papierkorb", topic=uid)
    found = content(topics, memos, uid)
    inside = _memos_in(memos, {t.uid for t in tree})
    if (inside or len(tree) > 1) and choice is None:
        raise MemosViolation(
            "topic_has_content",
            f"Das Topic hat Inhalt: {found.active} aktive und {found.archived} archivierte Memos, "
            f"{found.topics} Unter-Topics",
            active=found.active,
            archived=found.archived,
            topics=found.topics,
        )
    if choice is None:
        return TopicPlan(tuple(t.uid for t in tree))
    if choice.active == "move":
        _check_target(topics, {t.uid for t in tree}, choice.move_to)
    if choice.active == "archive" and not archiving:
        raise MemosViolation("choice_invalid", "Aktive Memos lassen sich nur beim Archivieren mitarchivieren")
    if choice.active is None and found.active:
        raise MemosViolation("choice_missing", "Für die aktiven Memos fehlt die Wahl", active=found.active)
    moves: dict[str, str | None] = {}
    affected: list[str] = []
    for memo in inside:
        if memo.archived:
            if choice.keep_archived:
                moves[memo.uid] = ARCHIVE_TARGET
            else:
                affected.append(memo.uid)
        elif choice.active == "move":
            moves[memo.uid] = choice.move_to
        else:
            affected.append(memo.uid)
    return TopicPlan(tuple(t.uid for t in tree), tuple(affected), moves)


def plan_delete(topics: Sequence[Topic], memos: Sequence[Memo], uid: str, choice: Choice | None) -> TopicPlan:
    """Löschen: mit Inhalt nur mit Wahl; nicht gewählte Gruppen gehen mit dem Topic in den Papierkorb."""
    topic = next((t for t in topics if t.uid == uid), None)
    if topic is not None and topic.system:
        raise MemosViolation("topic_system", f"Das Topic {topic.name} lässt sich nicht löschen", topic=topic.label)
    if choice is not None and choice.active == "archive":
        raise MemosViolation("choice_invalid", "Aktive Memos lassen sich nur beim Archivieren mitarchivieren")
    return _plan(topics, memos, uid, choice, archiving=False)


def plan_archive(topics: Sequence[Topic], memos: Sequence[Memo], uid: str, choice: Choice | None) -> TopicPlan:
    """Archivieren: wie Löschen, dazu darf man aktive Memos einfach mitarchivieren (`active="archive"`)."""
    topic = next((t for t in topics if t.uid == uid), None)
    if topic is not None and topic.system:
        raise MemosViolation("topic_system", f"Das Topic {topic.name} lässt sich nicht archivieren", topic=topic.label)
    if topic is not None and topic.archived_at is not None:
        raise MemosViolation("topic_archived", f"Das Topic {topic.name} ist schon archiviert", topic=topic.label)
    if choice is not None and choice.active == "delete":
        raise MemosViolation("choice_invalid", "Beim Archivieren werden aktive Memos nicht gelöscht")
    return _plan(topics, memos, uid, choice, archiving=True)


def plan_reactivate(topics: Sequence[Topic], memos: Sequence[Memo], uid: str) -> TopicPlan:
    """Das Topic samt archivierten Unter-Topics und die Memos, die nur wegen des Topics archiviert waren (also nicht
    erledigt, verworfen oder befördert), werden wieder aktiv. Ein archivierter Parent muss zuerst zurück."""
    live = _live(topics)
    topic = live.get(uid)
    if topic is None:
        raise MemosViolation("topic_deleted", "Das Topic gibt es nicht oder es liegt im Papierkorb", topic=uid)
    if topic.archived_at is None:
        raise MemosViolation("topic_not_archived", f"Das Topic {topic.name} ist nicht archiviert", topic=topic.label)
    parent = live.get(topic.parent_uid) if topic.parent_uid else None
    if parent is not None and parent.archived_at is not None:
        raise MemosViolation(
            "topic_archived",
            f"Das Parent-Topic {parent.name} ist archiviert; erst dieses reaktivieren",
            topic=topic.label,
        )
    tree = [t for t in subtree(topics, uid) if t.archived_at is not None]
    inside = _memos_in(memos, {t.uid for t in tree})
    return TopicPlan(
        tuple(t.uid for t in tree), tuple(n.uid for n in inside if n.archived and n.status not in FINISHED_STATUSES)
    )
