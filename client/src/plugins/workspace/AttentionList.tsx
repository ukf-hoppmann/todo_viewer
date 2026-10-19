import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Box, Button, IconButton, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { IconAction } from "../../shared";
import { formatDueSince, type AttentionEntry } from "./attention";
import { workspaceTestIds } from "./testIds";

/**
 * The due entries as a list, the newest first and unfolded; a click on the title opens the element (`onOpened`
 * closes the list), the arrow unfolds an entry with its caption and actions.
 */
export function AttentionList({ entries, onOpened }: { entries: AttentionEntry[]; onOpened: () => void }) {
	const { t, i18n } = useTranslation("workspace");
	const [unfolded, setUnfolded] = useState<ReadonlySet<string>>(() => new Set(entries[0] ? [entries[0].key] : []));
	const toggle = (key: string) =>
		setUnfolded((current) => {
			const next = new Set(current);
			if (!next.delete(key)) next.add(key);
			return next;
		});

	return (
		<Box sx={{ p: 1, minWidth: 320, maxWidth: 520 }} data-testid={workspaceTestIds.attentionList}>
			<Typography variant="overline">{t("attention.title")}</Typography>
			{entries.map((entry) => {
				const open = unfolded.has(entry.key);
				const Icon = entry.icon;
				return (
					<Box key={entry.key} sx={{ py: 0.5 }} data-testid={workspaceTestIds.attentionItem(entry.key)}>
						<Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
							<Icon fontSize="small" />
							<Box
								component="button"
								type="button"
								onClick={() => {
									entry.open();
									onOpened();
								}}
								data-testid={workspaceTestIds.attentionOpen(entry.key)}
								sx={{ flexGrow: 1, textAlign: "left", bgcolor: "transparent", border: 0, color: "inherit", cursor: "pointer", font: "inherit", p: 0 }}
							>
								{entry.title}
							</Box>
							<Typography variant="caption" color="text.secondary" sx={{ whiteSpace: "nowrap" }}>
								{formatDueSince(entry.dueSince, i18n.language)}
							</Typography>
							<IconButton
								size="small"
								aria-label={open ? t("attention.fold") : t("attention.unfold")}
								aria-expanded={open}
								onClick={() => toggle(entry.key)}
								data-testid={workspaceTestIds.attentionToggle(entry.key)}
							>
								{open ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
							</IconButton>
						</Box>
						{open && (
							<Box sx={{ pl: 3.5 }}>
								{entry.caption && (
									<Typography variant="caption" color="text.secondary" component="div">
										{entry.caption}
									</Typography>
								)}
								<Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
									{entry.actions.map((action) =>
										action.icon ? (
											<IconAction key={action.id} label={action.label} icon={action.icon} onClick={action.run} testId={action.testId} />
										) : (
											<Button key={action.id} size="small" onClick={action.run} data-testid={action.testId}>
												{action.label}
											</Button>
										),
									)}
								</Box>
							</Box>
						)}
					</Box>
				);
			})}
		</Box>
	);
}
