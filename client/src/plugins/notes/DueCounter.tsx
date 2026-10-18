import CancelIcon from "@mui/icons-material/Cancel";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import PushPinIcon from "@mui/icons-material/PushPin";
import SnoozeIcon from "@mui/icons-material/Snooze";
import { Box, Button, Popover, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { viewPath } from "../../core";
import { IconAction } from "../../shared";
import { REASONS } from "./constants";
import { useDecideNoticeMutation, useGetDueQuery, useNoteActionMutation, type DueNoteOut } from "./api";
import { useNotesState } from "./state";
import { notesTestIds } from "./testIds";

/** How often the counter asks again: notes become due with the clock, not by an event. */
const POLL_MS = 60_000;

/**
 * A discreet red exclamation mark with the number of due notes in the app bar (and in the title of the browser tab).
 * A click lists them grouped by the reason (trigger, notice, date, review) with the actions of each note; choosing a
 * note opens it in the notes view.
 */
export function DueCounter() {
	const { t } = useTranslation("notes");
	const { data } = useGetDueQuery(undefined, { pollingInterval: POLL_MS });
	const navigate = useNavigate();
	const { setSelected } = useNotesState();
	const [anchor, setAnchor] = useState<HTMLElement | null>(null);
	const count = data?.count ?? 0;

	useEffect(() => {
		const base = document.title.replace(/^\(\d+\) /, "");
		document.title = count > 0 ? `(${count}) ${base}` : base;
		return () => {
			document.title = base;
		};
	}, [count]);

	if (count === 0) return null;
	const open = (uid: string) => {
		setSelected(uid);
		setAnchor(null);
		void navigate(viewPath("notes", "main"));
	};
	return (
		<>
			<Box
				component="button"
				type="button"
				onClick={(event) => setAnchor(event.currentTarget)}
				aria-label={t("due.label", { count })}
				title={t("due.label", { count })}
				data-testid={notesTestIds.dueCounter}
				sx={{ bgcolor: "transparent", border: 0, color: "error.light", cursor: "pointer", font: "inherit", fontWeight: 700 }}
			>
				{`!${count}`}
			</Box>
			<Popover open={anchor !== null} anchorEl={anchor} onClose={() => setAnchor(null)}>
				<Box sx={{ p: 1, minWidth: 320, maxWidth: 520 }} data-testid={notesTestIds.dueList}>
					<Typography variant="overline">{t("due.title")}</Typography>
					{REASONS.map((reason) => {
						const group = (data?.notes ?? []).filter((note) => note.reason === reason);
						if (group.length === 0) return null;
						return (
							<Box key={reason} data-testid={notesTestIds.dueGroup(reason)} sx={{ mb: 1 }}>
								<Typography variant="caption" color="text.secondary" component="div">
									{t(`due.reason.${reason}`)}
								</Typography>
								{group.map((note) => (
									<DueRow key={note.uid} note={note} onOpen={() => open(note.uid)} />
								))}
							</Box>
						);
					})}
				</Box>
			</Popover>
		</>
	);
}

function DueRow({ note, onOpen }: { note: DueNoteOut; onOpen: () => void }) {
	const { t } = useTranslation("notes");
	const [act] = useNoteActionMutation();
	const [decide] = useDecideNoticeMutation();
	const notice = note.reason === "notice" ? note.notices[0] : undefined;
	const button = (action: string, label: string, run: () => unknown) => (
		<Button key={action} size="small" onClick={() => void run()} data-testid={notesTestIds.dueAction(action, note.uid)}>
			{label}
		</Button>
	);
	return (
		<Box sx={{ py: 0.5 }}>
			<Box
				component="button"
				type="button"
				onClick={onOpen}
				data-testid={notesTestIds.dueItem(note.uid)}
				sx={{ display: "block", width: "100%", textAlign: "left", bgcolor: "transparent", border: 0, color: "inherit", cursor: "pointer", font: "inherit" }}
			>
				{`${note.label} — ${note.summary}`}
				{note.path.length > 0 && (
					<Typography variant="caption" color="text.secondary" component="span">
						{` · ${note.path.join(" › ")}`}
					</Typography>
				)}
			</Box>
			<Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
				{notice?.decisions
					.filter((decision) => decision !== "promote")
					.map((decision) => button(decision, t(`notices.decision.${decision}`), () => decide({ uid: notice.uid, decision, version: note.version })))}
				{!notice && (
					<>
						<IconAction label={t("action.keep")} icon={PushPinIcon} onClick={() => void act({ uid: note.uid, version: note.version, action: "keep" })} testId={notesTestIds.dueAction("keep", note.uid)} />
						<IconAction label={t("action.snooze")} icon={SnoozeIcon} onClick={() => void act({ uid: note.uid, version: note.version, action: "snooze" })} testId={notesTestIds.dueAction("snooze", note.uid)} />
						<IconAction label={t("action.done")} icon={CheckCircleIcon} onClick={() => void act({ uid: note.uid, version: note.version, action: "finish", status: "done" })} testId={notesTestIds.dueAction("done", note.uid)} />
						<IconAction label={t("action.dropped")} icon={CancelIcon} onClick={() => void act({ uid: note.uid, version: note.version, action: "finish", status: "dropped" })} testId={notesTestIds.dueAction("dropped", note.uid)} />
					</>
				)}
			</Box>
		</Box>
	);
}
