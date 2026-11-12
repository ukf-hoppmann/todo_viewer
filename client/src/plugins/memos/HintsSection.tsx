import { Alert, Box, Button, Stack, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toWriteError, useDecideHintMutation, type MemoOut } from "./api";
import { hintText } from "./hintText";
import { PromoteDialog } from "./PromoteDialog";
import { memosTestIds } from "./testIds";

/**
 * The section "Hints" of the memo detail: what happened to a linked item since, with one button per possible
 * decision. "Promote" asks for the fields of the new item first.
 */
export function HintsSection({ memo }: { memo: MemoOut }) {
	const { t } = useTranslation("memos");
	const [decide] = useDecideHintMutation();
	const [promoting, setPromoting] = useState<string>();
	const [error, setError] = useState<string>();

	if (memo.hints.length === 0) {
		return (
			<Typography variant="body2" color="text.secondary" data-testid={memosTestIds.hints}>
				{t("hints.none")}
			</Typography>
		);
	}
	return (
		<Stack spacing={1.5} data-testid={memosTestIds.hints}>
			{memo.hints.map((hint) => (
				<Box key={hint.uid} data-testid={memosTestIds.hint(hint.uid)}>
					<Typography variant="body2">{hintText(hint, t)}</Typography>
					<Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mt: 0.5 }}>
						{hint.decisions.map((decision) => (
							<Button
								key={decision}
								size="small"
								variant="outlined"
								data-testid={memosTestIds.hintDecision(hint.uid, decision)}
								onClick={() => {
									setError(undefined);
									if (decision === "promote") setPromoting(hint.uid);
									else
										decide({ uid: hint.uid, decision, version: memo.version })
											.unwrap()
											.catch((failure: unknown) => setError(toWriteError(failure).message));
								}}
							>
								{t(`hints.decision.${decision}`)}
							</Button>
						))}
					</Box>
				</Box>
			))}
			{error && <Alert severity="error">{error}</Alert>}
			{promoting && <PromoteDialog memo={memo} hintUid={promoting} onClose={() => setPromoting(undefined)} />}
		</Stack>
	);
}
