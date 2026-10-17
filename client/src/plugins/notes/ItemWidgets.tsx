import { Alert, Box, Button, Stack, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useItemDetail } from "../backlog";
import { toWriteError, useDecideNoticeMutation, useDemoteItemMutation, useListItemNoticesQuery } from "./api";
import { noticeText } from "./noticeText";
import { notesTestIds } from "./testIds";

/** In the detail panel of an item: the action "back to a note" (only while the item is open and not deleted). */
export function DemoteAction() {
	const { t } = useTranslation("notes");
	const item = useItemDetail();
	const [demote, { isLoading }] = useDemoteItemMutation();
	const [error, setError] = useState<string>();
	const [done, setDone] = useState<string>();
	if (item.deleted || (item.status !== "Open" && !done)) return null;
	return (
		<Stack spacing={0.5} data-testid={notesTestIds.demote}>
			{done ? (
				<Typography variant="body2" data-testid={notesTestIds.demoteDone}>
					{t("demote.done", { label: done })}
				</Typography>
			) : (
				<Box>
					<Button
						size="small"
						variant="outlined"
						disabled={isLoading}
						onClick={() => {
							setError(undefined);
							demote({ uid: item.uid, version: item.version })
								.unwrap()
								.then((result) => setDone(result.note.label))
								.catch((failure: unknown) => setError(toWriteError(failure).message));
						}}
						data-testid={notesTestIds.demoteButton}
					>
						{t("demote.button")}
					</Button>
				</Box>
			)}
			{error && <Alert severity="error">{error}</Alert>}
		</Stack>
	);
}

/** In the detail panel of an item: the notices about notes that pointed at it (dropped, promoted) to acknowledge. */
export function ItemNotices() {
	const { t } = useTranslation("notes");
	const item = useItemDetail();
	const { data: notices = [] } = useListItemNoticesQuery(item.uid);
	const [decide] = useDecideNoticeMutation();
	if (notices.length === 0) return null;
	return (
		<Stack spacing={1} data-testid={notesTestIds.itemNotices}>
			<Typography variant="overline" color="text.secondary">
				{t("field.notices")}
			</Typography>
			{notices.map((notice) => (
				<Box key={notice.uid} data-testid={notesTestIds.itemNotice(notice.uid)} sx={{ display: "flex", alignItems: "center", gap: 1 }}>
					<Typography variant="body2" sx={{ flexGrow: 1 }}>
						{noticeText(notice, t)}
					</Typography>
					{notice.decisions.map((decision) => (
						<Button key={decision} size="small" variant="outlined" onClick={() => void decide({ uid: notice.uid, decision })} data-testid={notesTestIds.noticeDecision(notice.uid, decision)}>
							{t(`notices.decision.${decision}`)}
						</Button>
					))}
				</Box>
			))}
		</Stack>
	);
}
