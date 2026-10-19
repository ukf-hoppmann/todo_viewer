import CancelIcon from "@mui/icons-material/Cancel";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import PushPinIcon from "@mui/icons-material/PushPin";
import SnoozeIcon from "@mui/icons-material/Snooze";
import NotesIcon from "@mui/icons-material/StickyNote2";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { viewPath } from "../../core";
import { useProjectSelection, useReportAttention, type AttentionAction, type AttentionEntry } from "../workspace";
import { useDecideNoticeMutation, useGetDueQuery, useNoteActionMutation, type DueNoteOut } from "./api";
import { attentionOf } from "./model";
import { useNotesState } from "./state";
import { notesTestIds } from "./testIds";

/** How often the due notes are asked for again: notes become due with the clock, not by an event. */
const POLL_MS = 60_000;

/**
 * The due notes for the bell of `workspace` (slot `workspace.attention-sources`), with the actions of each note (or the
 * decisions of its notice); opening one shows it in the notes view (its project is switched on if it was hidden).
 */
export function NotesAttention() {
	const { t } = useTranslation("notes");
	const { data } = useGetDueQuery(undefined, { pollingInterval: POLL_MS });
	const [act] = useNoteActionMutation();
	const [decide] = useDecideNoticeMutation();
	const { setSelected } = useNotesState();
	const { visible, toggleVisible } = useProjectSelection();
	const navigate = useNavigate();

	const entries = useMemo<AttentionEntry[]>(() => {
		const actionsOf = (note: DueNoteOut): AttentionAction[] => {
			const notice = note.reason === "notice" ? note.notices[0] : undefined;
			if (notice) {
				return notice.decisions
					.filter((decision) => decision !== "promote")
					.map((decision) => ({
						id: decision,
						label: t(`notices.decision.${decision}`),
						run: () => void decide({ uid: notice.uid, decision, version: note.version }),
						testId: notesTestIds.dueAction(decision, note.uid),
					}));
			}
			const ref = { uid: note.uid, version: note.version };
			return [
				{ id: "keep", label: t("action.keep"), icon: PushPinIcon, run: () => void act({ ...ref, action: "keep" }), testId: notesTestIds.dueAction("keep", note.uid) },
				{ id: "snooze", label: t("action.snooze"), icon: SnoozeIcon, run: () => void act({ ...ref, action: "snooze" }), testId: notesTestIds.dueAction("snooze", note.uid) },
				{
					id: "done",
					label: t("action.done"),
					icon: CheckCircleIcon,
					run: () => void act({ ...ref, action: "finish", status: "done" }),
					testId: notesTestIds.dueAction("done", note.uid),
				},
				{
					id: "dropped",
					label: t("action.dropped"),
					icon: CancelIcon,
					run: () => void act({ ...ref, action: "finish", status: "dropped" }),
					testId: notesTestIds.dueAction("dropped", note.uid),
				},
			];
		};
		return (data?.notes ?? []).map((note) => ({
			...attentionOf(note, t(`due.reason.${note.reason}`)),
			icon: NotesIcon,
			actions: actionsOf(note),
			open: () => {
				if (!visible.some((project) => project.uid === note.project_uid)) toggleVisible(note.project_uid);
				setSelected(note.uid);
				void navigate(viewPath("notes", "main"));
			},
		}));
	}, [data, t, act, decide, visible, toggleVisible, setSelected, navigate]);
	useReportAttention(entries);
	return null;
}
