import StickyNote2OutlinedIcon from "@mui/icons-material/StickyNote2Outlined";
import { Box, Tooltip, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useGetNotesStateQuery } from "./api";
import { useNotesMarkText } from "./useNotesMarkText";
import { backlogTestIds as ids } from "./testIds";

/**
 * A small notes symbol at a row of the list. Pointing at it shows the head of the notes (goal, next step, open,
 * decided) without opening the item; the head is fetched on the first look only. It turns to the warning color when
 * the head is out of date; a missing head (the usual case of older notes) only dims it, so the list stays calm.
 */
export function NotesPeek({ uid, state }: { uid: string; state: string }) {
	const { t } = useTranslation("backlog");
	const [asked, setAsked] = useState(false);
	const { data } = useGetNotesStateQuery(uid, { skip: !asked });
	const mark = useNotesMarkText(state);
	return (
		<Tooltip
			onOpen={() => setAsked(true)}
			placement="right"
			slotProps={{ tooltip: { sx: { maxWidth: 440, p: 1 } } }}
			title={
				<Box data-testid={ids.notesPeekText}>
					{mark && (
						<Typography variant="caption" sx={{ display: "block", fontWeight: "bold", mb: 0.5 }}>
							{mark}
						</Typography>
					)}
					{!data && asked && <Typography variant="caption">…</Typography>}
					{data && data.content && (
						<Typography variant="caption" component="div" sx={{ whiteSpace: "pre-wrap", maxHeight: 320, overflow: "hidden" }}>
							{data.content}
						</Typography>
					)}
				</Box>
			}
		>
			<Box
				component="span"
				role="img"
				aria-label={t("notes.peek")}
				data-testid={ids.notesPeek(uid)}
				data-state={state}
				sx={{ display: "inline-flex", flexShrink: 0, color: state === "stale" ? "warning.main" : state === "missing" ? "text.disabled" : "text.secondary" }}
			>
				<StickyNote2OutlinedIcon fontSize="small" />
			</Box>
		</Tooltip>
	);
}
