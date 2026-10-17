import ClearIcon from "@mui/icons-material/Clear";
import { IconButton, InputAdornment, TextField } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useSearchText } from "./state";
import { workspaceTestIds } from "./testIds";

/** The search field at the top of the sidebar; the text is public (`useSearchText`). */
export function SearchSection() {
	const { t } = useTranslation("workspace");
	const [text, setText] = useSearchText();
	// The field answers at once; the stored text follows the keys.
	const [draft, setDraft] = useState<string>();
	const shown = draft ?? text;
	const change = (value: string) => {
		setDraft(value);
		setText(value);
	};
	return (
		<TextField
			size="small"
			fullWidth
			placeholder={t("search.placeholder")}
			value={shown}
			onChange={(event) => change(event.target.value)}
			slotProps={{
				htmlInput: { "aria-label": t("search.label"), "data-testid": workspaceTestIds.searchInput },
				input: {
					endAdornment: shown ? (
						<InputAdornment position="end">
							<IconButton size="small" aria-label={t("search.clear")} onClick={() => change("")} data-testid={workspaceTestIds.searchClear}>
								<ClearIcon fontSize="small" />
							</IconButton>
						</InputAdornment>
					) : undefined,
				},
			}}
		/>
	);
}
