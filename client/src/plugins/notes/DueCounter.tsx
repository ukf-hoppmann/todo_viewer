import { Box, Popover, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { viewPath } from "../../core";
import { useGetDueQuery } from "./api";
import { useNotesState } from "./state";
import { notesTestIds } from "./testIds";

/** How often the counter asks again: notes become due with the clock, not by an event. */
const POLL_MS = 60_000;

/**
 * A discreet red exclamation mark with the number of due notes in the app bar (and in the title of the browser tab).
 * A click lists them; choosing one opens it in the notes view.
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
				<Box sx={{ p: 1, minWidth: 260 }} data-testid={notesTestIds.dueList}>
					<Typography variant="overline">{t("due.title")}</Typography>
					{data?.notes.map((note) => (
						<Box
							key={note.uid}
							component="button"
							type="button"
							onClick={() => {
								setSelected(note.uid);
								setAnchor(null);
								void navigate(viewPath("notes", "main"));
							}}
							data-testid={notesTestIds.dueItem(note.uid)}
							sx={{ display: "block", width: "100%", textAlign: "left", bgcolor: "transparent", border: 0, color: "inherit", cursor: "pointer", font: "inherit", py: 0.5 }}
						>
							{`${note.label} — ${note.summary}`}
						</Box>
					))}
				</Box>
			</Popover>
		</>
	);
}
