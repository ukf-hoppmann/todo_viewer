import { useMemo, useState } from "react";
import { useNotesIndex, useSourceList } from "../api/queries";
import { NoteCreateDialog } from "../components/NoteCreateDialog";
import { NoteList } from "../components/NoteList";
import { TopicTree } from "../components/TopicTree";
import { notesOfTopic, sortNotes } from "../domain/notes";
import { describeError, useI18n } from "../i18n/i18n";
import { usePollingPaused } from "../state/pollingPause";
import { useUiState } from "../state/useUiStateStore";

/** The Notes area: the topic tree on the left, the notes of the chosen topic next to it. */
export function NotesView() {
  const i18n = useI18n();
  const { t } = i18n;
  const { state, dispatch } = useUiState();
  const index = useNotesIndex(usePollingPaused());
  const sources = useSourceList();
  const [creating, setCreating] = useState(false);

  const projects = useMemo(() => [...new Set((sources.data ?? []).filter((s) => !s.problem).map((s) => s.project))], [sources.data]);
  const allTopics = index.data?.topics;
  const topics = useMemo(
    () => (allTopics ?? []).filter((x) => state.notesProject === null || x.project === state.notesProject),
    [allTopics, state.notesProject],
  );
  const notes = useMemo(
    () =>
      sortNotes(
        notesOfTopic(index.data?.notes ?? [], allTopics ?? [], state.notesTopic?.project ?? state.notesProject, state.notesTopic?.label ?? null, true),
      ),
    [index.data?.notes, allTopics, state.notesProject, state.notesTopic],
  );
  const defaultProject = state.notesTopic?.project ?? state.notesProject ?? projects[0] ?? "";

  if (index.error && !index.data) return <div className="load-error">{t("err.load", { e: describeError(i18n, index.error) })}</div>;
  if (!index.data) return <div className="view hint">{t("notes.loading")}</div>;

  return (
    <div className="view notes-view">
      <aside className="notes-side">
        <label className="field notes-project">
          {t("notes.project")}
          <select
            value={state.notesProject ?? ""}
            onChange={(e) => dispatch({ type: "notesScope", project: e.target.value || null, topic: null })}
          >
            <option value="">{t("notes.allProjects")}</option>
            {projects.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
        <TopicTree
          topics={topics}
          allTopics={allTopics ?? []}
          projects={projects}
          defaultProject={defaultProject}
          selected={state.notesTopic}
          onSelect={(topic) => dispatch({ type: "notesScope", project: state.notesProject, topic })}
        />
      </aside>
      <section className="notes-main">
        <div className="notes-head">
          <span className="hint">{t("notes.count", { n: notes.length })}</span>
          <button className="btn small primary" disabled={projects.length === 0} onClick={() => setCreating(true)}>
            {t("notes.newNote")}
          </button>
        </div>
        {projects.length === 0 && <div className="hint">{t("notes.noProject")}</div>}
        <NoteList
          notes={notes}
          selected={state.selectedNote}
          showProject={state.notesProject === null && projects.length > 1}
          onSelect={(note) => dispatch({ type: "selectNote", note })}
        />
      </section>
      {creating && (
        <NoteCreateDialog
          projects={projects}
          topics={allTopics ?? []}
          project={defaultProject}
          topic={state.notesTopic?.project === defaultProject ? state.notesTopic.label : null}
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
