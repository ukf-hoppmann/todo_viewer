import StickyNote2OutlinedIcon from "@mui/icons-material/StickyNote2Outlined";
import { Box, Tooltip, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useGetNotesStateQuery } from "./api";
import { HeadSections } from "./HeadSections";
import { useNotesMarkText } from "./useNotesMarkText";
import { backlogTestIds as ids } from "./testIds";

/**
 * A small notes symbol at a row of the list; the tree shows it only while the pointer or the focus is on the row. Pointing at it shows the head of the notes (goal, next step, open,
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
			slotProps={{
				tooltip: {
					sx: { maxWidth: 460, p: 1.5, bgcolor: "background.paper", color: "text.primary", border: 1, borderColor: "divider", boxShadow: 4 },
				},
			}}
			title={
				<Box data-testid={ids.notesPeekText} sx={{ maxHeight: 380, overflowY: "auto" }}>
					{mark && (
						<Typography variant="caption" component="div" sx={{ color: "warning.main", fontWeight: "bold", mb: 0.75 }}>
							{mark}
						</Typography>
					)}
					{!data && asked && <Typography variant="caption">…</Typography>}
					{data && data.content && <HeadSections content={data.content} compact />}
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
