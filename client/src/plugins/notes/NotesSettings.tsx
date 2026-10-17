import { Alert, Box, Button, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toWriteError, useGetSettingsQuery, useUpdateSettingsMutation, type SettingsOut } from "./api";
import { notesTestIds } from "./testIds";

/** The section "Notes" of the settings page: the review interval and the deepest topic level. */
export function NotesSettings() {
	const { data } = useGetSettingsQuery();
	if (!data) return null;
	return <Loaded settings={data} />;
}

function Loaded({ settings }: { settings: SettingsOut }) {
	const { t } = useTranslation("notes");
	const [update] = useUpdateSettingsMutation();
	// What the user typed; nothing while a field shows the stored value.
	const [draft, setDraft] = useState<{ days?: string; depth?: string }>({});
	const days = draft.days ?? String(settings.review_days);
	const depth = draft.depth ?? String(settings.max_topic_depth);
	const [error, setError] = useState<string>();
	const [saved, setSaved] = useState(false);

	const save = async () => {
		setError(undefined);
		setSaved(false);
		try {
			await update({ review_days: Number(days), max_topic_depth: Number(depth) }).unwrap();
			setDraft({});
			setSaved(true);
		} catch (failure) {
			setError(toWriteError(failure).message);
		}
	};
	return (
		<Box data-testid={notesTestIds.settings} sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
			<Typography variant="h6" component="h3">
				{t("settings.title")}
			</Typography>
			<TextField
				type="number"
				size="small"
				label={t("settings.reviewDays")}
				helperText={t("settings.reviewDaysHint")}
				value={days}
				onChange={(event) => setDraft({ ...draft, days: event.target.value })}
				slotProps={{ htmlInput: { min: 1, "data-testid": notesTestIds.settingsField("review_days") } }}
			/>
			<TextField
				type="number"
				size="small"
				label={t("settings.maxDepth")}
				helperText={t("settings.maxDepthHint")}
				value={depth}
				onChange={(event) => setDraft({ ...draft, depth: event.target.value })}
				slotProps={{ htmlInput: { min: 1, max: 10, "data-testid": notesTestIds.settingsField("max_topic_depth") } }}
			/>
			{error && <Alert severity="error">{error}</Alert>}
			{saved && <Alert severity="success">{t("settings.saved")}</Alert>}
			<Box>
				<Button variant="contained" onClick={() => void save()} data-testid={notesTestIds.settingsSave}>
					{t("form.save")}
				</Button>
			</Box>
		</Box>
	);
}
