import { Alert, Box, Button, Stack, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toWriteError, useDecideNoticeMutation, type NoteOut } from "./api";
import { noticeText } from "./noticeText";
import { PromoteDialog } from "./PromoteDialog";
import { notesTestIds } from "./testIds";

/**
 * The section "Notices" of the note detail: what happened to a linked item since, with one button per possible
 * decision. "Promote" asks for the fields of the new item first.
 */
export function NoticesSection({ note }: { note: NoteOut }) {
	const { t } = useTranslation("notes");
	const [decide] = useDecideNoticeMutation();
	const [promoting, setPromoting] = useState<string>();
	const [error, setError] = useState<string>();

	if (note.notices.length === 0) {
		return (
			<Typography variant="body2" color="text.secondary" data-testid={notesTestIds.notices}>
				{t("notices.none")}
			</Typography>
		);
	}
	return (
		<Stack spacing={1.5} data-testid={notesTestIds.notices}>
			{note.notices.map((notice) => (
				<Box key={notice.uid} data-testid={notesTestIds.notice(notice.uid)}>
					<Typography variant="body2">{noticeText(notice, t)}</Typography>
					<Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mt: 0.5 }}>
						{notice.decisions.map((decision) => (
							<Button
								key={decision}
								size="small"
								variant="outlined"
								data-testid={notesTestIds.noticeDecision(notice.uid, decision)}
								onClick={() => {
									setError(undefined);
									if (decision === "promote") setPromoting(notice.uid);
									else
										decide({ uid: notice.uid, decision, version: note.version })
											.unwrap()
											.catch((failure: unknown) => setError(toWriteError(failure).message));
								}}
							>
								{t(`notices.decision.${decision}`)}
							</Button>
						))}
					</Box>
				</Box>
			))}
			{error && <Alert severity="error">{error}</Alert>}
			{promoting && <PromoteDialog note={note} noticeUid={promoting} onClose={() => setPromoting(undefined)} />}
		</Stack>
	);
}
