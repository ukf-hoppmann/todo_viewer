import { useContext, useEffect } from "react";
import { I18nContext } from "react-i18next";
import { supportedLanguages, type SupportedLanguage } from "../i18n/initI18n";
import { usePersistentState } from "./usePersistentState";

function isSupported(language: unknown): language is SupportedLanguage {
	return supportedLanguages.some((supported) => supported === language);
}

/**
 * Keeps the language of the interface in the UI state of the server (`core` / `language`): the stored
 * language is applied once it is loaded, and a change made by the user is stored. Renders nothing; needs the
 * store and an `I18nextProvider` above it. It uses the i18next instance of the provider itself (not the copy
 * `useTranslation` hands out), whose language is always current.
 */
export function LanguageSync() {
	const i18n = useContext(I18nContext)?.i18n;
	const [stored, setStored, loaded] = usePersistentState<string | undefined>("core", "language", undefined);

	useEffect(() => {
		if (i18n && loaded && isSupported(stored) && stored !== i18n.resolvedLanguage) void i18n.changeLanguage(stored);
	}, [i18n, loaded, stored]);

	useEffect(() => {
		if (!i18n || !loaded) return;
		const onChange = () => {
			const language = i18n.resolvedLanguage;
			if (isSupported(language) && language !== stored) setStored(language);
		};
		i18n.on("languageChanged", onChange);
		return () => i18n.off("languageChanged", onChange);
	}, [i18n, loaded, stored, setStored]);

	return null;
}
