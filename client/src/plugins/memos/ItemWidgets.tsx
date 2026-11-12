import { Alert, Box, Button, Stack, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useItemDetail } from "../backlog";
import { toWriteError, useDecideHintMutation, useDemoteItemMutation, useListItemHintsQuery } from "./api";
import { hintText } from "./hintText";
import { memosTestIds } from "./testIds";

/** In the detail panel of an item: the action "back to a memo" (only while the item is open and not deleted). */
export function DemoteAction() {
	const { t } = useTranslation("memos");
	const item = useItemDetail();
	const [demote, { isLoading }] = useDemoteItemMutation();
	const [error, setError] = useState<string>();
	const [done, setDone] = useState<string>();
	if (item.deleted || (item.status !== "Open" && !done)) return null;
	return (
		<Stack spacing={0.5} data-testid={memosTestIds.demote}>
			{done ? (
				<Typography variant="body2" data-testid={memosTestIds.demoteDone}>
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
								.then((result) => setDone(result.memo.label))
								.catch((failure: unknown) => setError(toWriteError(failure).message));
						}}
						data-testid={memosTestIds.demoteButton}
					>
						{t("demote.button")}
					</Button>
				</Box>
			)}
			{error && <Alert severity="error">{error}</Alert>}
		</Stack>
	);
}

/** In the detail panel of an item: the hints about memos that pointed at it (dropped, promoted) to acknowledge. */
export function ItemHints() {
	const { t } = useTranslation("memos");
	const item = useItemDetail();
	const { data: hints = [] } = useListItemHintsQuery(item.uid);
	const [decide] = useDecideHintMutation();
	if (hints.length === 0) return null;
	return (
		<Stack spacing={1} data-testid={memosTestIds.itemHints}>
			<Typography variant="overline" color="text.secondary">
				{t("field.hints")}
			</Typography>
			{hints.map((hint) => (
				<Box key={hint.uid} data-testid={memosTestIds.itemHint(hint.uid)} sx={{ display: "flex", alignItems: "center", gap: 1 }}>
					<Typography variant="body2" sx={{ flexGrow: 1 }}>
						{hintText(hint, t)}
					</Typography>
					{hint.decisions.map((decision) => (
						<Button key={decision} size="small" variant="outlined" onClick={() => void decide({ uid: hint.uid, decision })} data-testid={memosTestIds.hintDecision(hint.uid, decision)}>
							{t(`hints.decision.${decision}`)}
						</Button>
					))}
				</Box>
			))}
		</Stack>
	);
}
