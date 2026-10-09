import { lazy, Suspense, useMemo, useState } from "react";
import { type NotesIndexFilter, useNotesIndex, useSourceList } from "../api/queries";
import type { Schemas } from "../api/client";
import { IconButton } from "../components/IconButton";
import { NoteCreateDialog } from "../components/NoteCreateDialog";
import { NoteList } from "../components/NoteList";
import { TopicTree } from "../components/TopicTree";
import type { Item } from "../domain/model";
import { groupNotesByTopic, notesOfTopic, searchNotes, sortNotes } from "../domain/notes";
import { describeError, useI18n } from "../i18n/i18n";
import type { MessageKey } from "../i18n/messages";
import { usePollingPaused } from "../state/pollingPause";
import { useUiState } from "../state/useUiStateStore";

type NoteStatus = Schemas["NoteStatus"];
const NOTE_STATUSES: readonly NoteStatus[] = ["waiting", "due", "snoozed", "done", "dropped", "promoted"];

// The detail brings the markdown renderer; it is loaded when a note is opened.
const NoteDetail = lazy(() => import("../components/NoteDetail").then((m) => ({ default: m.NoteDetail })));

/** The Notes area: the topic tree on the left, the notes of the chosen topic next to it. */
export function NotesView({ items }: { items: readonly Item[] }) {
  const i18n = useI18n();
  const { t } = i18n;
  const { state, dispatch } = useUiState();
  const paused = usePollingPaused();
  const sources = useSourceList();
  const [creating, setCreating] = useState(false);
  const [status, setStatus] = useState<NoteStatus | "">("");
  const [dueOnly, setDueOnly] = useState(false);
  const [search, setSearch] = useState("");
  const [subtopics, setSubtopics] = useState(true);
  const [grouped, setGrouped] = useState(false);

  // The projects ticked in the sidebar. The server cuts by one project, status and due; with several projects ticked the
  // browser cuts by the project. The unfiltered index stays for the topic dialogs and the link pickers.
  const projects = useMemo(() => [...new Set((sources.data ?? []).filter((s) => !s.problem).map((s) => s.project))], [sources.data]);
  const visible = useMemo(() => new Set(projects.filter((p) => !state.hiddenProjects.has(p))), [projects, state.hiddenProjects]);
  const onlyProject = visible.size === 1 ? [...visible][0] : undefined;
  const filter: NotesIndexFilter = {
    ...(onlyProject !== undefined && { project: onlyProject }),
    ...(status !== "" && { status: [status] }),
    ...(dueOnly && { due: true }),
  };
  const index = useNotesIndex(paused, filter);
  const everything = useNotesIndex(paused);
  const filtered = status !== "" || dueOnly || search.trim() !== "";
  const topic = state.notesTopic !== null && visible.has(state.notesTopic.project) ? state.notesTopic : null;

  const allTopics = everything.data?.topics ?? index.data?.topics;
  const shownTopics = useMemo(() => (index.data?.topics ?? []).filter((x) => visible.has(x.project)), [index.data?.topics, visible]);
  const notes = useMemo(
    () =>
      sortNotes(
        searchNotes(
          notesOfTopic((index.data?.notes ?? []).filter((n) => visible.has(n.project)), shownTopics, topic?.project ?? null, topic?.label ?? null, subtopics),
          search,
        ),
      ),
    [index.data?.notes, shownTopics, visible, topic, subtopics, search],
  );
  const groups = useMemo(() => (grouped ? groupNotesByTopic(notes, shownTopics ?? []) : null), [grouped, notes, shownTopics]);
  const reset = () => {
    setStatus("");
    setDueOnly(false);
    setSearch("");
  };
  const defaultProject = topic?.project ?? [...visible][0] ?? projects[0] ?? "";

  if (index.error && !index.data) return <div className="load-error">{t("err.load", { e: describeError(i18n, index.error) })}</div>;
  if (!index.data) return <div className="view hint">{t("notes.loading")}</div>;

  return (
    <div className="view notes-view">
      <aside className="notes-side">
        <TopicTree
          topics={shownTopics}
          allTopics={allTopics ?? []}
          projects={projects}
          defaultProject={defaultProject}
          selected={topic}
          onSelect={(topic) => dispatch({ type: "notesScope", topic })}
        />
      </aside>
      <section className="notes-main">
        <div className="notes-head">
          <span className="hint">{t("notes.count", { n: notes.length })}</span>
          <button className="btn small primary" disabled={projects.length === 0} onClick={() => setCreating(true)}>
            {t("notes.newNote")}
          </button>
        </div>
        <div className="notes-filter" role="search" aria-label={t("notes.filter")}>
          <select aria-label={t("notes.filter.status")} value={status} onChange={(e) => setStatus(e.target.value as NoteStatus | "")}>
            <option value="">{t("notes.filter.open")}</option>
            {NOTE_STATUSES.map((s) => (
              <option key={s} value={s}>
                {t(`note.status.${s}` as MessageKey)}
              </option>
            ))}
          </select>
          <label className="check">
            <input type="checkbox" checked={dueOnly} onChange={(e) => setDueOnly(e.target.checked)} />
            {t("notes.filter.dueOnly")}
          </label>
          <input type="search" className="notes-search" placeholder={t("notes.filter.search")} aria-label={t("notes.filter.search")} value={search} onChange={(e) => setSearch(e.target.value)} />
          {topic && (
            <label className="check" title={t("notes.filter.subtopicsHint")}>
              <input type="checkbox" checked={subtopics} onChange={(e) => setSubtopics(e.target.checked)} />
              {t("notes.filter.subtopics")}
            </label>
          )}
          <IconButton icon="group" label={t("notes.filter.group")} pressed={grouped} onClick={() => setGrouped(!grouped)} />
          {filtered && <IconButton icon="reset" label={t("notes.filter.reset")} onClick={reset} />}
        </div>
        {projects.length === 0 && <div className="hint">{t("notes.noProject")}</div>}
        <NoteList
          groups={groups}
          notes={notes}
          selected={state.selectedNote}
          showProject={visible.size > 1}
          onSelect={(note) => dispatch({ type: "selectNote", note })}
        />
      </section>
      {state.selectedNote && (
        <Suspense fallback={null}>
          <NoteDetail
            key={`${state.selectedNote.project}/${state.selectedNote.label}`}
            note={state.selectedNote}
            projects={projects}
            topics={allTopics ?? []}
            notes={everything.data?.notes ?? index.data.notes}
            items={items}
            onClose={() => dispatch({ type: "selectNote", note: null })}
            onOpenNote={(note) => dispatch({ type: "selectNote", note })}
          />
        </Suspense>
      )}
      {creating && (
        <NoteCreateDialog
          projects={projects}
          topics={allTopics ?? []}
          project={defaultProject}
          topic={topic?.project === defaultProject ? topic.label : null}
          onClose={() => setCreating(false)}
          onCreated={(note) => {
            setCreating(false);
            dispatch({ type: "selectNote", note });
          }}
        />
      )}
    </div>
  );
}
