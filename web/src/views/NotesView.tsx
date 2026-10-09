import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { type NotesIndexFilter, useNotesIndex, useSourceList } from "../api/queries";
import { IconButton } from "../components/IconButton";
import { NoteCreateDialog } from "../components/NoteCreateDialog";
import { NoteTree } from "../components/NoteTree";
import type { Item } from "../domain/model";
import { buildNoteTree, noteTreeAncestors, shownNoteStatuses } from "../domain/notes";
import { describeError, useI18n } from "../i18n/i18n";
import { usePollingPaused } from "../state/pollingPause";
import { INITIAL_UI_STATE } from "../state/uiState";
import { useUiState } from "../state/useUiStateStore";

// The detail brings the markdown renderer; it is loaded when a note is opened.
const NoteDetail = lazy(() => import("../components/NoteDetail").then((m) => ({ default: m.NoteDetail })));

/** The Notes area: the notes as a tree (project → topic → note), the open note next to it. Projects, statuses and the
 *  search come from the sidebar. */
export function NotesView({ items }: { items: readonly Item[] }) {
  const i18n = useI18n();
  const { t } = i18n;
  const { state, dispatch } = useUiState();
  const paused = usePollingPaused();
  const sources = useSourceList();
  // Where a new note starts: a project and maybe a topic; null while the dialog is closed.
  const [creating, setCreating] = useState<{ project: string; topic: string | null } | null>(null);

  // The projects and statuses ticked in the sidebar. The server cuts by one project and the statuses; with several
  // projects ticked the browser cuts by the project. With no status ticked no note is shown. The unfiltered index
  // stays for the topic dialogs and the link pickers.
  const projects = useMemo(() => [...new Set((sources.data ?? []).filter((s) => !s.problem).map((s) => s.project))], [sources.data]);
  const visible = useMemo(() => projects.filter((p) => !state.hiddenProjects.has(p)).sort(), [projects, state.hiddenProjects]);
  const onlyProject = visible.length === 1 ? visible[0] : undefined;
  const statuses = shownNoteStatuses(state.hiddenNoteStatuses);
  const filter: NotesIndexFilter = {
    ...(onlyProject !== undefined && { project: onlyProject }),
    ...(statuses.length > 0 && { status: statuses }),
  };
  const index = useNotesIndex(paused, filter);
  const everything = useNotesIndex(paused);
  const search = state.search;
  const defaultStatuses = shownNoteStatuses(INITIAL_UI_STATE.hiddenNoteStatuses);
  const filtered = statuses.join() !== defaultStatuses.join() || search.trim() !== "";

  const allTopics = everything.data?.topics ?? index.data?.topics;
  const anyStatus = statuses.length > 0;
  const tree = useMemo(
    () => buildNoteTree(visible, index.data?.topics ?? [], anyStatus ? (index.data?.notes ?? []) : [], search),
    [visible, index.data?.topics, index.data?.notes, anyStatus, search],
  );
  const shownCount = tree.reduce((sum, p) => sum + p.count, 0);

  // A note opened from elsewhere (due list, link, item) gets its branch unfolded.
  const selected = state.selectedNote;
  const selectedNote = [...(index.data?.notes ?? []), ...(everything.data?.notes ?? [])].find((n) => n.project === selected?.project && n.label === selected.label);
  const unfold = selectedNote && allTopics ? noteTreeAncestors(allTopics, selectedNote).join("\u0000") : "";
  useEffect(() => {
    if (unfold !== "") dispatch({ type: "setCollapsed", uids: unfold.split("\u0000"), collapsed: false });
  }, [unfold, dispatch]);

  const reset = () => {
    dispatch({ type: "resetNoteStatuses" });
    dispatch({ type: "search", text: "" });
  };

  if (index.error && !index.data) return <div className="load-error">{t("err.load", { e: describeError(i18n, index.error) })}</div>;
  if (!index.data) return <div className="view hint">{t("notes.loading")}</div>;

  return (
    <div className="view notes-view">
      <section className="notes-main">
        <div className="notes-head">
          <span className="hint">{t("notes.count", { n: shownCount })}</span>
          {filtered && <IconButton icon="reset" label={t("notes.filter.reset")} onClick={reset} />}
          <button
            className="btn small primary"
            disabled={projects.length === 0}
            onClick={() => setCreating({ project: visible[0] ?? projects[0] ?? "", topic: null })}
          >
            {t("notes.newNote")}
          </button>
        </div>
        {projects.length === 0 && <div className="hint">{t("notes.noProject")}</div>}
        {projects.length > 0 && shownCount === 0 && <div className="hint note-empty">{t("notes.empty")}</div>}
        <NoteTree
          tree={tree}
          allTopics={allTopics ?? []}
          projects={projects}
          selected={selected}
          searching={search.trim() !== ""}
          onSelect={(note) => dispatch({ type: "selectNote", note })}
          onCreateNote={(project, topic) => setCreating({ project, topic })}
        />
      </section>
      {selected && (
        <Suspense fallback={null}>
          <NoteDetail
            key={`${selected.project}/${selected.label}`}
            note={selected}
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
          project={creating.project}
          topic={creating.topic}
          onClose={() => setCreating(null)}
          onCreated={(note) => {
            setCreating(null);
            dispatch({ type: "selectNote", note });
          }}
        />
      )}
    </div>
  );
}
