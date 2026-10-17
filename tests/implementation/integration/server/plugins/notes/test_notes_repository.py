from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from viewer.plugins.notes.application.ports import Document
from viewer.plugins.notes.domain.model import Note, NotesSettings, Topic
from viewer.plugins.notes.infrastructure.database.repository import (
    SqlDocumentRepository,
    SqlNoteRepository,
    SqlSettingsRepository,
    SqlTopicRepository,
)
from workspace_env import Env

NOW = datetime(2026, 10, 17, 9, 30, tzinfo=UTC)


def test_topics_and_notes_round_trip_through_sqlite(notes: Env) -> None:
    project = str(notes.general()["uid"])
    registry = notes.workspace.registry
    topics, repo = SqlTopicRepository(), SqlNoteRepository()
    with notes.app.state.database.transaction() as tx:
        t_element = registry.register(tx, project, "topic", "Thema")
        topic = Topic(t_element.uid, project, t_element.label, "Thema", None, NOW, None, False, t_element.revision)
        topics.insert(tx, topic)
        n_element = registry.register(tx, project, "note", "Eine")
        note = Note(n_element.uid, project, n_element.label, "Eine", "Text", "snoozed", topic.uid, NOW, "all", False, 1)
        repo.insert(tx, note)
    with notes.app.state.database.transaction() as tx:
        assert topics.get(tx, topic.uid) == topic
        assert repo.get(tx, note.uid) == note
        assert [n.uid for n in repo.in_topic(tx, topic.uid)] == [note.uid]
        repo.update(tx, replace(note, status="done", archived=True, topic_uid=None))
        topics.update(tx, replace(topic, archived_at=NOW, system=True))
    with notes.app.state.database.transaction() as tx:
        stored = repo.get(tx, note.uid)
        assert stored is not None and (stored.status, stored.archived, stored.topic_uid) == ("done", True, None)
        assert topics.archive_topic_of(tx, project) is not None
        assert [t.uid for t in topics.list_in(tx, [project])] == [topic.uid]
        assert repo.list_in(tx, []) == []


def test_documents_keep_their_revision_and_go_with_the_note(notes: Env) -> None:
    project = str(notes.general()["uid"])
    repo, docs = SqlNoteRepository(), SqlDocumentRepository()
    with notes.app.state.database.transaction() as tx:
        element = notes.workspace.registry.register(tx, project, "note", "Mit Doku")
        repo.insert(
            tx, Note(element.uid, project, element.label, "Mit Doku", None, "waiting", None, None, "any", False, 1)
        )
        docs.insert(tx, Document(element.uid, f"{element.label}_spec.md", "spec", "s", 1, NOW))
        docs.insert(tx, Document(element.uid, f"{element.label}_notes.md", "notes", "n", 1, NOW))
        assert [d.kind for d in docs.list_for(tx, element.uid)] == ["notes", "spec"]
        assert docs.update(tx, element.uid, f"{element.label}_notes.md", "n2", 1, NOW) == 2
        loaded = repo.get(tx, element.uid)
        assert loaded is not None and loaded.documents == (f"{element.label}_notes.md", f"{element.label}_spec.md")
        repo.delete(tx, element.uid)
        assert docs.list_for(tx, element.uid) == []


def test_settings_default_and_survive_a_save(notes: Env) -> None:
    repo = SqlSettingsRepository()
    with notes.app.state.database.transaction() as tx:
        assert repo.load(tx) == NotesSettings()
        repo.save(tx, NotesSettings(5, 12))
        repo.save(tx, NotesSettings(6, 12))
    with notes.app.state.database.transaction() as tx:
        assert repo.load(tx) == NotesSettings(6, 12)
