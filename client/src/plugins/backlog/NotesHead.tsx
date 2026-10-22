import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import { Box, Button, Stack, Tooltip, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { MarkdownView } from "../../shared";
import { useGetNotesStateQuery, useListNotesEntriesQuery, type ItemOut } from "./api";
import { needsAttention } from "./model";
import { useNotesMarkText } from "./useNotesMarkText";
import { backlogTestIds as ids } from "./testIds";

/** The entry text without its heading line (`## day — topic`), which is shown as the title of the entry. */
const withoutHeading = (text: string) => (text.startsWith("## ") ? text.slice(text.indexOf("\n") + 1) : text);

/** The head of the notes of an item above its log; the log is folded until it is asked for. Nothing without notes. */
export function NotesHead({ item }: { item: ItemOut }) {
	const { t } = useTranslation("backlog");
	const hasNotes = item.notes.length > 0;
	const [logOpen, setLogOpen] = useState(false);
	const { data: head } = useGetNotesStateQuery(item.uid, { skip: !hasNotes });
	const { data: entries } = useListNotesEntriesQuery(item.uid, { skip: !hasNotes || !logOpen });
	const state = head?.state ?? item.notes_state;
	const mark = useNotesMarkText(state);
	if (!hasNotes) return null;

	return (
		<Stack spacing={0.5} data-testid={ids.notesHead}>
			<Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
				<Typography variant="subtitle2">{t("notes.head")}</Typography>
				{needsAttention(state) && mark && (
					<Tooltip title={mark}>
						<Box component="span" role="img" aria-label={mark} data-testid={ids.notesHeadWarning} sx={{ display: "inline-flex", color: "warning.main" }}>
							<WarningAmberIcon fontSize="small" />
						</Box>
					</Tooltip>
				)}
			</Box>
			<Box data-testid={ids.notesHeadContent}>
				{head?.content ? (
					<MarkdownView source={head.content} />
				) : (
					<Typography variant="body2" color="text.secondary">
						{t("notes.noHead")}
					</Typography>
				)}
			</Box>
			<Button
				size="small"
				onClick={() => setLogOpen((value) => !value)}
				startIcon={logOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
				aria-expanded={logOpen}
				data-testid={ids.notesLogToggle}
				sx={{ alignSelf: "flex-start", textTransform: "none" }}
			>
				{t("notes.log")}
			</Button>
			{logOpen &&
				[...(entries ?? [])].reverse().map((entry) => (
					<Box key={entry.position} data-testid={ids.notesLogEntry(entry.position)} sx={{ pl: 1, borderLeft: 2, borderColor: "divider" }}>
						<Typography variant="subtitle2">{`${entry.day} — ${entry.topic}`}</Typography>
						<MarkdownView source={withoutHeading(entry.text)} />
					</Box>
				))}
		</Stack>
	);
}
