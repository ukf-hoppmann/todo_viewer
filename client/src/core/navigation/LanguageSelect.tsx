import { MenuItem, Select } from "@mui/material";
import type { HTMLAttributes } from "react";
import { useTranslation } from "react-i18next";
import { supportedLanguages, type SupportedLanguage } from "../i18n/initI18n";
import { languageNames } from "../i18n/languageNames";
import { coreTestIds } from "../testIds";

function isSupported(language: string | undefined): language is SupportedLanguage {
	return supportedLanguages.some((supported) => supported === language);
}

/**
 * The language of the interface as a select in the app bar. It shows the language that is in effect (a
 * regional variant such as `de-DE` counts as `de`). The choice is remembered by `LanguageSync` in the UI state
 * of the server.
 */
export function LanguageSelect() {
	const { t, i18n } = useTranslation("core");
	const value = isSupported(i18n.resolvedLanguage) ? i18n.resolvedLanguage : "";

	const choose = (language: SupportedLanguage) => {
		void i18n.changeLanguage(language);
	};

	// Typed as a whole, because `data-*` attributes are not part of the type.
	const displayProps = { "aria-label": t("appBar.language"), "data-testid": coreTestIds.languageSelect } as HTMLAttributes<HTMLDivElement>;

	return (
		<Select
			variant="standard"
			disableUnderline
			value={value}
			onChange={(event) => choose(event.target.value as SupportedLanguage)}
			SelectDisplayProps={displayProps}
			sx={{ color: "inherit", "& .MuiSelect-icon": { color: "inherit" } }}
		>
			{supportedLanguages.map((language) => (
				<MenuItem key={language} value={language} lang={language} data-testid={coreTestIds.languageOption(language)}>
					{languageNames[language]}
				</MenuItem>
			))}
		</Select>
	);
}
