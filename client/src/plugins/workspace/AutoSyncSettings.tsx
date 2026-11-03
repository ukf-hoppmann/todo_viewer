import { Alert, Box, Button, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { errorMessage, useGetSyncSettingsQuery, useUpdateSyncSettingsMutation, type SyncSettings } from "./api";
import { workspaceTestIds } from "./testIds";

/** The section "Auto sync" of the settings page (group system): the interval of the automatic sync, changeable at runtime. */
export function AutoSyncSettings() {
	const { data } = useGetSyncSettingsQuery();
	if (!data) return null;
	return <Loaded settings={data} />;
}

function Loaded({ settings }: { settings: SyncSettings }) {
	const { t } = useTranslation("workspace");
	const [update] = useUpdateSyncSettingsMutation();
	// What the user typed; nothing while the field shows the stored value.
	const [draft, setDraft] = useState<string>();
	const text = draft ?? String(settings.auto_sync_interval_seconds);
	const seconds = Number(text);
	const valid = text.trim() !== "" && Number.isFinite(seconds);
	const locked = settings.locked_by_environment;
	const [error, setError] = useState<string>();
	const [saved, setSaved] = useState(false);

	const save = async () => {
		setError(undefined);
		setSaved(false);
		try {
			await update({ auto_sync_interval_seconds: seconds }).unwrap();
			setDraft(undefined);
			setSaved(true);
		} catch (failure) {
			setError(errorMessage(failure, t("autoSync.failed")));
		}
	};

	return (
		<Box data-testid={workspaceTestIds.autoSync} sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
			<Typography variant="h6" component="h3">
				{t("autoSync.title")}
			</Typography>
			<TextField
				type="number"
				size="small"
				label={t("autoSync.interval")}
				helperText={t("autoSync.hint")}
				value={text}
				disabled={locked}
				onChange={(event) => {
					setDraft(event.target.value);
					setSaved(false);
				}}
				slotProps={{ htmlInput: { min: 0, max: 86400, "data-testid": workspaceTestIds.autoSyncField } }}
			/>
			{locked && (
				<Alert severity="info" data-testid={workspaceTestIds.autoSyncLocked}>
					{t("autoSync.locked")}
				</Alert>
			)}
			{error && (
				<Alert severity="error" data-testid={workspaceTestIds.autoSyncError}>
					{error}
				</Alert>
			)}
			{saved && (
				<Alert severity="success" data-testid={workspaceTestIds.autoSyncSaved}>
					{t("autoSync.saved")}
				</Alert>
			)}
			<Box>
				<Button variant="contained" disabled={locked || !valid} onClick={() => void save()} data-testid={workspaceTestIds.autoSyncSave}>
					{t("card.save")}
				</Button>
			</Box>
		</Box>
	);
}
