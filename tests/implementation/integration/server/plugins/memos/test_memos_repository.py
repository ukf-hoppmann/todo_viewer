from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from viewer.plugins.memos.application.ports import Document
from viewer.plugins.memos.domain.model import Memo, MemosSettings, Topic
from viewer.plugins.memos.infrastructure.database.repository import (
    SqlDocumentRepository,
    SqlMemoRepository,
    SqlSettingsRepository,
    SqlTopicRepository,
)
from workspace_env import Env

NOW = datetime(2026, 10, 17, 9, 30, tzinfo=UTC)


def test_topics_and_memos_round_trip_through_sqlite(memos: Env) -> None:
    project = str(memos.general()["uid"])
    registry = memos.workspace.registry
    topics, repo = SqlTopicRepository(), SqlMemoRepository()
    with memos.app.state.database.transaction() as tx:
        t_element = registry.register(tx, project, "topic", "Thema")
        topic = Topic(t_element.uid, project, t_element.label, "Thema", None, NOW, None, False, t_element.revision)
        topics.insert(tx, topic)
        n_element = registry.register(tx, project, "memo", "Eine")
        memo = Memo(n_element.uid, project, n_element.label, "Eine", "Text", "snoozed", topic.uid, NOW, "all", False, 1)
        repo.insert(tx, memo)
    with memos.app.state.database.transaction() as tx:
        assert topics.get(tx, topic.uid) == topic
        assert repo.get(tx, memo.uid) == memo
        assert [n.uid for n in repo.in_topic(tx, topic.uid)] == [memo.uid]
        repo.update(tx, replace(memo, status="done", archived=True, topic_uid=None))
        topics.update(tx, replace(topic, archived_at=NOW, system=True))
    with memos.app.state.database.transaction() as tx:
        stored = repo.get(tx, memo.uid)
        assert stored is not None and (stored.status, stored.archived, stored.topic_uid) == ("done", True, None)
        assert topics.archive_topic_of(tx, project) is not None
        assert [t.uid for t in topics.list_in(tx, [project])] == [topic.uid]
        assert repo.list_in(tx, []) == []


def test_documents_keep_their_revision_and_go_with_the_memo(memos: Env) -> None:
    project = str(memos.general()["uid"])
    repo, docs = SqlMemoRepository(), SqlDocumentRepository()
    with memos.app.state.database.transaction() as tx:
        element = memos.workspace.registry.register(tx, project, "memo", "Mit Doku")
        repo.insert(
            tx, Memo(element.uid, project, element.label, "Mit Doku", None, "waiting", None, None, "any", False, 1)
        )
        docs.insert(tx, Document(element.uid, f"{element.label}_spec.md", "spec", "s", 1, NOW))
        docs.insert(tx, Document(element.uid, f"{element.label}_notes.md", "notes", "n", 1, NOW))
        assert [d.kind for d in docs.list_for(tx, element.uid)] == ["notes", "spec"]
        assert docs.update(tx, element.uid, f"{element.label}_notes.md", "n2", 1, NOW) == 2
        loaded = repo.get(tx, element.uid)
        assert loaded is not None and loaded.documents == (f"{element.label}_notes.md", f"{element.label}_spec.md")
        repo.delete(tx, element.uid)
        assert docs.list_for(tx, element.uid) == []


def test_settings_default_and_survive_a_save(memos: Env) -> None:
    repo = SqlSettingsRepository()
    with memos.app.state.database.transaction() as tx:
        assert repo.load(tx) == MemosSettings()
        repo.save(tx, MemosSettings(5, 12))
        repo.save(tx, MemosSettings(6, 12))
    with memos.app.state.database.transaction() as tx:
        assert repo.load(tx) == MemosSettings(6, 12)
