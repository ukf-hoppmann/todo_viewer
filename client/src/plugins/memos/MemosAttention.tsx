import CancelIcon from "@mui/icons-material/Cancel";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import PushPinIcon from "@mui/icons-material/PushPin";
import SnoozeIcon from "@mui/icons-material/Snooze";
import MemosIcon from "@mui/icons-material/StickyNote2";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { viewPath } from "../../core";
import { useProjectSelection, useReportAttention, type AttentionAction, type AttentionEntry } from "../workspace";
import { useDecideHintMutation, useGetDueQuery, useMemoActionMutation, type DueMemoOut } from "./api";
import { attentionOf } from "./model";
import { useMemosState } from "./state";
import { memosTestIds } from "./testIds";

/**
 * The due memos for the bell of `workspace` (slot `workspace.attention-sources`), with the actions of each memo (or the
 * decisions of its hint); opening one shows it in the memos view (its project is switched on if it was hidden).
 * The list reloads on the events of `memos`, also `memos.due` when a review date or a topic date has come.
 */
export function MemosAttention() {
	const { t } = useTranslation("memos");
	const { data } = useGetDueQuery();
	const [act] = useMemoActionMutation();
	const [decide] = useDecideHintMutation();
	const { setSelected } = useMemosState();
	const { visible, toggleVisible } = useProjectSelection();
	const navigate = useNavigate();

	const entries = useMemo<AttentionEntry[]>(() => {
		const actionsOf = (memo: DueMemoOut): AttentionAction[] => {
			const hint = memo.reason === "hint" ? memo.hints[0] : undefined;
			if (hint) {
				return hint.decisions
					.filter((decision) => decision !== "promote")
					.map((decision) => ({
						id: decision,
						label: t(`hints.decision.${decision}`),
						run: () => void decide({ uid: hint.uid, decision, version: memo.version }),
						testId: memosTestIds.dueAction(decision, memo.uid),
					}));
			}
			const ref = { uid: memo.uid, version: memo.version };
			return [
				{ id: "keep", label: t("action.keep"), icon: PushPinIcon, run: () => void act({ ...ref, action: "keep" }), testId: memosTestIds.dueAction("keep", memo.uid) },
				{ id: "snooze", label: t("action.snooze"), icon: SnoozeIcon, run: () => void act({ ...ref, action: "snooze" }), testId: memosTestIds.dueAction("snooze", memo.uid) },
				{
					id: "done",
					label: t("action.done"),
					icon: CheckCircleIcon,
					run: () => void act({ ...ref, action: "finish", status: "done" }),
					testId: memosTestIds.dueAction("done", memo.uid),
				},
				{
					id: "dropped",
					label: t("action.dropped"),
					icon: CancelIcon,
					run: () => void act({ ...ref, action: "finish", status: "dropped" }),
					testId: memosTestIds.dueAction("dropped", memo.uid),
				},
			];
		};
		return (data?.memos ?? []).map((memo) => ({
			...attentionOf(memo, t(`due.reason.${memo.reason}`)),
			icon: MemosIcon,
			actions: actionsOf(memo),
			open: () => {
				if (!visible.some((project) => project.uid === memo.project_uid)) toggleVisible(memo.project_uid);
				setSelected(memo.uid);
				void navigate(viewPath("memos", "main"));
			},
		}));
	}, [data, t, act, decide, visible, toggleVisible, setSelected, navigate]);
	useReportAttention(entries);
	return null;
}
